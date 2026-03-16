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
