from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from pfbench.generation import generate_dataset_bundle


def _write_config(path: Path) -> None:
    path.write_text(
        """
dataset:
  dataset_id: pfbench_schema_test
  dataset_version: "0.3.0"
  generated_at: "1970-01-01T00:00:00Z"
  seed: 11
  cases:
    - case14
  num_scenarios_per_case: 1
  split_ratios:
    dev: 1.0
  query_families:
    - direct_bus_vm
    - is_voltage_violation_present
  export:
    jsonl: true
    parquet: false
""".strip() + "\n",
        encoding="utf-8",
    )


def test_generated_records_validate_against_schemas(tmp_path: Path) -> None:
    config = tmp_path / "dataset.yaml"
    out = tmp_path / "questions.jsonl"
    _write_config(config)
    bundle = generate_dataset_bundle(config_path=config, out_path=out)

    question_schema = json.loads((Path("schemas") / "question_item.schema.json").read_text(encoding="utf-8"))
    scenario_schema = json.loads((Path("schemas") / "scenario_record.schema.json").read_text(encoding="utf-8"))

    for scenario in bundle["scenarios"]:
        jsonschema.validate(scenario, scenario_schema)

    for question in bundle["questions"]:
        jsonschema.validate(question, question_schema)
        jsonschema.validate(question["gold_answer"], question["response_schema"])
