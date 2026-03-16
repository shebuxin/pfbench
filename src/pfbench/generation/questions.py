from __future__ import annotations

from random import Random
from typing import Any

from pfbench.utils import stable_seed


QUERY_FAMILIES = [
    "direct_bus_vm",
    "direct_bus_va",
    "argmin_bus_vm",
    "argmax_bus_va_abs",
    "direct_branch_p_from",
    "direct_branch_q_from",
    "max_branch_abs_p_from",
    "max_branch_abs_q_from",
    "compare_ac_dc_branch_p_from",
    "is_voltage_violation_present",
]


def _response_schema(properties: dict[str, dict[str, Any]], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


def _scenario_digest(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "num_buses": int(record["grid_reference"]["counts"]["num_buses"]),
        "num_generators": int(record["grid_reference"]["counts"]["num_generators"]),
        "num_branches": int(record["grid_reference"]["counts"]["num_branches"]),
        "num_active_branches": int(record["scenario_input_state"]["totals"]["num_active_branches"]),
        "mutation_ops": list(record["metadata"]["mutation_ops"]),
        "bus_partition": dict(record["scenario_input_state"]["bus_partition"]),
        "total_pd_mw": float(record["scenario_input_state"]["totals"]["total_pd_mw"]),
        "total_qd_mvar": float(record["scenario_input_state"]["totals"]["total_qd_mvar"]),
        "total_scheduled_pg_mw": float(record["scenario_input_state"]["totals"]["total_scheduled_pg_mw"]),
    }


def _pick_bus(record: dict[str, Any], family: str) -> dict[str, Any]:
    buses = record["powerflow_results"]["ac"]["bus_results"]
    rng = Random(stable_seed(record["scenario_id"], family, "bus"))
    return sorted(buses, key=lambda row: row["bus_id"])[rng.randrange(len(buses))]


def _active_branches(record: dict[str, Any], mode: str = "ac") -> list[dict[str, Any]]:
    return [
        row for row in record["powerflow_results"][mode]["branch_results"]
        if int(row["status"]) == 1
    ]


def _pick_branch(record: dict[str, Any], family: str) -> dict[str, Any]:
    branches = _active_branches(record, mode="ac")
    rng = Random(stable_seed(record["scenario_id"], family, "branch"))
    return sorted(branches, key=lambda row: row["branch_id"])[rng.randrange(len(branches))]


def _source_voltage_limit_exclusions(record: dict[str, Any]) -> set[int]:
    flags = record.get("data_quality_flags", {})
    return {int(bus_id) for bus_id in flags.get("source_voltage_limit_inconsistency_bus_ids", [])}


def _voltage_violations(record: dict[str, Any]) -> list[int]:
    bus_limits = {
        int(row["bus_id"]): (float(row["vmin_pu"]), float(row["vmax_pu"]))
        for row in record["scenario_input_state"]["buses"]
    }
    excluded_bus_ids = _source_voltage_limit_exclusions(record)
    violating: list[int] = []
    for row in record["powerflow_results"]["ac"]["bus_results"]:
        bus_id = int(row["bus_id"])
        if bus_id in excluded_bus_ids:
            continue
        vmin, vmax = bus_limits[bus_id]
        vm = float(row["vm_pu"])
        if vm < vmin or vm > vmax:
            violating.append(bus_id)
    return sorted(violating)


def build_question_item(
    dataset_id: str,
    scenario_record: dict[str, Any],
    query_family: str,
    scenario_artifact_name: str = "scenarios.jsonl",
) -> dict[str, Any]:
    scenario_id = scenario_record["scenario_id"]
    source_case = scenario_record["source_case"]
    split = scenario_record["split"]
    scenario_text = scenario_record["metadata"]["scenario_text"]
    digest = _scenario_digest(scenario_record)

    if query_family == "direct_bus_vm":
        target = _pick_bus(scenario_record, query_family)
        prompt = (
            f"Scenario ID: {scenario_id}. {scenario_text} "
            f"Using the scenario record for this modified network, run AC power flow and report "
            f"the voltage magnitude at bus {target['bus_id']}. Return JSON."
        )
        response_schema = _response_schema(
            {"bus_id": {"type": "integer"}, "vm_pu": {"type": "number"}},
            ["bus_id", "vm_pu"],
        )
        gold_answer = {"bus_id": int(target["bus_id"]), "vm_pu": float(target["vm_pu"])}
        grader = {"type": "json_numeric_tolerance", "float_tol": 1e-4, "required_fields": ["bus_id", "vm_pu"]}
        metadata = {"solver_mode": "ac", "target_bus_id": int(target["bus_id"]), "tool_required": True}

    elif query_family == "direct_bus_va":
        target = _pick_bus(scenario_record, query_family)
        prompt = (
            f"Scenario ID: {scenario_id}. {scenario_text} "
            f"Using the scenario record for this modified network, run AC power flow and report "
            f"the voltage angle in degrees at bus {target['bus_id']}. Return JSON."
        )
        response_schema = _response_schema(
            {"bus_id": {"type": "integer"}, "va_deg": {"type": "number"}},
            ["bus_id", "va_deg"],
        )
        gold_answer = {"bus_id": int(target["bus_id"]), "va_deg": float(target["va_deg"])}
        grader = {"type": "json_numeric_tolerance", "float_tol": 1e-4, "required_fields": ["bus_id", "va_deg"]}
        metadata = {"solver_mode": "ac", "target_bus_id": int(target["bus_id"]), "tool_required": True}

    elif query_family == "argmin_bus_vm":
        target = min(scenario_record["powerflow_results"]["ac"]["bus_results"], key=lambda row: row["vm_pu"])
        prompt = (
            f"Scenario ID: {scenario_id}. {scenario_text} "
            "Using the scenario record, identify the bus with the minimum AC voltage magnitude. Return JSON."
        )
        response_schema = _response_schema(
            {"bus_id": {"type": "integer"}, "vm_pu": {"type": "number"}},
            ["bus_id", "vm_pu"],
        )
        gold_answer = {"bus_id": int(target["bus_id"]), "vm_pu": float(target["vm_pu"])}
        grader = {"type": "json_numeric_tolerance", "float_tol": 1e-4, "required_fields": ["bus_id", "vm_pu"]}
        metadata = {"solver_mode": "ac", "criterion": "argmin_vm_pu", "tool_required": True}

    elif query_family == "argmax_bus_va_abs":
        target = max(
            scenario_record["powerflow_results"]["ac"]["bus_results"],
            key=lambda row: abs(float(row["va_deg"])),
        )
        prompt = (
            f"Scenario ID: {scenario_id}. {scenario_text} "
            "Using the scenario record, identify the bus with the largest absolute AC voltage angle. Return JSON."
        )
        response_schema = _response_schema(
            {"bus_id": {"type": "integer"}, "va_deg": {"type": "number"}},
            ["bus_id", "va_deg"],
        )
        gold_answer = {"bus_id": int(target["bus_id"]), "va_deg": float(target["va_deg"])}
        grader = {"type": "json_numeric_tolerance", "float_tol": 1e-4, "required_fields": ["bus_id", "va_deg"]}
        metadata = {"solver_mode": "ac", "criterion": "argmax_abs_va_deg", "tool_required": True}

    elif query_family == "direct_branch_p_from":
        target = _pick_branch(scenario_record, query_family)
        prompt = (
            f"Scenario ID: {scenario_id}. {scenario_text} "
            f"Using the scenario record, report the AC from-side active power flow on branch "
            f"{target['branch_id']} ({target['from_bus']}-{target['to_bus']}). Return JSON."
        )
        response_schema = _response_schema(
            {
                "branch_id": {"type": "integer"},
                "from_bus": {"type": "integer"},
                "to_bus": {"type": "integer"},
                "p_from_mw": {"type": "number"},
            },
            ["branch_id", "from_bus", "to_bus", "p_from_mw"],
        )
        gold_answer = {
            "branch_id": int(target["branch_id"]),
            "from_bus": int(target["from_bus"]),
            "to_bus": int(target["to_bus"]),
            "p_from_mw": float(target["p_from_mw"]),
        }
        grader = {
            "type": "json_numeric_tolerance",
            "float_tol": 1e-4,
            "required_fields": ["branch_id", "from_bus", "to_bus", "p_from_mw"],
        }
        metadata = {"solver_mode": "ac", "target_branch_id": int(target["branch_id"]), "tool_required": True}

    elif query_family == "direct_branch_q_from":
        target = _pick_branch(scenario_record, query_family)
        prompt = (
            f"Scenario ID: {scenario_id}. {scenario_text} "
            f"Using the scenario record, report the AC from-side reactive power flow on branch "
            f"{target['branch_id']} ({target['from_bus']}-{target['to_bus']}). Return JSON."
        )
        response_schema = _response_schema(
            {
                "branch_id": {"type": "integer"},
                "from_bus": {"type": "integer"},
                "to_bus": {"type": "integer"},
                "q_from_mvar": {"type": "number"},
            },
            ["branch_id", "from_bus", "to_bus", "q_from_mvar"],
        )
        gold_answer = {
            "branch_id": int(target["branch_id"]),
            "from_bus": int(target["from_bus"]),
            "to_bus": int(target["to_bus"]),
            "q_from_mvar": float(target["q_from_mvar"]),
        }
        grader = {
            "type": "json_numeric_tolerance",
            "float_tol": 1e-4,
            "required_fields": ["branch_id", "from_bus", "to_bus", "q_from_mvar"],
        }
        metadata = {"solver_mode": "ac", "target_branch_id": int(target["branch_id"]), "tool_required": True}

    elif query_family == "max_branch_abs_p_from":
        target = max(
            _active_branches(scenario_record, mode="ac"),
            key=lambda row: abs(float(row["p_from_mw"])),
        )
        prompt = (
            f"Scenario ID: {scenario_id}. {scenario_text} "
            "Using the scenario record, find the active branch with the largest absolute AC active power flow "
            "measured at the from side. Return JSON."
        )
        response_schema = _response_schema(
            {
                "branch_id": {"type": "integer"},
                "from_bus": {"type": "integer"},
                "to_bus": {"type": "integer"},
                "p_from_mw": {"type": "number"},
            },
            ["branch_id", "from_bus", "to_bus", "p_from_mw"],
        )
        gold_answer = {
            "branch_id": int(target["branch_id"]),
            "from_bus": int(target["from_bus"]),
            "to_bus": int(target["to_bus"]),
            "p_from_mw": float(target["p_from_mw"]),
        }
        grader = {
            "type": "json_numeric_tolerance",
            "float_tol": 1e-4,
            "required_fields": ["branch_id", "from_bus", "to_bus", "p_from_mw"],
        }
        metadata = {"solver_mode": "ac", "criterion": "max_abs_p_from", "tool_required": True}

    elif query_family == "max_branch_abs_q_from":
        target = max(
            _active_branches(scenario_record, mode="ac"),
            key=lambda row: abs(float(row["q_from_mvar"])),
        )
        prompt = (
            f"Scenario ID: {scenario_id}. {scenario_text} "
            "Using the scenario record, find the active branch with the largest absolute AC reactive power flow "
            "measured at the from side. Return JSON."
        )
        response_schema = _response_schema(
            {
                "branch_id": {"type": "integer"},
                "from_bus": {"type": "integer"},
                "to_bus": {"type": "integer"},
                "q_from_mvar": {"type": "number"},
            },
            ["branch_id", "from_bus", "to_bus", "q_from_mvar"],
        )
        gold_answer = {
            "branch_id": int(target["branch_id"]),
            "from_bus": int(target["from_bus"]),
            "to_bus": int(target["to_bus"]),
            "q_from_mvar": float(target["q_from_mvar"]),
        }
        grader = {
            "type": "json_numeric_tolerance",
            "float_tol": 1e-4,
            "required_fields": ["branch_id", "from_bus", "to_bus", "q_from_mvar"],
        }
        metadata = {"solver_mode": "ac", "criterion": "max_abs_q_from", "tool_required": True}

    elif query_family == "compare_ac_dc_branch_p_from":
        ac_target = _pick_branch(scenario_record, query_family)
        dc_map = {
            int(row["branch_id"]): row
            for row in _active_branches(scenario_record, mode="dc")
        }
        dc_target = dc_map[int(ac_target["branch_id"])]
        diff = abs(float(ac_target["p_from_mw"]) - float(dc_target["p_from_mw"]))
        prompt = (
            f"Scenario ID: {scenario_id}. {scenario_text} "
            f"Using the scenario record, compare AC and DC from-side active power flow on branch "
            f"{ac_target['branch_id']} ({ac_target['from_bus']}-{ac_target['to_bus']}). Return JSON."
        )
        response_schema = _response_schema(
            {
                "branch_id": {"type": "integer"},
                "from_bus": {"type": "integer"},
                "to_bus": {"type": "integer"},
                "ac_p_from_mw": {"type": "number"},
                "dc_p_from_mw": {"type": "number"},
                "abs_diff_mw": {"type": "number"},
            },
            ["branch_id", "from_bus", "to_bus", "ac_p_from_mw", "dc_p_from_mw", "abs_diff_mw"],
        )
        gold_answer = {
            "branch_id": int(ac_target["branch_id"]),
            "from_bus": int(ac_target["from_bus"]),
            "to_bus": int(ac_target["to_bus"]),
            "ac_p_from_mw": float(ac_target["p_from_mw"]),
            "dc_p_from_mw": float(dc_target["p_from_mw"]),
            "abs_diff_mw": float(round(diff, 6)),
        }
        grader = {
            "type": "json_numeric_tolerance",
            "float_tol": 1e-4,
            "required_fields": ["branch_id", "from_bus", "to_bus", "ac_p_from_mw", "dc_p_from_mw", "abs_diff_mw"],
        }
        metadata = {"solver_mode": "ac_dc", "target_branch_id": int(ac_target["branch_id"]), "tool_required": True}

    elif query_family == "is_voltage_violation_present":
        violating_bus_ids = _voltage_violations(scenario_record)
        excluded_bus_ids = sorted(_source_voltage_limit_exclusions(scenario_record))
        prompt = (
            f"Scenario ID: {scenario_id}. {scenario_text} "
            "Using the scenario record, determine whether any AC bus voltage magnitude violates its limits "
            "after excluding any buses already flagged as source-case voltage-limit inconsistencies. "
            "Return JSON."
        )
        response_schema = _response_schema(
            {
                "voltage_violation_present": {"type": "boolean"},
                "num_violations": {"type": "integer"},
                "violating_bus_ids": {"type": "array", "items": {"type": "integer"}},
            },
            ["voltage_violation_present", "num_violations", "violating_bus_ids"],
        )
        gold_answer = {
            "voltage_violation_present": bool(violating_bus_ids),
            "num_violations": len(violating_bus_ids),
            "violating_bus_ids": violating_bus_ids,
        }
        grader = {
            "type": "json_exact",
            "required_fields": ["voltage_violation_present", "num_violations", "violating_bus_ids"],
        }
        metadata = {
            "solver_mode": "ac",
            "criterion": "voltage_limit_check_excluding_source_inconsistencies",
            "excluded_source_inconsistency_bus_ids": excluded_bus_ids,
            "tool_required": True,
        }

    else:
        raise ValueError(f"Unsupported query family: {query_family}")

    return {
        "dataset_id": dataset_id,
        "scenario_id": scenario_id,
        "question_id": f"q_{scenario_id}_{query_family}",
        "source_case": source_case,
        "split": split,
        "query_family": query_family,
        "evaluation_mode": "tool_or_structured_context_required",
        "prompt": prompt,
        "response_schema": response_schema,
        "gold_answer": gold_answer,
        "grader": grader,
        "scenario_digest": digest,
        "provenance": {
            "gold_source": "solver_truth",
            "scenario_artifact": scenario_artifact_name,
            "pipeline": "pfbench_phase1",
            "dataset_version": scenario_record["provenance"]["dataset_version"],
        },
        "metadata": metadata,
    }
