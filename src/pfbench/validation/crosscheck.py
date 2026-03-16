from __future__ import annotations

import contextlib
import copy
import io
import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np

from pfbench.io import load_yaml, read_jsonl, write_jsonl
from pfbench.powerflow.cases import load_case
from pfbench.powerflow.scenario import apply_scenario
from pfbench.utils import repo_root, stable_hex


DEFAULT_CROSS_VALIDATION_CONFIG: dict[str, Any] = {
    "pandapower": {
        "preprocess": {
            "missing_base_kv_fill_kv": "auto",
        },
        "ac": {
            "algorithm": "nr",
            "calculate_voltage_angles": True,
            "init": "flat",
            "enforce_q_lims": False,
            "check_connectivity": True,
        },
        "dc": {
            "check_connectivity": True,
        },
        "tolerances": {
            "ac_bus_vm_pu": 1e-4,
            "ac_bus_va_deg": 1e-2,
            "ac_bus_pg_mw": 1e-4,
            "ac_bus_qg_mvar": 1e-2,
            "ac_branch_p_from_mw": 1e-3,
            "ac_branch_q_from_mvar": 1e-2,
            "ac_branch_p_to_mw": 1e-3,
            "ac_branch_q_to_mvar": 1e-2,
            "dc_bus_va_deg": 1e-2,
            "dc_bus_pg_mw": 1e-4,
            "dc_branch_p_from_mw": 1e-3,
            "dc_branch_p_to_mw": 1e-3,
        },
        "report_top_n": 10,
    }
}


class CrossValidationError(RuntimeError):
    """Raised when pandapower cross-validation cannot be completed."""


