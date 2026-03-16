from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from pfbench.generation.questions import QUERY_FAMILIES, build_question_item
from pfbench.io import load_yaml, write_jsonl
from pfbench.powerflow import PowerFlowError, solve_scenario
from pfbench.powerflow.scenario import generate_scenario_spec
from pfbench.utils import assign_split, repo_root, stable_hex, stable_seed


def _load_json_schema(schema_name: str) -> dict[str, Any]:
    schema_path = repo_root() / "schemas" / schema_name
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _validate(record: dict[str, Any], schema: dict[str, Any]) -> None:
    jsonschema.validate(record, schema)


def _sibling_scenarios_path(out_path: Path) -> Path:
    if out_path.stem == "questions":
        return out_path.with_name("scenarios.jsonl")
    return out_path.with_name(out_path.stem.replace("_questions", "") + "_scenarios.jsonl")


def _sibling_manifest_path(out_path: Path) -> Path:
    if out_path.stem == "questions":
        return out_path.with_name("manifest.json")
    return out_path.with_name(out_path.stem.replace("_questions", "") + "_manifest.json")


def _sibling_failed_scenarios_path(out_path: Path) -> Path:
    if out_path.stem == "questions":
        return out_path.with_name("failed_scenarios.jsonl")
    return out_path.with_name(out_path.stem.replace("_questions", "") + "_failed_scenarios.jsonl")


def generate_dataset_bundle(config_path: Path, out_path: Path) -> dict[str, Any]:
    config = load_yaml(config_path)
    solver_cfg = load_yaml(repo_root() / "configs" / "solver.yaml").get("solver", {})
    dataset_cfg = config.get("dataset", {})
    dataset_id = str(dataset_cfg.get("dataset_id", "pfbench_demo"))
    dataset_version = str(dataset_cfg.get("dataset_version", "0.1.0"))
    generated_at = str(dataset_cfg.get("generated_at", "1970-01-01T00:00:00Z"))
    base_seed = int(dataset_cfg.get("seed", 42))
    cases = list(dataset_cfg.get("cases", ["case14"]))
    num_scenarios_per_case = int(dataset_cfg.get("num_scenarios_per_case", 2))
    scenarios_per_case_cfg = {
        str(case_name): int(count)
        for case_name, count in dict(dataset_cfg.get("scenarios_per_case", {})).items()
    }
    split_ratios = dict(dataset_cfg.get("split_ratios", {"dev": 0.6, "public_test": 0.2, "private_test": 0.2}))
    query_families = list(dataset_cfg.get("query_families", QUERY_FAMILIES))
    max_attempts = int(solver_cfg.get("retry", {}).get("max_attempts", 6))
    schema_versions = {
        "question_item": "0.3.0",
        "scenario_record": "0.5.0",
    }

    scenario_schema = _load_json_schema("scenario_record.schema.json")
    question_schema = _load_json_schema("question_item.schema.json")
    scenarios_path = _sibling_scenarios_path(out_path)
    manifest_path = _sibling_manifest_path(out_path)
    failed_scenarios_path = _sibling_failed_scenarios_path(out_path)

    scenarios: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    failed_scenarios: list[dict[str, Any]] = []

    for case_name in cases:
        case_scenarios = scenarios_per_case_cfg.get(case_name, num_scenarios_per_case)
        for scenario_idx in range(case_scenarios):
            scenario_seed = stable_seed(dataset_id, base_seed, case_name, scenario_idx)
            solved_record: dict[str, Any] | None = None
            last_error: Exception | None = None
            for attempt in range(max_attempts):
                spec = generate_scenario_spec(case_name, scenario_seed, attempt=attempt)
                split = assign_split(spec["scenario_id"], split_ratios)
                try:
                    solved_record = solve_scenario(
                        case_name=case_name,
                        scenario_spec=spec,
                        solver_config=solver_cfg,
                        dataset_id=dataset_id,
                        split=split,
                        dataset_version=dataset_version,
                        generated_at=generated_at,
                        schema_versions=schema_versions,
                    )
                    break
                except PowerFlowError as exc:
                    last_error = exc
            if solved_record is None:
                failed_scenarios.append({
                    "dataset_id": dataset_id,
                    "dataset_version": dataset_version,
                    "source_case": case_name,
                    "scenario_index": scenario_idx,
                    "scenario_seed": scenario_seed,
                    "split": assign_split(f"{case_name}:{scenario_idx}:{scenario_seed}", split_ratios),
                    "attempts": max_attempts,
                    "error": str(last_error),
                    "generated_at": generated_at,
                })
                continue

            _validate(solved_record, scenario_schema)
            scenarios.append(solved_record)

            for family in query_families:
                question = build_question_item(
                    dataset_id=dataset_id,
                    scenario_record=solved_record,
                    query_family=family,
                    scenario_artifact_name=scenarios_path.name,
                )
                _validate(question, question_schema)
                jsonschema.validate(question["gold_answer"], question["response_schema"])
                questions.append(question)

    write_jsonl(out_path, questions)
    write_jsonl(scenarios_path, scenarios)
    write_jsonl(failed_scenarios_path, failed_scenarios)

    manifest = {
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "questions_path": str(out_path),
        "scenarios_path": str(scenarios_path),
        "failed_scenarios_path": str(failed_scenarios_path),
        "num_questions": len(questions),
        "num_scenarios": len(scenarios),
        "num_failed_scenarios": len(failed_scenarios),
        "cases": cases,
        "query_families": query_families,
        "schema_versions": schema_versions,
        "generated_at": generated_at,
        "solver_config_digest": stable_hex(solver_cfg, length=16),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    export_cfg = dataset_cfg.get("export", {})
    if export_cfg.get("parquet"):
        import pandas as pd

        pd.DataFrame(questions).to_parquet(out_path.with_suffix(".parquet"), index=False)
        pd.DataFrame(scenarios).to_parquet(scenarios_path.with_suffix(".parquet"), index=False)
        pd.DataFrame(failed_scenarios).to_parquet(failed_scenarios_path.with_suffix(".parquet"), index=False)

    return {
        "questions": questions,
        "scenarios": scenarios,
        "failed_scenarios": failed_scenarios,
        "manifest": manifest,
        "questions_path": out_path,
        "scenarios_path": scenarios_path,
        "failed_scenarios_path": failed_scenarios_path,
        "manifest_path": manifest_path,
    }
