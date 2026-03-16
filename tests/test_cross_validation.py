from __future__ import annotations

from pfbench.powerflow.scenario import generate_scenario_spec
from pfbench.powerflow.solver import solve_scenario
from pfbench.validation import cross_validate_record


def test_cross_validate_record_against_pandapower() -> None:
    spec = generate_scenario_spec("case14", seed=12345, attempt=0)
    record = solve_scenario(
        case_name="case14",
        scenario_spec=spec,
        solver_config={"ac": {"tolerance": 1e-8, "max_iterations": 30}},
        dataset_id="pfbench_test",
        split="dev",
    )

    result = cross_validate_record(record)

    assert result["passed"] is True
    assert result["preprocess"]["base_kv_filled_bus_ids"] == list(range(1, 15))
    assert result["preprocess"]["base_kv_fill_value_kv"] == 1.0
    assert result["metrics"]["ac_bus_vm_pu"]["within_tolerance"] is True
    assert result["metrics"]["ac_branch_p_from_mw"]["within_tolerance"] is True
    assert result["metrics"]["dc_bus_va_deg"]["within_tolerance"] is True
    assert result["metrics"]["dc_branch_p_from_mw"]["within_tolerance"] is True


def test_cross_validate_record_with_outaged_transformer() -> None:
    spec = {
        "seed": 2121320162,
        "source_case": "case57",
        "solver_modes": ["ac", "dc"],
        "mutations": [
            {"op": "scale_bus_load", "bus_id": 20, "p_mult": 1.0936, "q_mult": 0.9114},
            {"op": "scale_bus_load", "bus_id": 43, "p_mult": 0.9119, "q_mult": 1.0184},
            {"op": "line_outage", "branch_id": 73, "from_bus": 45, "to_bus": 15},
            {
                "op": "set_tap_ratio",
                "branch_id": 72,
                "from_bus": 41,
                "to_bus": 11,
                "old_ratio": 0.9550000000000001,
                "new_ratio": 0.9325,
            },
        ],
        "scenario_id": "scn_case57_bb0ebea95d23",
    }
    record = solve_scenario(
        case_name="case57",
        scenario_spec=spec,
        solver_config={"ac": {"tolerance": 1e-8, "max_iterations": 30}},
        dataset_id="pfbench_test",
        split="public_test",
    )

    result = cross_validate_record(record)

    assert result["passed"] is True
    assert result["metrics"]["ac_bus_vm_pu"]["within_tolerance"] is True
    assert result["metrics"]["ac_branch_p_from_mw"]["within_tolerance"] is True
    assert result["metrics"]["dc_branch_p_from_mw"]["within_tolerance"] is True
