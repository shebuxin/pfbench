from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pfbench.cli import app
from pfbench.generation import generate_dataset_bundle
from pfbench.grading import grade_answer
from pfbench.io import read_jsonl

RUNNER = CliRunner()


def _write_small_config(path: Path) -> None:
    path.write_text(
        """
dataset:
  dataset_id: pfbench_test
  dataset_version: "0.3.0"
  generated_at: "1970-01-01T00:00:00Z"
  seed: 7
  cases:
    - case14
  num_scenarios_per_case: 1
  split_ratios:
    dev: 1.0
    public_test: 0.0
    private_test: 0.0
  query_families:
    - direct_bus_vm
    - direct_bus_va
    - argmin_bus_vm
    - argmax_bus_va_abs
    - direct_branch_p_from
    - direct_branch_q_from
    - max_branch_abs_p_from
    - max_branch_abs_q_from
    - compare_ac_dc_branch_p_from
    - is_voltage_violation_present
  export:
    jsonl: true
    parquet: false
""".strip() + "\n",
        encoding="utf-8",
    )


def test_generate_bundle_small(tmp_path: Path) -> None:
    config = tmp_path / "dataset.yaml"
    out = tmp_path / "demo_questions.jsonl"
    _write_small_config(config)
    bundle = generate_dataset_bundle(config_path=config, out_path=out)

    assert len(bundle["questions"]) == 10
    assert len(bundle["scenarios"]) == 1
    assert bundle["failed_scenarios"] == []
    scenario = bundle["scenarios"][0]
    assert "base_grid_snapshot" in scenario
    assert "scenario_input_state" in scenario
    assert "powerflow_results" in scenario
    assert "provenance" in scenario
    assert "slack_bus_ids" in scenario["scenario_input_state"]["bus_partition"]
    assert scenario["scenario_input_state"]["buses"]
    assert scenario["scenario_input_state"]["generators"]
    assert scenario["scenario_input_state"]["branches"]
    assert scenario["powerflow_results"]["ac"]["bus_results"]
    assert scenario["powerflow_results"]["dc"]["branch_results"]
    assert scenario["metadata"]["dataset_version"] == "0.3.0"

    questions = list(read_jsonl(out))
    assert len(questions) == 10
    assert all(question["evaluation_mode"] == "tool_or_structured_context_required" for question in questions)
    assert all(question["provenance"]["scenario_artifact"] == "demo_scenarios.jsonl" for question in questions)


def test_grade_answer_pass_and_fail(tmp_path: Path) -> None:
    config = tmp_path / "dataset.yaml"
    out = tmp_path / "demo_questions.jsonl"
    _write_small_config(config)
    bundle = generate_dataset_bundle(config_path=config, out_path=out)
    item = next(question for question in bundle["questions"] if question["query_family"] == "direct_bus_vm")

    passed = grade_answer(item, item["gold_answer"])
    assert passed["passed"] is True
    assert passed["score"] == 1.0

    wrong = grade_answer(item, {"bus_id": item["gold_answer"]["bus_id"], "vm_pu": 999.0})
    assert wrong["passed"] is False
    assert wrong["score"] < 1.0

    violation_item = next(
        question for question in bundle["questions"]
        if question["query_family"] == "is_voltage_violation_present"
    )
    passed_exact = grade_answer(violation_item, violation_item["gold_answer"])
    assert passed_exact["passed"] is True


def test_cli_end_to_end_small(tmp_path: Path) -> None:
    config = tmp_path / "dataset.yaml"
    out = tmp_path / "demo_questions.jsonl"
    report_path = tmp_path / "report.md"
    _write_small_config(config)

    result_generate = RUNNER.invoke(app, ["generate-demo", "--config", str(config), "--out", str(out)])
    assert result_generate.exit_code == 0, result_generate.stdout
    assert out.exists()
    assert out.with_name("demo_scenarios.jsonl").exists()
    assert out.with_name("demo_manifest.json").exists()

    result_report = RUNNER.invoke(app, ["report", "--dataset", str(out), "--out", str(report_path)])
    assert result_report.exit_code == 0, result_report.stdout
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "Scenario completeness" in content
    assert "Number of questions" in content
    assert "Scenario solve status by case" in content


def test_bundle_generation_is_deterministic(tmp_path: Path) -> None:
    config = tmp_path / "dataset.yaml"
    out = tmp_path / "demo_questions.jsonl"
    _write_small_config(config)

    bundle_a = generate_dataset_bundle(config_path=config, out_path=out)
    first_questions = out.read_text(encoding="utf-8")
    first_scenarios = out.with_name("demo_scenarios.jsonl").read_text(encoding="utf-8")
    bundle_b = generate_dataset_bundle(config_path=config, out_path=out)
    second_questions = out.read_text(encoding="utf-8")
    second_scenarios = out.with_name("demo_scenarios.jsonl").read_text(encoding="utf-8")

    assert bundle_a["questions"] == bundle_b["questions"]
    assert bundle_a["scenarios"] == bundle_b["scenarios"]
    assert bundle_a["manifest"]["dataset_version"] == bundle_b["manifest"]["dataset_version"]
    assert first_questions == second_questions
    assert first_scenarios == second_scenarios
