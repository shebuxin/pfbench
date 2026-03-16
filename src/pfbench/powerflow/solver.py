from __future__ import annotations

import math
from typing import Any

import numpy as np

from pfbench.powerflow.cases import load_case
from pfbench.powerflow.scenario import apply_scenario, bus_partition, scenario_summary_text
from pfbench.utils import stable_hex


BUS_TYPE_LABEL = {
    1: "PQ",
    2: "PV",
    3: "Slack",
}


class PowerFlowError(RuntimeError):
    """Raised when a scenario cannot be solved."""


def _bus_index(case: dict[str, Any]) -> dict[int, int]:
    return {int(row[0]): idx for idx, row in enumerate(case["bus"])}


def _build_ybus(case: dict[str, Any]) -> tuple[np.ndarray, list[dict[str, Any]]]:
    bus = np.array(case["bus"], dtype=float)
    branch = np.array(case["branch"], dtype=float)
    idx = _bus_index(case)
    base_mva = float(case["baseMVA"])
    nb = bus.shape[0]
    ybus = np.zeros((nb, nb), dtype=complex)
    branch_models: list[dict[str, Any]] = []

    for branch_id, row in enumerate(branch, start=1):
        fbus, tbus, r, x, b, rate_a, rate_b, rate_c, ratio, angle, status, angmin, angmax = row[:13]
        if int(status) == 0:
            branch_models.append({
                "branch_id": branch_id,
                "from_bus": int(fbus),
                "to_bus": int(tbus),
                "status": 0,
            })
            continue
        i = idx[int(fbus)]
        j = idx[int(tbus)]
        z = complex(float(r), float(x))
        y = 1 / z if abs(z) > 0 else complex(0.0, -1.0 / float(x))
        bsh = 1j * float(b) / 2.0
        tap_mag = float(ratio) if float(ratio) != 0.0 else 1.0
        shift = math.radians(float(angle))
        tap = tap_mag * np.exp(1j * shift)

        yff = (y + bsh) / (tap * np.conj(tap))
        ytt = y + bsh
        yft = -y / np.conj(tap)
        ytf = -y / tap

        ybus[i, i] += yff
        ybus[j, j] += ytt
        ybus[i, j] += yft
        ybus[j, i] += ytf

        branch_models.append({
            "branch_id": branch_id,
            "from_bus": int(fbus),
            "to_bus": int(tbus),
            "status": 1,
            "from_idx": i,
            "to_idx": j,
            "yff": yff,
            "yft": yft,
            "ytf": ytf,
            "ytt": ytt,
            "tap": tap,
        })

    gs = bus[:, 4] / base_mva
    bs = bus[:, 5] / base_mva
    ybus += np.diag(gs + 1j * bs)
    return ybus, branch_models


