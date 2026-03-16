from __future__ import annotations

from copy import deepcopy
from random import Random
from typing import Any

from pfbench.powerflow.cases import load_case
from pfbench.utils import canonical_json, stable_hex


def bus_partition(case: dict[str, Any]) -> dict[str, list[int]]:
    slack, pv, pq = [], [], []
    for row in case["bus"]:
        bus_id = int(row[0])
        bus_type = int(row[1])
        if bus_type == 3:
            slack.append(bus_id)
        elif bus_type == 2:
            pv.append(bus_id)
        else:
            pq.append(bus_id)
    return {"slack_bus_ids": slack, "pv_bus_ids": pv, "pq_bus_ids": pq}


def active_branches(case: dict[str, Any]) -> list[dict[str, int]]:
    rows = []
    for branch_id, row in enumerate(case["branch"], start=1):
        if int(row[10]) == 1:
            rows.append({"branch_id": branch_id, "from_bus": int(row[0]), "to_bus": int(row[1])})
    return rows


def _connected_after_outage(case: dict[str, Any], branch_id_to_disable: int) -> bool:
    buses = [int(row[0]) for row in case["bus"]]
    neighbors = {bus_id: set() for bus_id in buses}
    for branch_id, row in enumerate(case["branch"], start=1):
        if branch_id == branch_id_to_disable:
            continue
        if int(row[10]) == 0:
            continue
        a, b = int(row[0]), int(row[1])
        neighbors[a].add(b)
        neighbors[b].add(a)
    if not buses:
        return True
    seen = set()
    stack = [buses[0]]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(sorted(neighbors[node] - seen))
    return len(seen) == len(buses)


def generate_scenario_spec(case_name: str, seed: int, attempt: int = 0) -> dict[str, Any]:
    case = load_case(case_name)
    rng = Random(seed + attempt * 9973)
    buses_with_load = [int(row[0]) for row in case["bus"] if abs(float(row[2])) > 0 or abs(float(row[3])) > 0]
    branch_candidates = [branch["branch_id"] for branch in active_branches(case)]
    tap_candidates = [
        idx for idx, row in enumerate(case["branch"], start=1)
        if int(row[10]) == 1 and float(row[8]) not in (0.0, 1.0)
    ]

    mutations: list[dict[str, Any]] = []

    num_load_mutations = min(len(buses_with_load), 2 + rng.randrange(2))
    for bus_id in sorted(rng.sample(buses_with_load, k=num_load_mutations)):
        p_mult = round(rng.uniform(0.9, 1.15), 4)
        q_mult = round(rng.uniform(0.9, 1.15), 4)
        mutations.append({
            "op": "scale_bus_load",
            "bus_id": bus_id,
            "p_mult": p_mult,
            "q_mult": q_mult,
        })

    if branch_candidates and rng.random() < 0.45:
        shuffled = branch_candidates[:]
        rng.shuffle(shuffled)
        for branch_id in shuffled:
            if _connected_after_outage(case, branch_id):
                row = case["branch"][branch_id - 1]
                mutations.append({
                    "op": "line_outage",
                    "branch_id": branch_id,
                    "from_bus": int(row[0]),
                    "to_bus": int(row[1]),
                })
                break

    if tap_candidates and rng.random() < 0.5:
        branch_id = rng.choice(tap_candidates)
        row = case["branch"][branch_id - 1]
        base_ratio = float(row[8])
        new_ratio = round(base_ratio * rng.uniform(0.96, 1.04), 4)
        mutations.append({
            "op": "set_tap_ratio",
            "branch_id": branch_id,
            "from_bus": int(row[0]),
            "to_bus": int(row[1]),
            "old_ratio": base_ratio,
            "new_ratio": new_ratio,
        })

    spec_core = {
        "seed": int(seed),
        "source_case": case_name,
        "solver_modes": ["ac", "dc"],
        "mutations": mutations,
    }
    scenario_id = f"scn_{case_name}_{stable_hex(spec_core, length=12)}"
    spec_core["scenario_id"] = scenario_id
    return spec_core


def apply_scenario(case: dict[str, Any], scenario_spec: dict[str, Any]) -> dict[str, Any]:
    mutated = deepcopy(case)

    bus_id_to_idx = {int(row[0]): idx for idx, row in enumerate(mutated["bus"])}
    for mutation in scenario_spec.get("mutations", []):
        op = mutation["op"]
        if op == "scale_bus_load":
            row = mutated["bus"][bus_id_to_idx[int(mutation["bus_id"])]]
            row[2] = round(float(row[2]) * float(mutation["p_mult"]), 6)
            row[3] = round(float(row[3]) * float(mutation["q_mult"]), 6)
        elif op == "line_outage":
            branch_idx = int(mutation["branch_id"]) - 1
            mutated["branch"][branch_idx][10] = 0
        elif op == "set_tap_ratio":
            branch_idx = int(mutation["branch_id"]) - 1
            mutated["branch"][branch_idx][8] = float(mutation["new_ratio"])
        else:
            raise ValueError(f"Unsupported mutation op: {op}")
    return mutated


def scenario_summary_text(case_name: str, scenario_spec: dict[str, Any]) -> str:
    if not scenario_spec.get("mutations"):
        return f"Base case {case_name} with no scenario mutations."
    pieces = []
    for mutation in scenario_spec["mutations"]:
        if mutation["op"] == "scale_bus_load":
            pieces.append(
                f"scale load at bus {mutation['bus_id']} by P×{mutation['p_mult']} and Q×{mutation['q_mult']}"
            )
        elif mutation["op"] == "line_outage":
            pieces.append(
                f"switch off branch {mutation['branch_id']} ({mutation['from_bus']}-{mutation['to_bus']})"
            )
        elif mutation["op"] == "set_tap_ratio":
            pieces.append(
                f"change transformer tap on branch {mutation['branch_id']} ({mutation['from_bus']}-{mutation['to_bus']}) "
                f"from {mutation['old_ratio']} to {mutation['new_ratio']}"
            )
    return f"Base case {case_name}; mutations: " + "; ".join(pieces) + "."