def _deep_update(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_update(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_cross_validation_config(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or repo_root() / "configs" / "validation.yaml"
    if not path.exists():
        return copy.deepcopy(DEFAULT_CROSS_VALIDATION_CONFIG)
    raw = load_yaml(path)
    return _deep_update(DEFAULT_CROSS_VALIDATION_CONFIG, raw.get("cross_validation", raw))


def _default_summary_path(scenarios_path: Path) -> Path:
    if scenarios_path.stem == "scenarios":
        return scenarios_path.with_name("CROSS_VALIDATION_SUMMARY.json")
    stem = scenarios_path.stem.replace("_scenarios", "")
    return scenarios_path.with_name(f"{stem}_cross_validation_summary.json")


def _default_details_path(scenarios_path: Path) -> Path:
    if scenarios_path.stem == "scenarios":
        return scenarios_path.with_name("cross_validation_results.jsonl")
    stem = scenarios_path.stem.replace("_scenarios", "")
    return scenarios_path.with_name(f"{stem}_cross_validation_results.jsonl")


def _default_report_path(scenarios_path: Path) -> Path:
    if scenarios_path.stem == "scenarios":
        return scenarios_path.with_name("CROSS_VALIDATION_REPORT.md")
    stem = scenarios_path.stem.replace("_scenarios", "")
    return scenarios_path.with_name(f"{stem}_cross_validation_report.md")


def _pandapower_imports() -> tuple[Any, Any]:
    try:
        import pandapower as pp
        import pandapower.converter as pc
    except Exception as exc:  # pragma: no cover - exercised in environments without pandapower
        raise CrossValidationError(
            "pandapower is required for cross-validation. Install the repository environment first."
        ) from exc
    return pp, pc


def _ppc_from_case(case: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    bus = np.array(case["bus"], dtype=float)
    gen = np.array(case["gen"], dtype=float)
    branch = np.array(case["branch"], dtype=float)

    missing_mask = np.isclose(bus[:, 9], 0.0)
    fill_value: float | None = None
    if missing_mask.any():
        fill_cfg = config["pandapower"]["preprocess"].get("missing_base_kv_fill_kv", "auto")
        if fill_cfg == "auto":
            nonzero = bus[~missing_mask, 9]
            fill_value = float(nonzero[0]) if nonzero.size else 1.0
        else:
            fill_value = float(fill_cfg)
        bus[missing_mask, 9] = fill_value

    return (
        {
            "version": case.get("matpower_case_format_version", "2"),
            "baseMVA": float(case["baseMVA"]),
            "bus": bus,
            "gen": gen,
            "branch": branch,
        },
        {
            "base_kv_filled_bus_ids": [
                int(case["bus"][idx][0])
                for idx, is_missing in enumerate(missing_mask)
                if is_missing
            ],
            "base_kv_fill_value_kv": fill_value,
        },
    )


def _solve_with_pandapower(
    case: dict[str, Any],
    mode: str,
    config: dict[str, Any],
) -> tuple[Any, dict[str, Any], str]:
    pp, pc = _pandapower_imports()
    ppc, preprocess = _ppc_from_case(case, config)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            net = pc.from_ppc(ppc, validate_conversion=False)
            _apply_branch_status(case, net)
            if mode == "ac":
                pp.runpp(net, **config["pandapower"]["ac"])
            elif mode == "dc":
                pp.rundcpp(net, **config["pandapower"]["dc"])
            else:  # pragma: no cover - internal misuse
                raise ValueError(f"Unsupported pandapower mode: {mode}")
    return net, preprocess, pp.__version__


def _apply_branch_status(case: dict[str, Any], net: Any) -> None:
    """Project MATPOWER branch status back onto converted pandapower elements.

    `pandapower.converter.from_ppc()` preserves the branch lookup, but some
    branch-backed element tables can come back in-service even when the source
    MATPOWER row had `status = 0`. Cross-validation must solve the exact same
    mutated topology as the scenario record, so we reapply branch status here.
    """

    branch_lookup = net._from_ppc_lookups["branch"]
    for input_idx, row in branch_lookup.iterrows():
        in_service = bool(int(case["branch"][int(input_idx)][10]))
        element = int(row["element"])
        element_type = str(row["element_type"])
        if element_type == "line":
            net.line.at[element, "in_service"] = in_service
        elif element_type == "trafo":
            net.trafo.at[element, "in_service"] = in_service
        elif element_type == "impedance":
            net.impedance.at[element, "in_service"] = in_service
        else:  # pragma: no cover - unsupported by current cases
            raise CrossValidationError(f"Unsupported pandapower branch element type: {element_type}")


def _bus_series(net: Any, bus_ids: list[int], field: str) -> np.ndarray:
    return np.asarray([float(net.res_bus.at[bus_id, field]) for bus_id in bus_ids], dtype=float)


def _bus_generation_totals(net: Any, bus_ids: list[int], include_q: bool) -> tuple[np.ndarray, np.ndarray | None]:
    pg_by_bus = {bus_id: 0.0 for bus_id in bus_ids}
    qg_by_bus = {bus_id: 0.0 for bus_id in bus_ids} if include_q else None

    if hasattr(net, "ext_grid") and not net.ext_grid.empty:
        for element_id, row in net.ext_grid.iterrows():
            if not bool(row["in_service"]):
                continue
            bus_id = int(row["bus"])
            pg_by_bus[bus_id] += float(net.res_ext_grid.at[element_id, "p_mw"])
            if include_q and qg_by_bus is not None:
                qg_by_bus[bus_id] += float(net.res_ext_grid.at[element_id, "q_mvar"])

    if hasattr(net, "gen") and not net.gen.empty:
        for element_id, row in net.gen.iterrows():
            if not bool(row["in_service"]):
                continue
            bus_id = int(row["bus"])
            pg_by_bus[bus_id] += float(net.res_gen.at[element_id, "p_mw"])
            if include_q and qg_by_bus is not None:
                qg_by_bus[bus_id] += float(net.res_gen.at[element_id, "q_mvar"])

    ordered_pg = np.asarray([pg_by_bus[bus_id] for bus_id in bus_ids], dtype=float)
    ordered_qg = None
    if include_q and qg_by_bus is not None:
        ordered_qg = np.asarray([qg_by_bus[bus_id] for bus_id in bus_ids], dtype=float)
    return ordered_pg, ordered_qg


def _branch_result_arrays(case: dict[str, Any], net: Any) -> dict[str, np.ndarray]:
    count = len(case["branch"])
    arrays = {
        "p_from_mw": np.zeros(count, dtype=float),
        "q_from_mvar": np.zeros(count, dtype=float),
        "p_to_mw": np.zeros(count, dtype=float),
        "q_to_mvar": np.zeros(count, dtype=float),
    }
    branch_lookup = net._from_ppc_lookups["branch"]

    for input_idx, row in branch_lookup.iterrows():
        case_row = case["branch"][int(input_idx)]
        if int(case_row[10]) == 0:
            continue
        element = int(row["element"])
        element_type = str(row["element_type"])

        if element_type == "line":
            if not bool(net.line.at[element, "in_service"]):
                continue
            result = net.res_line.loc[element]
            arrays["p_from_mw"][int(input_idx)] = float(result["p_from_mw"])
            arrays["q_from_mvar"][int(input_idx)] = float(result["q_from_mvar"])
            arrays["p_to_mw"][int(input_idx)] = float(result["p_to_mw"])
            arrays["q_to_mvar"][int(input_idx)] = float(result["q_to_mvar"])
        elif element_type == "impedance":
            if not bool(net.impedance.at[element, "in_service"]):
                continue
            result = net.res_impedance.loc[element]
            arrays["p_from_mw"][int(input_idx)] = float(result["p_from_mw"])
            arrays["q_from_mvar"][int(input_idx)] = float(result["q_from_mvar"])
            arrays["p_to_mw"][int(input_idx)] = float(result["p_to_mw"])
            arrays["q_to_mvar"][int(input_idx)] = float(result["q_to_mvar"])
        elif element_type == "trafo":
            if not bool(net.trafo.at[element, "in_service"]):
                continue
            result = net.res_trafo.loc[element]
            hv_bus = int(net.trafo.at[element, "hv_bus"])
            lv_bus = int(net.trafo.at[element, "lv_bus"])
            from_bus = int(case_row[0])
            to_bus = int(case_row[1])
            if from_bus == hv_bus and to_bus == lv_bus:
                arrays["p_from_mw"][int(input_idx)] = float(result["p_hv_mw"])
                arrays["q_from_mvar"][int(input_idx)] = float(result["q_hv_mvar"])
                arrays["p_to_mw"][int(input_idx)] = float(result["p_lv_mw"])
                arrays["q_to_mvar"][int(input_idx)] = float(result["q_lv_mvar"])
            elif from_bus == lv_bus and to_bus == hv_bus:
                arrays["p_from_mw"][int(input_idx)] = float(result["p_lv_mw"])
                arrays["q_from_mvar"][int(input_idx)] = float(result["q_lv_mvar"])
                arrays["p_to_mw"][int(input_idx)] = float(result["p_hv_mw"])
                arrays["q_to_mvar"][int(input_idx)] = float(result["q_hv_mvar"])
            else:
                raise CrossValidationError(
                    f"Transformer orientation mismatch for branch {int(input_idx) + 1}: "
                    f"case=({from_bus},{to_bus}) pandapower=({hv_bus},{lv_bus})"
                )
        else:  # pragma: no cover - unsupported by current cases
            raise CrossValidationError(f"Unsupported pandapower branch element type: {element_type}")

    return arrays


def _normalize_by_reference(values: np.ndarray, reference_index: int) -> np.ndarray:
    reference_value = float(values[reference_index])
    return np.asarray(values - reference_value, dtype=float)


def _metric_result(
    rows: list[dict[str, Any]],
    field: str,
    values: np.ndarray,
    id_field: str,
    tolerance: float,
) -> dict[str, Any]:
    if len(rows) != len(values):
        raise CrossValidationError(
            f"Cross-validation length mismatch for field {field}: {len(rows)} record rows vs {len(values)} pandapower rows."
        )

    max_abs_diff = 0.0
    worst_observation: dict[str, Any] | None = None
    for idx, row in enumerate(rows):
        ours = row.get(field)
        if ours is None:
            continue
        other = float(values[idx])
        diff = abs(float(ours) - other)
        if diff >= max_abs_diff:
            max_abs_diff = diff
            worst_observation = {
                id_field: int(row[id_field]),
                "ours": float(ours),
                "pandapower": other,
                "abs_diff": float(diff),
            }

    return {
        "tolerance": float(tolerance),
        "max_abs_diff": float(max_abs_diff),
        "within_tolerance": float(max_abs_diff) <= float(tolerance),
        "worst_observation": worst_observation,
    }


def _metric_summary(results: list[dict[str, Any]], metric_name: str) -> dict[str, Any]:
    worst_result = max(results, key=lambda row: row["metrics"][metric_name]["max_abs_diff"])
    metric = worst_result["metrics"][metric_name]
    return {
        "tolerance": metric["tolerance"],
        "max_abs_diff": metric["max_abs_diff"],
        "num_scenarios_within_tolerance": sum(
            1 for row in results if row["metrics"][metric_name]["within_tolerance"]
        ),
        "worst_scenario_id": worst_result["scenario_id"],
        "worst_observation": metric["worst_observation"],
    }


def _cross_validation_report(summary: dict[str, Any]) -> str:
    metric_lines = []
    for metric_name, metric in sorted(summary["metric_summary"].items()):
        metric_lines.append(
            f"- `{metric_name}`: max_abs_diff={metric['max_abs_diff']:.6g}, "
            f"tolerance={metric['tolerance']:.6g}, "
            f"within_tolerance={metric['num_scenarios_within_tolerance']}/{summary['num_scenarios']}, "
            f"worst_scenario_id=`{metric['worst_scenario_id']}`"
        )
    failed_lines = "\n".join(f"- `{scenario_id}`" for scenario_id in summary["failed_scenario_ids"]) or "- None"
    return (
        "# Pandapower cross-validation report\n\n"
        f"- Validation engine: `pandapower {summary['pandapower_version']}`\n"
        f"- Scenarios validated: {summary['num_scenarios']}\n"
        f"- Passed all tolerances: {summary['num_passed']}\n"
        f"- Failed one or more tolerances: {summary['num_failed']}\n"
        f"- All passed: `{summary['all_passed']}`\n"
        f"- Scenarios requiring temporary base_kV fill for pandapower conversion: {summary['num_scenarios_with_base_kv_fill']}\n\n"
        "## Metric summary\n\n"
        + "\n".join(metric_lines)
        + "\n\n## Failed scenarios\n\n"
        + failed_lines
        + "\n"
    )


def cross_validate_record(
    scenario_record: dict[str, Any],
    config: dict[str, Any] | None = None,
    config_path: Path | None = None,
) -> dict[str, Any]:
    cfg = config or load_cross_validation_config(config_path)

    base_case = load_case(scenario_record["source_case"])
    mutated_case = apply_scenario(base_case, scenario_record["scenario_spec"])
    ac_net, preprocess, pandapower_version = _solve_with_pandapower(mutated_case, mode="ac", config=cfg)
    dc_net, _, _ = _solve_with_pandapower(mutated_case, mode="dc", config=cfg)

    bus_ids = [int(row["bus_id"]) for row in scenario_record["powerflow_results"]["ac"]["bus_results"]]
    ac_bus_vm = _bus_series(ac_net, bus_ids, "vm_pu")
    ac_bus_va = _bus_series(ac_net, bus_ids, "va_degree")
    dc_bus_va = _bus_series(dc_net, bus_ids, "va_degree")

    ac_bus_pg, ac_bus_qg = _bus_generation_totals(ac_net, bus_ids, include_q=True)
    dc_bus_pg, _ = _bus_generation_totals(dc_net, bus_ids, include_q=False)

    reference_bus_id = int(scenario_record["powerflow_results"]["dc"]["reference_bus_ids"][0])
    reference_index = bus_ids.index(reference_bus_id)
    dc_bus_va = _normalize_by_reference(dc_bus_va, reference_index)

    ac_branch = _branch_result_arrays(mutated_case, ac_net)
    dc_branch = _branch_result_arrays(mutated_case, dc_net)

    tolerances = cfg["pandapower"]["tolerances"]
    metrics = {
        "ac_bus_vm_pu": _metric_result(
            scenario_record["powerflow_results"]["ac"]["bus_results"],
            "vm_pu",
            ac_bus_vm,
            "bus_id",
            tolerances["ac_bus_vm_pu"],
        ),
        "ac_bus_va_deg": _metric_result(
            scenario_record["powerflow_results"]["ac"]["bus_results"],
            "va_deg",
            ac_bus_va,
            "bus_id",
            tolerances["ac_bus_va_deg"],
        ),
        "ac_bus_pg_mw": _metric_result(
            scenario_record["powerflow_results"]["ac"]["bus_results"],
            "pg_mw",
            ac_bus_pg,
            "bus_id",
            tolerances["ac_bus_pg_mw"],
        ),
        "ac_bus_qg_mvar": _metric_result(
            scenario_record["powerflow_results"]["ac"]["bus_results"],
            "qg_mvar",
            np.asarray(ac_bus_qg if ac_bus_qg is not None else np.zeros_like(ac_bus_pg)),
            "bus_id",
            tolerances["ac_bus_qg_mvar"],
        ),
        "ac_branch_p_from_mw": _metric_result(
            scenario_record["powerflow_results"]["ac"]["branch_results"],
            "p_from_mw",
            ac_branch["p_from_mw"],
            "branch_id",
            tolerances["ac_branch_p_from_mw"],
        ),
        "ac_branch_q_from_mvar": _metric_result(
            scenario_record["powerflow_results"]["ac"]["branch_results"],
            "q_from_mvar",
            ac_branch["q_from_mvar"],
            "branch_id",
            tolerances["ac_branch_q_from_mvar"],
        ),
        "ac_branch_p_to_mw": _metric_result(
            scenario_record["powerflow_results"]["ac"]["branch_results"],
            "p_to_mw",
            ac_branch["p_to_mw"],
            "branch_id",
            tolerances["ac_branch_p_to_mw"],
        ),
        "ac_branch_q_to_mvar": _metric_result(
            scenario_record["powerflow_results"]["ac"]["branch_results"],
            "q_to_mvar",
            ac_branch["q_to_mvar"],
            "branch_id",
            tolerances["ac_branch_q_to_mvar"],
        ),
        "dc_bus_va_deg": _metric_result(
            scenario_record["powerflow_results"]["dc"]["bus_results"],
            "va_deg",
            dc_bus_va,
            "bus_id",
            tolerances["dc_bus_va_deg"],
        ),
        "dc_bus_pg_mw": _metric_result(
            scenario_record["powerflow_results"]["dc"]["bus_results"],
            "pg_mw",
            dc_bus_pg,
            "bus_id",
            tolerances["dc_bus_pg_mw"],
        ),
        "dc_branch_p_from_mw": _metric_result(
            scenario_record["powerflow_results"]["dc"]["branch_results"],
            "p_from_mw",
            dc_branch["p_from_mw"],
            "branch_id",
            tolerances["dc_branch_p_from_mw"],
        ),
        "dc_branch_p_to_mw": _metric_result(
            scenario_record["powerflow_results"]["dc"]["branch_results"],
            "p_to_mw",
            dc_branch["p_to_mw"],
            "branch_id",
            tolerances["dc_branch_p_to_mw"],
        ),
    }

    failing_metrics = [
        metric_name
        for metric_name, metric in metrics.items()
        if not metric["within_tolerance"]
    ]
    return {
        "scenario_id": scenario_record["scenario_id"],
        "source_case": scenario_record["source_case"],
        "split": scenario_record["split"],
        "pandapower_version": pandapower_version,
        "passed": not failing_metrics,
        "failing_metrics": failing_metrics,
        "preprocess": preprocess,
        "metrics": metrics,
    }


def cross_validate_scenarios(
    scenarios_path: Path,
    config_path: Path | None = None,
    summary_path: Path | None = None,
    details_path: Path | None = None,
    report_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Path]]:
    cfg = load_cross_validation_config(config_path)
    scenarios = list(read_jsonl(scenarios_path))
    results = [cross_validate_record(scenario, config=cfg) for scenario in scenarios]

    if not results:
        raise CrossValidationError(f"No scenarios found for cross-validation in {scenarios_path}")

    summary = {
        "validation_engine": "pandapower",
        "pandapower_version": results[0]["pandapower_version"],
        "config_digest": stable_hex(cfg, length=16),
        "num_scenarios": len(results),
        "num_passed": sum(1 for row in results if row["passed"]),
        "num_failed": sum(1 for row in results if not row["passed"]),
        "all_passed": all(row["passed"] for row in results),
        "failed_scenario_ids": [row["scenario_id"] for row in results if not row["passed"]],
        "num_scenarios_with_base_kv_fill": sum(
            1 for row in results if row["preprocess"]["base_kv_filled_bus_ids"]
        ),
        "metric_summary": {
            metric_name: _metric_summary(results, metric_name)
            for metric_name in sorted(results[0]["metrics"])
        },
    }

    resolved_summary_path = summary_path or _default_summary_path(scenarios_path)
    resolved_details_path = details_path or _default_details_path(scenarios_path)
    resolved_report_path = report_path or _default_report_path(scenarios_path)

    resolved_summary_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_jsonl(resolved_details_path, results)
    resolved_report_path.write_text(_cross_validation_report(summary), encoding="utf-8")

    return summary, {
        "summary_path": resolved_summary_path,
        "details_path": resolved_details_path,
        "report_path": resolved_report_path,
    }