def _scheduled_bus_power(case: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    bus = np.array(case["bus"], dtype=float)
    base_mva = float(case["baseMVA"])
    nb = bus.shape[0]
    pg = np.zeros(nb)
    qg = np.zeros(nb)
    idx = _bus_index(case)
    for gen in case["gen"]:
        if int(gen[7]) == 0:
            continue
        bus_pos = idx[int(gen[0])]
        pg[bus_pos] += float(gen[1])
        qg[bus_pos] += float(gen[2])
    pd = bus[:, 2]
    qd = bus[:, 3]
    return (pg - pd) / base_mva, (qg - qd) / base_mva


def _calc_power(ybus: np.ndarray, vm: np.ndarray, va: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    v = vm * np.exp(1j * va)
    s = v * np.conj(ybus @ v)
    return s.real, s.imag


def _ac_power_flow(case: dict[str, Any], tolerance: float, max_iterations: int) -> dict[str, Any]:
    bus = np.array(case["bus"], dtype=float)
    ybus, branch_models = _build_ybus(case)
    p_spec, q_spec = _scheduled_bus_power(case)
    types = bus[:, 1].astype(int)
    ref = np.where(types == 3)[0]
    pv = np.where(types == 2)[0]
    pq = np.where(types == 1)[0]
    if len(ref) != 1:
        raise PowerFlowError("Current phase-1 solver expects exactly one slack bus.")

    vm = bus[:, 7].copy()
    va = np.deg2rad(bus[:, 8].copy())
    pvpq = np.r_[pv, pq]
    converged = False
    p = np.zeros_like(vm)
    q = np.zeros_like(vm)

    for iteration in range(max_iterations):
        p, q = _calc_power(ybus, vm, va)
        d_p = p_spec - p
        d_q = q_spec - q
        mismatch = np.r_[d_p[pvpq], d_q[pq]]
        if mismatch.size == 0 or float(np.max(np.abs(mismatch))) < tolerance:
            converged = True
            break

        g = ybus.real
        b = ybus.imag
        n_pvpq = len(pvpq)
        n_pq = len(pq)
        h = np.zeros((n_pvpq, n_pvpq))
        n = np.zeros((n_pvpq, n_pq))
        m = np.zeros((n_pq, n_pvpq))
        l = np.zeros((n_pq, n_pq))

        for a, i in enumerate(pvpq):
            for bb, j in enumerate(pvpq):
                if i == j:
                    h[a, bb] = -q[i] - b[i, i] * vm[i] ** 2
                else:
                    theta = va[i] - va[j]
                    h[a, bb] = vm[i] * vm[j] * (g[i, j] * np.sin(theta) - b[i, j] * np.cos(theta))
            for bb, j in enumerate(pq):
                if i == j:
                    n[a, bb] = p[i] / vm[i] + g[i, i] * vm[i]
                else:
                    theta = va[i] - va[j]
                    n[a, bb] = vm[i] * (g[i, j] * np.cos(theta) + b[i, j] * np.sin(theta))

        for a, i in enumerate(pq):
            for bb, j in enumerate(pvpq):
                if i == j:
                    m[a, bb] = p[i] - g[i, i] * vm[i] ** 2
                else:
                    theta = va[i] - va[j]
                    m[a, bb] = -vm[i] * vm[j] * (g[i, j] * np.cos(theta) + b[i, j] * np.sin(theta))
            for bb, j in enumerate(pq):
                if i == j:
                    l[a, bb] = q[i] / vm[i] - b[i, i] * vm[i]
                else:
                    theta = va[i] - va[j]
                    l[a, bb] = vm[i] * (g[i, j] * np.sin(theta) - b[i, j] * np.cos(theta))

        jacobian = np.block([[h, n], [m, l]])
        try:
            delta = np.linalg.solve(jacobian, mismatch)
        except np.linalg.LinAlgError as exc:
            raise PowerFlowError(f"AC Jacobian is singular: {exc}") from exc

        va[pvpq] += delta[:n_pvpq]
        vm[pq] += delta[n_pvpq:]

    if not converged:
        raise PowerFlowError("AC power flow did not converge.")

    p, q = _calc_power(ybus, vm, va)
    return {
        "converged": True,
        "solver_name": "newton_raphson_polar",
        "iterations": int(iteration + 1),
        "tolerance": float(tolerance),
        "vm": vm,
        "va": va,
        "p_inj_pu": p,
        "q_inj_pu": q,
        "ybus": ybus,
        "branch_models": branch_models,
    }


def _dc_power_flow(case: dict[str, Any]) -> dict[str, Any]:
    bus = np.array(case["bus"], dtype=float)
    branch = np.array(case["branch"], dtype=float)
    types = bus[:, 1].astype(int)
    ref = np.where(types == 3)[0]
    if len(ref) != 1:
        raise PowerFlowError("Current phase-1 DC solver expects exactly one slack bus.")
    ref_idx = int(ref[0])

    nb = bus.shape[0]
    idx = _bus_index(case)
    p_spec, _ = _scheduled_bus_power(case)

    bbus = np.zeros((nb, nb))
    pbusinj = np.zeros(nb)
    for row in branch:
        fbus, tbus, r, x, b, rate_a, rate_b, rate_c, ratio, angle, status, angmin, angmax = row[:13]
        if int(status) == 0:
            continue
        i = idx[int(fbus)]
        j = idx[int(tbus)]
        tap = float(ratio) if float(ratio) != 0.0 else 1.0
        shift = math.radians(float(angle))
        bij = 1.0 / float(x)
        bbus[i, i] += bij / (tap ** 2)
        bbus[j, j] += bij
        bbus[i, j] += -bij / tap
        bbus[j, i] += -bij / tap
        if abs(shift) > 0:
            pbusinj[i] += -shift * bij / tap
            pbusinj[j] += shift * bij / tap

    mask = [i for i in range(nb) if i != ref_idx]
    reduced = bbus[np.ix_(mask, mask)]
    rhs = p_spec[mask] - pbusinj[mask]
    try:
        theta = np.zeros(nb)
        theta[np.array(mask, dtype=int)] = np.linalg.solve(reduced, rhs)
    except np.linalg.LinAlgError as exc:
        raise PowerFlowError(f"DC B-matrix is singular: {exc}") from exc

    p_inj = bbus @ theta + pbusinj
    return {
        "converged": True,
        "solver_name": "dc_power_flow",
        "iterations": 1,
        "tolerance": 0.0,
        "vm": np.ones(nb),
        "va": theta,
        "p_inj_pu": p_inj,
        "q_inj_pu": None,
    }


def _element_type(branch_row: list[float]) -> str:
    return "transformer" if float(branch_row[8]) not in (0.0, 1.0) else "line"


def _snapshot_buses(case: dict[str, Any]) -> list[dict[str, Any]]:
    buses = []
    bus_names = list(case.get("bus_name", []))
    for pos, row in enumerate(case["bus"]):
        buses.append({
            "bus_id": int(row[0]),
            "bus_name": bus_names[pos] if pos < len(bus_names) else None,
            "type_code": int(row[1]),
            "type_label": BUS_TYPE_LABEL.get(int(row[1]), "Unknown"),
            "pd_mw": float(row[2]),
            "qd_mvar": float(row[3]),
            "gs_mw": float(row[4]),
            "bs_mvar": float(row[5]),
            "area": int(row[6]),
            "vm_init_pu": float(row[7]),
            "va_init_deg": float(row[8]),
            "base_kv": float(row[9]),
            "zone": int(row[10]),
            "vmax_pu": float(row[11]),
            "vmin_pu": float(row[12]),
        })
    return buses


def _snapshot_generators(case: dict[str, Any]) -> list[dict[str, Any]]:
    partition = bus_partition(case)
    slack_set = set(partition["slack_bus_ids"])
    pv_set = set(partition["pv_bus_ids"])
    rows = []
    for gen_id, row in enumerate(case["gen"], start=1):
        bus_id = int(row[0])
        rows.append({
            "gen_id": gen_id,
            "bus_id": bus_id,
            "pg_mw": float(row[1]),
            "qg_mvar": float(row[2]),
            "qmax_mvar": float(row[3]),
            "qmin_mvar": float(row[4]),
            "vg_pu": float(row[5]),
            "m_base_mva": float(row[6]),
            "status": int(row[7]),
            "pmax_mw": float(row[8]),
            "pmin_mw": float(row[9]),
            "is_slack_bus": bus_id in slack_set,
            "is_pv_bus": bus_id in pv_set,
        })
    return rows


def _snapshot_branches(case: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for branch_id, row in enumerate(case["branch"], start=1):
        rows.append({
            "branch_id": branch_id,
            "from_bus": int(row[0]),
            "to_bus": int(row[1]),
            "r_pu": float(row[2]),
            "x_pu": float(row[3]),
            "b_pu": float(row[4]),
            "rate_a_mva": float(row[5]),
            "rate_b_mva": float(row[6]),
            "rate_c_mva": float(row[7]),
            "tap_ratio": float(row[8]) if float(row[8]) != 0.0 else 1.0,
            "shift_deg": float(row[9]),
            "status": int(row[10]),
            "angmin_deg": float(row[11]),
            "angmax_deg": float(row[12]),
            "element_type": _element_type(row),
        })
    return rows


def _distribute_total(total: float, weights: list[float]) -> list[float]:
    if not weights:
        return []
    positive = [max(0.0, float(w)) for w in weights]
    denom = sum(positive)
    if denom <= 0:
        return [total / len(weights)] * len(weights)
    return [total * (w / denom) for w in positive]


def _generator_results(case: dict[str, Any], p_inj_pu: np.ndarray, q_inj_pu: np.ndarray | None) -> list[dict[str, Any]]:
    bus = np.array(case["bus"], dtype=float)
    base_mva = float(case["baseMVA"])
    partition = bus_partition(case)
    slack_set = set(partition["slack_bus_ids"])
    idx = _bus_index(case)

    gens_by_bus: dict[int, list[tuple[int, list[float]]]] = {}
    for gen_id, row in enumerate(case["gen"], start=1):
        if int(row[7]) == 0:
            continue
        gens_by_bus.setdefault(int(row[0]), []).append((gen_id, row))

    results: list[dict[str, Any]] = []
    for bus_id, gens in sorted(gens_by_bus.items()):
        bus_row = case["bus"][idx[bus_id]]
        bus_p_total = float(p_inj_pu[idx[bus_id]] * base_mva + float(bus_row[2]))
        bus_q_total = None if q_inj_pu is None else float(q_inj_pu[idx[bus_id]] * base_mva + float(bus_row[3]))

        scheduled_p = [float(gen[1]) for _, gen in gens]
        if bus_id in slack_set:
            p_values = _distribute_total(bus_p_total, scheduled_p)
        else:
            p_values = scheduled_p

        if bus_q_total is None:
            q_values: list[float | None] = [None] * len(gens)
        else:
            q_weights = [max(0.0, float(gen[3]) - float(gen[4])) for _, gen in gens]
            q_values = _distribute_total(bus_q_total, q_weights)

        for offset, (gen_id, gen) in enumerate(gens):
            q_value = q_values[offset] if q_inj_pu is not None else None
            results.append({
                "gen_id": gen_id,
                "bus_id": bus_id,
                "pg_mw": round(float(p_values[offset]), 6),
                "qg_mvar": None if q_value is None else round(float(q_value), 6),
                "qmax_mvar": float(gen[3]),
                "qmin_mvar": float(gen[4]),
                "vg_pu": float(gen[5]),
                "status": int(gen[7]),
                "pmax_mw": float(gen[8]),
                "pmin_mw": float(gen[9]),
            })
    return results


def _bus_results(case: dict[str, Any], ac_or_dc: dict[str, Any], gen_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bus = np.array(case["bus"], dtype=float)
    p_inj = ac_or_dc["p_inj_pu"] * float(case["baseMVA"])
    q_inj = None if ac_or_dc["q_inj_pu"] is None else ac_or_dc["q_inj_pu"] * float(case["baseMVA"])
    gen_by_bus: dict[int, list[dict[str, Any]]] = {}
    for row in gen_results:
        gen_by_bus.setdefault(int(row["bus_id"]), []).append(row)

    rows = []
    for pos, raw in enumerate(bus):
        bus_id = int(raw[0])
        gens = gen_by_bus.get(bus_id, [])
        pg_total = sum(float(item["pg_mw"]) for item in gens)
        qg_total = None if q_inj is None else sum(float(item["qg_mvar"] or 0.0) for item in gens)
        rows.append({
            "bus_id": bus_id,
            "type_code": int(raw[1]),
            "type_label": BUS_TYPE_LABEL.get(int(raw[1]), "Unknown"),
            "vm_pu": round(float(ac_or_dc["vm"][pos]), 6),
            "va_deg": round(float(np.rad2deg(ac_or_dc["va"][pos])), 6),
            "pd_mw": float(raw[2]),
            "qd_mvar": float(raw[3]),
            "pg_mw": round(float(pg_total), 6),
            "qg_mvar": None if qg_total is None else round(float(qg_total), 6),
            "p_net_injection_mw": round(float(p_inj[pos]), 6),
            "q_net_injection_mvar": None if q_inj is None else round(float(q_inj[pos]), 6),
        })
    return rows


def _branch_results_ac(case: dict[str, Any], ac_solution: dict[str, Any]) -> list[dict[str, Any]]:
    base_mva = float(case["baseMVA"])
    v = ac_solution["vm"] * np.exp(1j * ac_solution["va"])
    rows = []
    for branch_model, raw in zip(ac_solution["branch_models"], case["branch"]):
        branch_id = int(branch_model["branch_id"])
        if int(raw[10]) == 0:
            rows.append({
                "branch_id": branch_id,
                "from_bus": int(raw[0]),
                "to_bus": int(raw[1]),
                "status": 0,
                "element_type": _element_type(raw),
                "tap_ratio": float(raw[8]) if float(raw[8]) != 0.0 else 1.0,
                "p_from_mw": 0.0,
                "q_from_mvar": 0.0,
                "p_to_mw": 0.0,
                "q_to_mvar": 0.0,
                "p_loss_mw": 0.0,
                "q_loss_mvar": 0.0,
                "s_from_mva": 0.0,
                "s_to_mva": 0.0,
            })
            continue

        i = branch_model["from_idx"]
        j = branch_model["to_idx"]
        i_from = branch_model["yff"] * v[i] + branch_model["yft"] * v[j]
        i_to = branch_model["ytf"] * v[i] + branch_model["ytt"] * v[j]
        s_from = v[i] * np.conj(i_from) * base_mva
        s_to = v[j] * np.conj(i_to) * base_mva
        rows.append({
            "branch_id": branch_id,
            "from_bus": int(raw[0]),
            "to_bus": int(raw[1]),
            "status": 1,
            "element_type": _element_type(raw),
            "tap_ratio": float(raw[8]) if float(raw[8]) != 0.0 else 1.0,
            "p_from_mw": round(float(s_from.real), 6),
            "q_from_mvar": round(float(s_from.imag), 6),
            "p_to_mw": round(float(s_to.real), 6),
            "q_to_mvar": round(float(s_to.imag), 6),
            "p_loss_mw": round(float((s_from + s_to).real), 6),
            "q_loss_mvar": round(float((s_from + s_to).imag), 6),
            "s_from_mva": round(float(abs(s_from)), 6),
            "s_to_mva": round(float(abs(s_to)), 6),
        })
    return rows


def _branch_results_dc(case: dict[str, Any], dc_solution: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    idx = _bus_index(case)
    theta = dc_solution["va"]
    base_mva = float(case["baseMVA"])
    for branch_id, raw in enumerate(case["branch"], start=1):
        if int(raw[10]) == 0:
            rows.append({
                "branch_id": branch_id,
                "from_bus": int(raw[0]),
                "to_bus": int(raw[1]),
                "status": 0,
                "element_type": _element_type(raw),
                "tap_ratio": float(raw[8]) if float(raw[8]) != 0.0 else 1.0,
                "p_from_mw": 0.0,
                "p_to_mw": 0.0,
                "p_loss_mw": 0.0,
            })
            continue
        i = idx[int(raw[0])]
        j = idx[int(raw[1])]
        tap = float(raw[8]) if float(raw[8]) != 0.0 else 1.0
        shift = math.radians(float(raw[9]))
        p_from = (theta[i] - theta[j] - shift) / (float(raw[3]) * tap) * base_mva
        rows.append({
            "branch_id": branch_id,
            "from_bus": int(raw[0]),
            "to_bus": int(raw[1]),
            "status": 1,
            "element_type": _element_type(raw),
            "tap_ratio": tap,
            "p_from_mw": round(float(p_from), 6),
            "p_to_mw": round(float(-p_from), 6),
            "p_loss_mw": 0.0,
        })
    return rows


def _system_summary(case: dict[str, Any], bus_results: list[dict[str, Any]], gen_results: list[dict[str, Any]], branch_results: list[dict[str, Any]], include_q: bool) -> dict[str, Any]:
    total_pd = round(sum(float(row[2]) for row in case["bus"]), 6)
    total_qd = round(sum(float(row[3]) for row in case["bus"]), 6)
    total_pg = round(sum(float(row["pg_mw"]) for row in gen_results), 6)
    total_qg = None if not include_q else round(sum(float(row["qg_mvar"] or 0.0) for row in gen_results), 6)
    total_p_loss = round(sum(float(row["p_loss_mw"]) for row in branch_results), 6)
    total_q_loss = None if not include_q else round(sum(float(row["q_loss_mvar"]) for row in branch_results), 6)
    min_bus = min(bus_results, key=lambda row: row["vm_pu"])
    max_bus = max(bus_results, key=lambda row: row["vm_pu"])
    return {
        "total_load_p_mw": total_pd,
        "total_load_q_mvar": total_qd,
        "total_gen_p_mw": total_pg,
        "total_gen_q_mvar": total_qg,
        "total_loss_p_mw": total_p_loss,
        "total_loss_q_mvar": total_q_loss,
        "min_vm_bus_id": int(min_bus["bus_id"]),
        "min_vm_pu": float(min_bus["vm_pu"]),
        "max_vm_bus_id": int(max_bus["bus_id"]),
        "max_vm_pu": float(max_bus["vm_pu"]),
        "num_active_branches": sum(1 for row in branch_results if int(row["status"]) == 1),
    }


def _grid_reference(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_name": case["case_name"],
        "source_library": case.get("source_library"),
        "source_url": case.get("source_url"),
        "matpower_case_format_version": case.get("matpower_case_format_version"),
        "base_mva": float(case["baseMVA"]),
        "counts": {
            "num_buses": len(case["bus"]),
            "num_generators": len(case["gen"]),
            "num_branches": len(case["branch"]),
        },
        "bus_partition_counts": {
            "num_slack_buses": len(bus_partition(case)["slack_bus_ids"]),
            "num_pv_buses": len(bus_partition(case)["pv_bus_ids"]),
            "num_pq_buses": len(bus_partition(case)["pq_bus_ids"]),
        },
        "data_digest": case["data_digest"],
    }


def _base_snapshot(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "bus_partition": bus_partition(case),
        "buses": _snapshot_buses(case),
        "generators": _snapshot_generators(case),
        "branches": _snapshot_branches(case),
    }


def _scenario_input_state(mutated_case: dict[str, Any]) -> dict[str, Any]:
    bus_loads = []
    for row in mutated_case["bus"]:
        bus_loads.append({
            "bus_id": int(row[0]),
            "pd_mw": float(row[2]),
            "qd_mvar": float(row[3]),
        })
    generator_setpoints = []
    for gen_id, row in enumerate(mutated_case["gen"], start=1):
        generator_setpoints.append({
            "gen_id": gen_id,
            "bus_id": int(row[0]),
            "pg_mw": float(row[1]),
            "qg_mvar_initial": float(row[2]),
            "qmax_mvar": float(row[3]),
            "qmin_mvar": float(row[4]),
            "vg_pu": float(row[5]),
            "status": int(row[7]),
            "pmax_mw": float(row[8]),
            "pmin_mw": float(row[9]),
        })
    branch_state = []
    for branch_id, row in enumerate(mutated_case["branch"], start=1):
        branch_state.append({
            "branch_id": branch_id,
            "from_bus": int(row[0]),
            "to_bus": int(row[1]),
            "status": int(row[10]),
            "tap_ratio": float(row[8]) if float(row[8]) != 0.0 else 1.0,
            "shift_deg": float(row[9]),
            "element_type": _element_type(row),
        })
    return {
        "bus_partition": bus_partition(mutated_case),
        "buses": _snapshot_buses(mutated_case),
        "generators": _snapshot_generators(mutated_case),
        "branches": _snapshot_branches(mutated_case),
        "bus_loads": bus_loads,
        "generator_setpoints": generator_setpoints,
        "branch_state": branch_state,
        "totals": {
            "total_pd_mw": round(sum(float(row[2]) for row in mutated_case["bus"]), 6),
            "total_qd_mvar": round(sum(float(row[3]) for row in mutated_case["bus"]), 6),
            "total_scheduled_pg_mw": round(sum(float(row[1]) for row in mutated_case["gen"] if int(row[7]) == 1), 6),
            "num_active_generators": sum(1 for row in mutated_case["gen"] if int(row[7]) == 1),
            "num_active_branches": sum(1 for row in mutated_case["branch"] if int(row[10]) == 1),
        },
    }


def solve_scenario(
    case_name: str,
    scenario_spec: dict[str, Any],
    solver_config: dict[str, Any],
    dataset_id: str,
    split: str,
    dataset_version: str = "0.1.0",
    generated_at: str = "1970-01-01T00:00:00Z",
    schema_versions: dict[str, str] | None = None,
) -> dict[str, Any]:
    base_case = load_case(case_name)
    mutated_case = apply_scenario(base_case, scenario_spec)
    ac_cfg = solver_config.get("ac", {})
    solver_config_digest = stable_hex(solver_config, length=16)
    schema_versions = schema_versions or {
        "question_item": "0.2.0",
        "scenario_record": "0.2.0",
    }
    ac_solution = _ac_power_flow(
        mutated_case,
        tolerance=float(ac_cfg.get("tolerance", 1e-8)),
        max_iterations=int(ac_cfg.get("max_iterations", 30)),
    )
    dc_solution = _dc_power_flow(mutated_case)

    ac_gen = _generator_results(mutated_case, ac_solution["p_inj_pu"], ac_solution["q_inj_pu"])
    dc_gen = _generator_results(mutated_case, dc_solution["p_inj_pu"], None)

    ac_bus = _bus_results(mutated_case, ac_solution, ac_gen)
    dc_bus = _bus_results(mutated_case, dc_solution, dc_gen)

    ac_branch = _branch_results_ac(mutated_case, ac_solution)
    dc_branch = _branch_results_dc(mutated_case, dc_solution)

    record = {
        "dataset_id": dataset_id,
        "scenario_id": scenario_spec["scenario_id"],
        "source_case": case_name,
        "split": split,
        "grid_reference": _grid_reference(base_case),
        "base_grid_snapshot": _base_snapshot(base_case),
        "scenario_spec": scenario_spec,
        "scenario_input_state": _scenario_input_state(mutated_case),
        "powerflow_results": {
            "ac": {
                "converged": True,
                "solver_name": ac_solution["solver_name"],
                "iterations": ac_solution["iterations"],
                "tolerance": ac_solution["tolerance"],
                "solver_options": {
                    "max_iterations": int(ac_cfg.get("max_iterations", 30)),
                    "tolerance": float(ac_cfg.get("tolerance", 1e-8)),
                },
                "reference_bus_ids": bus_partition(mutated_case)["slack_bus_ids"],
                "system_summary": _system_summary(mutated_case, ac_bus, ac_gen, ac_branch, include_q=True),
                "bus_results": ac_bus,
                "generator_results": ac_gen,
                "branch_results": ac_branch,
            },
            "dc": {
                "converged": True,
                "solver_name": dc_solution["solver_name"],
                "iterations": dc_solution["iterations"],
                "tolerance": dc_solution["tolerance"],
                "solver_options": {
                    "dc_voltage_magnitude_pu": 1.0,
                    "branch_resistance_ignored": True,
                },
                "reference_bus_ids": bus_partition(mutated_case)["slack_bus_ids"],
                "system_summary": _system_summary(mutated_case, dc_bus, dc_gen, dc_branch, include_q=False),
                "bus_results": dc_bus,
                "generator_results": dc_gen,
                "branch_results": dc_branch,
            },
        },
        "provenance": {
            "dataset_version": dataset_version,
            "generated_at": generated_at,
            "schema_versions": schema_versions,
            "solver_config_digest": solver_config_digest,
            "source_library": base_case.get("source_library"),
            "source_reference": base_case.get("source_url"),
        },
        "metadata": {
            "seed": int(scenario_spec["seed"]),
            "scenario_text": scenario_summary_text(case_name, scenario_spec),
            "mutation_ops": [mutation["op"] for mutation in scenario_spec.get("mutations", [])],
            "num_mutations": len(scenario_spec.get("mutations", [])),
            "case_family": "transmission",
            "solver_bundle": ["ac", "dc"],
            "solver_name_ac": ac_solution["solver_name"],
            "solver_name_dc": dc_solution["solver_name"],
            "solver_config_digest": solver_config_digest,
            "schema_versions": schema_versions,
            "generated_at": generated_at,
            "dataset_version": dataset_version,
            "solver_assumptions": [
                "single_slack_bus",
                "generator_q_limits_not_enforced",
                "dc_voltage_magnitude_fixed_at_1pu"
            ],
        },
    }
    return record
