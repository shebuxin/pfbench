from __future__ import annotations

from pfbench.powerflow.cases import load_case
from pfbench.powerflow.scenario import generate_scenario_spec
from pfbench.powerflow.solver import solve_scenario


def test_ac_dc_solver_on_case14() -> None:
    case_name = "case14"
    spec = generate_scenario_spec(case_name, seed=12345, attempt=0)
    record = solve_scenario(
        case_name=case_name,
        scenario_spec=spec,
        solver_config={"ac": {"tolerance": 1e-8, "max_iterations": 30}},
        dataset_id="pfbench_test",
        split="dev",
    )
    assert record["powerflow_results"]["ac"]["converged"] is True
    assert record["powerflow_results"]["dc"]["converged"] is True
    assert record["scenario_input_state"]["bus_partition"]["slack_bus_ids"] == [1]
    assert len(record["powerflow_results"]["ac"]["bus_results"]) == 14
    assert "vm_init_pu" not in record["base_grid_snapshot"]["buses"][0]
    assert "va_init_deg" not in record["base_grid_snapshot"]["buses"][0]
    assert "base_kv_kv" not in record["base_grid_snapshot"]["buses"][0]
    assert record["base_grid_snapshot"]["buses"][0]["base_kv"] is None
    assert record["base_grid_snapshot"]["buses"][0]["base_kv_is_missing"] is True
    assert record["base_grid_snapshot"]["generators"][0]["q_limit_violated"] is True
    assert record["grid_reference"]["source_url"] == "https://raw.githubusercontent.com/MATPOWER/matpower/8.1/data/case14.m"
    assert record["provenance"]["schema_versions"]["scenario_record"] == "0.5.0"

    flags = record["data_quality_flags"]
    assert flags["base_kv_missing_bus_ids"] == list(range(1, 15))
    assert flags["source_voltage_limit_inconsistency_bus_ids"] == [6, 7, 8]
    assert flags["source_generator_q_limit_inconsistency_gen_ids"] == [1]
    assert flags["missing_branch_rating_branch_ids"] == list(range(1, 21))

    ac_summary = record["powerflow_results"]["ac"]["system_summary"]
    assert abs(ac_summary["power_balance_residual_q_mvar"]) < 1e-4
    assert ac_summary["total_shunt_q_injection_mvar"] > 0.0
    assert record["powerflow_results"]["ac"]["bus_results"][0]["shunt_q_injection_mvar"] is not None

    dc_summary = record["powerflow_results"]["dc"]["system_summary"]
    assert abs(dc_summary["power_balance_residual_p_mw"]) < 1e-6
    assert abs(dc_summary["net_bus_injection_p_mw"] - dc_summary["total_loss_p_mw"]) < 1e-6
    assert record["powerflow_results"]["dc"]["bus_results"][0]["shunt_q_injection_mvar"] is None
