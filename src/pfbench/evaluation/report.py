from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from pfbench.io import read_jsonl
from pfbench.utils import repo_root


def _related_jsonl_path(dataset_path: Path, canonical_name: str, suffix: str) -> Path | None:
    if dataset_path.stem == canonical_name:
        candidate = dataset_path.with_name(f"{suffix}.jsonl")
    else:
        stem = dataset_path.stem.replace(f"_{canonical_name}", "")
        candidate = dataset_path.with_name(f"{stem}_{suffix}.jsonl")
    return candidate if candidate.exists() else None


def _auto_scenarios_path(dataset_path: Path) -> Path | None:
    return _related_jsonl_path(dataset_path, canonical_name="questions", suffix="scenarios")


def _auto_failed_scenarios_path(dataset_path: Path) -> Path | None:
    return _related_jsonl_path(dataset_path, canonical_name="questions", suffix="failed_scenarios")


def _range(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"min": min(values), "max": max(values)}


def write_report(dataset_path: Path, report_path: Path | None = None) -> tuple[dict[str, Any], Path]:
    questions = list(read_jsonl(dataset_path))
    scenarios_path = _auto_scenarios_path(dataset_path)
    scenarios = list(read_jsonl(scenarios_path)) if scenarios_path else []
    failed_scenarios_path = _auto_failed_scenarios_path(dataset_path)
    failed_scenarios = list(read_jsonl(failed_scenarios_path)) if failed_scenarios_path else []

    by_case = Counter(row["source_case"] for row in questions)
    by_split = Counter(row["split"] for row in questions)
    by_query = Counter(row["query_family"] for row in questions)
    by_mutation = Counter(
        mutation
        for row in scenarios
        for mutation in row.get("metadata", {}).get("mutation_ops", [])
    )

    scenario_success_by_case = Counter(row["source_case"] for row in scenarios)
    scenario_failure_by_case = Counter(row["source_case"] for row in failed_scenarios)
    scenario_attempts_by_case = {
        case: scenario_success_by_case.get(case, 0) + scenario_failure_by_case.get(case, 0)
        for case in sorted(set(scenario_success_by_case) | set(scenario_failure_by_case))
    }

    total_load_values = [
        float(row["scenario_input_state"]["totals"]["total_pd_mw"])
        for row in scenarios
    ]
    total_gen_values = [
        float(row["scenario_input_state"]["totals"]["total_scheduled_pg_mw"])
        for row in scenarios
    ]
    voltage_values = [
        float(bus["vm_pu"])
        for row in scenarios
        for bus in row.get("powerflow_results", {}).get("ac", {}).get("bus_results", [])
    ]
    branch_p_values = [
        abs(float(branch["p_from_mw"]))
        for row in scenarios
        for branch in row.get("powerflow_results", {}).get("ac", {}).get("branch_results", [])
        if int(branch["status"]) == 1
    ]
    branch_q_values = [
        abs(float(branch["q_from_mvar"]))
        for row in scenarios
        for branch in row.get("powerflow_results", {}).get("ac", {}).get("branch_results", [])
        if int(branch["status"]) == 1 and "q_from_mvar" in branch
    ]
    ac_balance_residual_values = [
        abs(float(row.get("data_quality_flags", {}).get("ac_power_balance_residual_mw", 0.0)))
        for row in scenarios
    ]
    dc_balance_residual_values = [
        abs(float(row.get("data_quality_flags", {}).get("dc_power_balance_residual_mw", 0.0)))
        for row in scenarios
    ]

    scenario_checks = {
        "has_base_grid_snapshot": sum(1 for row in scenarios if "base_grid_snapshot" in row),
        "has_scenario_input_state": sum(1 for row in scenarios if "scenario_input_state" in row),
        "has_mutated_bus_snapshot": sum(1 for row in scenarios if row.get("scenario_input_state", {}).get("buses")),
        "has_mutated_generator_snapshot": sum(1 for row in scenarios if row.get("scenario_input_state", {}).get("generators")),
        "has_mutated_branch_snapshot": sum(1 for row in scenarios if row.get("scenario_input_state", {}).get("branches")),
        "has_ac_results": sum(1 for row in scenarios if row.get("powerflow_results", {}).get("ac")),
        "has_dc_results": sum(1 for row in scenarios if row.get("powerflow_results", {}).get("dc")),
        "has_bus_partition": sum(
            1 for row in scenarios
            if row.get("scenario_input_state", {}).get("bus_partition")
        ),
    }
    data_quality_counts = {
        "scenarios_with_base_kv_missing": sum(
            1 for row in scenarios
            if row.get("data_quality_flags", {}).get("base_kv_missing_bus_ids")
        ),
        "scenarios_with_source_voltage_limit_inconsistency": sum(
            1 for row in scenarios
            if row.get("data_quality_flags", {}).get("source_voltage_limit_inconsistency_bus_ids")
        ),
        "scenarios_with_source_generator_q_limit_inconsistency": sum(
            1 for row in scenarios
            if row.get("data_quality_flags", {}).get("source_generator_q_limit_inconsistency_gen_ids")
        ),
        "scenarios_with_missing_branch_ratings": sum(
            1 for row in scenarios
            if row.get("data_quality_flags", {}).get("missing_branch_rating_branch_ids")
        ),
    }

    summary = {
        "num_questions": len(questions),
        "num_scenarios": len(scenarios),
        "num_failed_scenarios": len(failed_scenarios),
        "by_case": dict(by_case),
        "by_split": dict(by_split),
        "by_query_family": dict(by_query),
        "by_mutation": dict(by_mutation),
        "scenario_success_by_case": dict(scenario_success_by_case),
        "scenario_failure_by_case": dict(scenario_failure_by_case),
        "scenario_attempts_by_case": scenario_attempts_by_case,
        "total_load_p_mw_range": _range(total_load_values),
        "total_scheduled_pg_mw_range": _range(total_gen_values),
        "voltage_magnitude_pu_range": _range(voltage_values),
        "branch_abs_p_from_mw_range": _range(branch_p_values),
        "branch_abs_q_from_mvar_range": _range(branch_q_values),
        "ac_power_balance_residual_mw_range": _range(ac_balance_residual_values),
        "dc_power_balance_residual_mw_range": _range(dc_balance_residual_values),
        "scenario_completeness": scenario_checks,
        "data_quality_counts": data_quality_counts,
    }

    if report_path is None:
        report_path = repo_root() / "reports" / "pfbench_demo_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# pfbench report",
        "",
        f"- Number of questions: {len(questions)}",
        f"- Number of scenarios: {len(scenarios)}",
        f"- Number of failed scenarios: {len(failed_scenarios)}",
        "",
        "## Question counts by case",
        "",
    ]
    for key, value in sorted(by_case.items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Question counts by split", ""]
    for key, value in sorted(by_split.items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Question counts by query family", ""]
    for key, value in sorted(by_query.items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Scenario solve status by case", ""]
    for key in sorted(scenario_attempts_by_case):
        attempts = scenario_attempts_by_case[key]
        success = scenario_success_by_case.get(key, 0)
        fail = scenario_failure_by_case.get(key, 0)
        rate = 0.0 if attempts == 0 else success / attempts
        lines.append(f"- {key}: success={success}, failed={fail}, success_rate={rate:.2%}")
    lines += ["", "## Mutation counts", ""]
    for key, value in sorted(by_mutation.items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Scenario metric ranges", ""]
    for label, value in [
        ("Total load P (MW)", summary["total_load_p_mw_range"]),
        ("Total scheduled generation P (MW)", summary["total_scheduled_pg_mw_range"]),
        ("Voltage magnitude (p.u.)", summary["voltage_magnitude_pu_range"]),
        ("Absolute branch P_from (MW)", summary["branch_abs_p_from_mw_range"]),
        ("Absolute branch Q_from (MVAr)", summary["branch_abs_q_from_mvar_range"]),
        ("Absolute AC power-balance residual (MW)", summary["ac_power_balance_residual_mw_range"]),
        ("Absolute DC power-balance residual (MW)", summary["dc_power_balance_residual_mw_range"]),
    ]:
        if value is None:
            lines.append(f"- {label}: n/a")
        else:
            lines.append(f"- {label}: min={value['min']:.6f}, max={value['max']:.6f}")
    if scenarios:
        lines += ["", "## Scenario completeness", ""]
        for key, value in sorted(scenario_checks.items()):
            lines.append(f"- {key}: {value}/{len(scenarios)}")
        lines += ["", "## Data quality flags", ""]
        for key, value in sorted(data_quality_counts.items()):
            lines.append(f"- {key}: {value}/{len(scenarios)}")
        lines += ["", "## Notes", ""]
        lines.append("- Scenario records include base grid snapshot, scenario input state, and AC/DC power flow results.")
        lines.append("- Scenario records also carry explicit data-quality flags for inherited source-case artifacts and balance residuals.")
        lines.append("- Question items reference scenario_id and keep benchmark-specific fields compact.")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary, report_path
