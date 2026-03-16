from __future__ import annotations

from pfbench.powerflow.cases import available_cases, load_case
from pfbench.powerflow.scenario import generate_scenario_spec


def test_supported_cases_cover_phase1_targets() -> None:
    supported = set(available_cases())
    assert {"case14", "case30", "case39", "case57", "case118"}.issubset(supported)


def test_case14_and_case30_load() -> None:
    for case_name in ["case14", "case30"]:
        case = load_case(case_name)
        assert case["case_name"] == case_name
        assert case["bus"]
        assert case["gen"]
        assert case["branch"]


def test_extended_cases_generate_scenarios() -> None:
    for case_name in ["case39", "case57", "case118"]:
        spec = generate_scenario_spec(case_name, seed=123, attempt=0)
        assert spec["source_case"] == case_name
        assert spec["scenario_id"].startswith(f"scn_{case_name}_")
