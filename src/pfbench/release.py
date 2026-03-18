from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import jsonschema

from pfbench.evaluation import write_report
from pfbench.generation import generate_dataset_bundle
from pfbench.io import load_yaml, read_jsonl
from pfbench.utils import repo_root, stable_hex
from pfbench.validation import cross_validate_scenarios

_QUESTION_FIELDS = [
    ("dataset_id", "Dataset family identifier shared across all question items in the release."),
    ("scenario_id", "Stable pointer to the parent scenario record."),
    ("question_id", "Stable question identifier derived from scenario and query family."),
    ("source_case", "Base network case name before perturbation."),
    ("split", "Deterministic evaluation split assigned at scenario level."),
    ("query_family", "Question template family used to derive the prompt and gold answer."),
    ("evaluation_mode", "Benchmark contract. Phase 1 expects tool use or structured context, not free-form guessing."),
    ("prompt", "Natural-language instruction shown to the evaluated system."),
    ("response_schema", "JSON schema that valid model outputs must satisfy."),
    ("gold_answer", "Solver-derived reference answer for the question."),
    ("grader", "Programmatic grading configuration for exact or tolerance-based scoring."),
    ("scenario_digest", "Compact summary of the parent scenario state for benchmark consumers."),
    ("provenance", "Question-level lineage including the scenario artifact name and dataset version."),
    ("metadata", "Benchmark-facing metadata such as target element identifiers and solver mode."),
]

_SCENARIO_FIELDS = [
    ("dataset_id", "Dataset family identifier shared across the release."),
    ("scenario_id", "Stable scenario identifier derived from case, seed, and mutations."),
    ("source_case", "Base network case used before perturbation."),
    ("split", "Deterministic split assigned before question expansion."),
    ("grid_reference", "Reference metadata for the original network, including counts and a base-grid digest."),
    ("base_grid_snapshot", "Original network state before mutations are applied."),
    ("scenario_spec", "Canonical mutation specification including seed and solver modes."),
    ("scenario_input_state", "Full post-mutation network input state used by the solvers."),
    ("data_quality_flags", "Scenario-level quality annotations for inherited source-case artifacts and solver balance residuals."),
    ("powerflow_results", "AC and DC power-flow outputs for the mutated network."),
    ("provenance", "Scenario-level lineage including schema versions and solver configuration digest."),
    ("metadata", "Operational metadata such as mutation names, scenario text, and generation timestamp."),
]

_CORE_NESTED_FIELDS = [
    ("scenario_input_state.bus_partition", "Slack/PV/PQ bus partition after mutation, preserved explicitly for reproducibility."),
    ("scenario_input_state.bus_loads", "Per-bus aggregated active and reactive load values after mutation."),
    ("scenario_input_state.generator_setpoints", "Generator dispatch and voltage setpoints entering the solve."),
    ("scenario_input_state.branch_state", "Per-branch topology state and tap/phase-shift parameters entering the solve."),
    ("scenario_input_state.totals", "Scenario-level system totals such as total load, scheduled generation, and active branch count."),
    ("data_quality_flags", "Inherited source-case issues and per-scenario power-balance residuals recorded for downstream filtering."),
    ("powerflow_results.ac.bus_results", "AC bus voltage and injection results."),
    ("powerflow_results.ac.generator_results", "AC generator injection results."),
    ("powerflow_results.ac.branch_results", "AC branch from/to-side flow results."),
    ("powerflow_results.dc.branch_results", "DC branch flow results used in AC/DC comparison questions."),
    ("powerflow_results.ac.system_summary", "Scenario-level AC convergence and balance summary."),
    ("powerflow_results.dc.system_summary", "Scenario-level DC convergence and balance summary."),
]

_QUERY_FAMILY_DESCRIPTIONS = {
    "direct_bus_vm": "Direct retrieval of AC bus voltage magnitude.",
    "direct_bus_va": "Direct retrieval of AC bus voltage angle.",
    "argmin_bus_vm": "Identify the bus with minimum AC voltage magnitude.",
    "argmax_bus_va_abs": "Identify the bus with largest absolute AC voltage angle.",
    "direct_branch_p_from": "Direct retrieval of AC from-side active branch flow.",
    "direct_branch_q_from": "Direct retrieval of AC from-side reactive branch flow.",
    "max_branch_abs_p_from": "Identify the branch with largest absolute AC from-side active flow.",
    "max_branch_abs_q_from": "Identify the branch with largest absolute AC from-side reactive flow.",
    "compare_ac_dc_branch_p_from": "Compare AC and DC from-side active branch flow for the same active branch.",
    "is_voltage_violation_present": "Detect whether any AC bus voltage limit violations are present after excluding inherited source-case limit inconsistencies.",
}

_DATASET_FILES = {
    "questions.jsonl": "Question item collection for benchmark evaluation.",
    "questions.parquet": "Columnar export of the question item collection.",
    "scenarios.jsonl": "Full scenario records with mutated network state and AC/DC results.",
    "scenarios.parquet": "Columnar export of the scenario record collection.",
    "failed_scenarios.jsonl": "Retry-exhausted scenarios kept for diagnostics and transparency.",
    "failed_scenarios.parquet": "Columnar export of the failed scenario log.",
    "manifest.json": "Release manifest with counts, paths, schema versions, and solver configuration digest.",
    "report.md": "Human-readable summary report with coverage counts and metric ranges.",
    "reference_question_item.json": "One frozen question record for quick inspection.",
    "reference_scenario_record.json": "One frozen scenario record for quick inspection.",
    "VALIDATION_SUMMARY.json": "Structured validation results for the frozen release.",
    "FAIR_METADATA.json": "Release-level metadata focused on findability, accessibility, interoperability, and reuse.",
    "README.md": "Dataset card and access guide for the release package.",
    "RELEASE_NOTES.md": "Release-specific notes for version tracking and downstream repositories.",
    "LICENSE_AND_REDISTRIBUTION.md": "Redistribution and attribution guidance for derived case data.",
    "FIELD_DICTIONARY.md": "Field-level descriptions for question and scenario artifacts.",
    "SCHEMA_DOCS.md": "Schema overview for release consumers.",
    "QUALITY_REPORT.md": "Data quality, validation, and known-limitations summary.",
    "CROSS_VALIDATION_SUMMARY.json": "Aggregate pandapower cross-validation summary for the frozen scenarios.",
    "cross_validation_results.jsonl": "Per-scenario pandapower cross-validation metrics.",
    "CROSS_VALIDATION_REPORT.md": "Human-readable pandapower cross-validation report.",
    "SUBMISSION_FRAMING.md": "Paper-positioning notes that keep the dataset release as the primary artifact.",
    "VERSION": "Plain-text release version.",
    "configs/generation_config.yaml": "Exact generation config used to build the frozen release.",
    "configs/solver.yaml": "Exact solver config used to build the frozen release.",
    "configs/validation.yaml": "Exact pandapower cross-validation config used to validate the frozen release.",
    "schemas/question_item.schema.json": "Frozen question schema for release consumers.",
    "schemas/scenario_record.schema.json": "Frozen scenario schema for release consumers.",
    "CHECKSUMS.sha256": "SHA-256 checksums for every shipped file in the release package.",
}


def _load_json_schema(schema_name: str) -> dict[str, Any]:
    return json.loads((repo_root() / "schemas" / schema_name).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _copy_text_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_inventory(release_dir: Path) -> list[dict[str, Any]]:
    files = []
    for path in sorted(p for p in release_dir.rglob("*") if p.is_file() and p.name != "CHECKSUMS.sha256"):
        rel = path.relative_to(release_dir).as_posix()
        files.append({
            "path": rel,
            "description": _DATASET_FILES.get(rel, "Release artifact."),
            "size_bytes": path.stat().st_size,
            "format": path.suffix.lstrip(".") or "text",
        })
    return files


def _validate_release(
    questions_path: Path,
    scenarios_path: Path,
    failed_scenarios_path: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    question_schema = _load_json_schema("question_item.schema.json")
    scenario_schema = _load_json_schema("scenario_record.schema.json")

    questions = list(read_jsonl(questions_path))
    scenarios = list(read_jsonl(scenarios_path))
    failed_scenarios = list(read_jsonl(failed_scenarios_path))

    for scenario in scenarios:
        jsonschema.validate(scenario, scenario_schema)

    for question in questions:
        jsonschema.validate(question, question_schema)
        jsonschema.validate(question["gold_answer"], question["response_schema"])

    question_ids = [row["question_id"] for row in questions]
    scenario_ids = [row["scenario_id"] for row in scenarios]
    scenario_split_map = {row["scenario_id"]: row["split"] for row in scenarios}
    scenario_question_counts: dict[str, int] = {}
    split_assignments: dict[str, set[str]] = {}
    scenario_artifacts = sorted({row["provenance"]["scenario_artifact"] for row in questions})

    for question in questions:
        scenario_id = question["scenario_id"]
        scenario_question_counts[scenario_id] = scenario_question_counts.get(scenario_id, 0) + 1
        split_assignments.setdefault(scenario_id, set()).add(question["split"])

    multi_split_scenarios = sorted(
        scenario_id for scenario_id, splits in split_assignments.items() if len(splits) > 1
    )
    split_mismatches = sorted(
        scenario_id
        for scenario_id, splits in split_assignments.items()
        if scenario_split_map.get(scenario_id) not in splits or len(splits) != 1
    )
    missing_question_scenarios = sorted({row["scenario_id"] for row in questions} - set(scenario_ids))

    return {
        "validation_passed": True,
        "dataset_id": manifest["dataset_id"],
        "dataset_version": manifest["dataset_version"],
        "num_questions_validated": len(questions),
        "num_scenarios_validated": len(scenarios),
        "num_failed_scenarios_recorded": len(failed_scenarios),
        "num_gold_answers_validated": len(questions),
        "question_ids_unique": len(question_ids) == len(set(question_ids)),
        "scenario_ids_unique": len(scenario_ids) == len(set(scenario_ids)),
        "questions_reference_known_scenarios": not missing_question_scenarios,
        "scenario_ids_in_multiple_question_splits": len(multi_split_scenarios),
        "split_consistency_ok": not split_mismatches and not multi_split_scenarios,
        "scenario_artifacts_declared_by_questions": scenario_artifacts,
        "questions_per_scenario": {
            "min": min(scenario_question_counts.values()) if scenario_question_counts else 0,
            "max": max(scenario_question_counts.values()) if scenario_question_counts else 0,
        },
        "missing_question_scenarios": missing_question_scenarios,
        "split_mismatches": split_mismatches,
        "manifest_counts_match_files": (
            manifest["num_questions"] == len(questions)
            and manifest["num_scenarios"] == len(scenarios)
            and manifest["num_failed_scenarios"] == len(failed_scenarios)
        ),
        "validation_digest": stable_hex(
            manifest["dataset_id"],
            manifest["dataset_version"],
            len(questions),
            len(scenarios),
            len(failed_scenarios),
            scenario_artifacts,
            length=16,
        ),
    }


def _split_ratio_text(split_ratios: dict[str, Any]) -> str:
    parts = []
    total = sum(float(value) for value in split_ratios.values())
    for key, value in split_ratios.items():
        frac = 0.0 if total == 0 else float(value) / total
        parts.append(f"{key}={frac:.0%}")
    return ", ".join(parts)


def _release_readme(
    manifest: dict[str, Any],
    summary: dict[str, Any],
    validation: dict[str, Any],
    cross_validation: dict[str, Any],
    dataset_cfg: dict[str, Any],
    release_dir: Path,
) -> str:
    case_lines = "\n".join(
        f"- `{case}`: {count} questions, {summary['scenario_success_by_case'].get(case, 0)} solved scenarios"
        for case, count in sorted(summary["by_case"].items())
    )
    query_lines = "\n".join(
        f"- `{family}`: {count} questions"
        for family, count in sorted(summary["by_query_family"].items())
    )
    file_lines = "\n".join(
        f"- `{path}`: {description}"
        for path, description in _DATASET_FILES.items()
        if path in {"CHECKSUMS.sha256", "README.md", "FAIR_METADATA.json"} or (release_dir / path).exists()
    )
    split_text = _split_ratio_text(dict(dataset_cfg.get("split_ratios", {})))
    return (
        f"# pfbench v{manifest['dataset_version']}\n\n"
        "This directory is the frozen dataset release package for the Phase 1 `pfbench` benchmark collection. "
        "It is intended to be uploaded unchanged to a third-party data repository.\n\n"
        "## Release summary\n\n"
        f"- Dataset ID: `{manifest['dataset_id']}`\n"
        f"- Dataset version: `{manifest['dataset_version']}`\n"
        f"- Freeze timestamp recorded in artifacts: `{manifest['generated_at']}`\n"
        f"- Questions: {summary['num_questions']}\n"
        f"- Solved scenarios: {summary['num_scenarios']}\n"
        f"- Failed scenarios logged: {summary['num_failed_scenarios']}\n"
        f"- Cases: {', '.join(manifest['cases'])}\n"
        f"- Query families: {', '.join(manifest['query_families'])}\n"
        f"- Split policy: deterministic hash-based assignment at scenario level with target ratios {split_text}\n"
        f"- Validation status: `validation_passed={validation['validation_passed']}`\n\n"
        f"- External pandapower cross-validation: `all_passed={cross_validation['all_passed']}` "
        f"across {cross_validation['num_scenarios']} scenarios\n\n"
        "## Intended use\n\n"
        "- Evaluate structured reasoning, tool use, and retrieval over solved power-flow scenarios.\n"
        "- Benchmark systems that can read scenario records and return JSON matching the provided response schema.\n"
        "- Support data-paper release, offline benchmarking, and reproducible downstream slicing by case, split, and query family.\n\n"
        "## Not intended for\n\n"
        "- Replacing production grid studies or operational planning tools.\n"
        "- Training a generative model to infer unconstrained grid physics from text alone.\n"
        "- Claims about generator reactive limit handling, contingency screening, or market realism beyond the frozen scenario definitions.\n\n"
        "## Access instructions\n\n"
        "1. Upload this directory as-is to the chosen data repository.\n"
        "2. Preserve file names, checksums, and directory structure.\n"
        "3. After deposit, update the repository landing page or manuscript with the persistent DOI/URL assigned by the host platform.\n"
        "4. Cite the release version and the external repository record, not just the source code repository.\n\n"
        "## File inventory\n\n"
        f"{file_lines}\n\n"
        "## Coverage by case\n\n"
        f"{case_lines}\n\n"
        "## Coverage by query family\n\n"
        f"{query_lines}\n\n"
        "## Caveats\n\n"
        "- Gold answers come only from the in-repo solvers and stored scenario records.\n"
        "- The AC solver assumes exactly one slack bus and does not enforce generator reactive power limits.\n"
        "- Release validation includes a separate pandapower cross-validation pass over the frozen scenarios.\n"
        "- Scenario records preserve source-case fidelity and explicitly flag inherited metadata inconsistencies such as missing nominal voltages or pre-existing limit violations.\n"
        "- Failed scenarios are preserved instead of silently dropped, but the current default release recorded zero failed scenarios.\n"
        "- The code repository is a supporting generation artifact; the dataset collection in this directory is the primary archival object for a data-paper submission.\n"
    )


def _release_notes(
    manifest: dict[str, Any],
    summary: dict[str, Any],
    validation: dict[str, Any],
) -> str:
    return (
        f"# Release notes for pfbench v{manifest['dataset_version']}\n\n"
        "## Scope\n\n"
        f"- Frozen release date encoded in artifacts: `{manifest['generated_at']}`\n"
        f"- Solved scenarios shipped: {summary['num_scenarios']}\n"
        f"- Question items shipped: {summary['num_questions']}\n"
        f"- Failed scenarios recorded for transparency: {summary['num_failed_scenarios']}\n"
        f"- Cases included: {', '.join(manifest['cases'])}\n"
        f"- Query families included: {', '.join(manifest['query_families'])}\n\n"
        "## Release guarantees\n\n"
        "- File names and checksums in this directory define the frozen release boundary.\n"
        "- `manifest.json`, `VALIDATION_SUMMARY.json`, and `CHECKSUMS.sha256` should be archived with the dataset.\n"
        "- Scenario and question schemas are copied into `schemas/` so external users do not need the source repository to validate records.\n\n"
        "## Validation summary\n\n"
        f"- Validation passed: `{validation['validation_passed']}`\n"
        f"- Manifest counts match stored files: `{validation['manifest_counts_match_files']}`\n"
        f"- Question IDs unique: `{validation['question_ids_unique']}`\n"
        f"- Scenario IDs unique: `{validation['scenario_ids_unique']}`\n"
        f"- Cross-split scenario leakage detected: `{validation['scenario_ids_in_multiple_question_splits']}` scenarios\n\n"
        "## Suggested citation practice\n\n"
        "- Cite the dataset version, external repository DOI, and the accompanying data paper once available.\n"
        "- Treat the code repository as a companion method artifact rather than the canonical data archive.\n"
    )


def _license_and_redistribution() -> str:
    return (
        "# License and redistribution guidance\n\n"
        "## What this release contains\n\n"
        "- Derived scenario records generated from MATPOWER-style network data and pandapower-backed converted cases.\n"
        "- Derived question items whose gold answers come from solver outputs on those frozen scenarios.\n"
        "- Supporting schemas, manifests, reports, and documentation generated within this repository.\n\n"
        "## Upstream source projects\n\n"
        "- MATPOWER is distributed under the BSD 3-Clause license.\n"
        "- pandapower is distributed under the BSD 3-Clause license.\n"
        "- This release uses built-in MATPOWER-style test cases and pandapower network conversions as upstream engineering references.\n\n"
        "## Redistribution note\n\n"
        "- This package distributes derived benchmark artifacts, not a copy of the full MATPOWER or pandapower source repositories.\n"
        "- Users who separately redistribute upstream case files, source code, or modified network libraries should review the original upstream license text and attribution requirements.\n"
        "- Before public deposition, keep the upstream project names in the release metadata and manuscript so provenance remains visible.\n\n"
        "## Recommended attribution in the paper and repository record\n\n"
        "- State that the benchmark scenarios are derived from MATPOWER-style cases and pandapower-backed converted networks.\n"
        "- Cite the MATPOWER project and the pandapower project in the manuscript reference list.\n"
        "- Preserve `grid_reference.source_library` and `grid_reference.source_url` fields in downstream repackaging.\n\n"
        "## Limitation\n\n"
        "- This document clarifies dataset provenance and redistribution posture, but it is not legal advice.\n"
    )


def _field_dictionary() -> str:
    def _lines(items: list[tuple[str, str]]) -> str:
        return "\n".join(f"- `{field}`: {description}" for field, description in items)

    query_family_lines = "\n".join(
        f"- `{name}`: {description}"
        for name, description in sorted(_QUERY_FAMILY_DESCRIPTIONS.items())
    )
    return (
        "# Field dictionary\n\n"
        "## Question item top-level fields\n\n"
        f"{_lines(_QUESTION_FIELDS)}\n\n"
        "## Scenario record top-level fields\n\n"
        f"{_lines(_SCENARIO_FIELDS)}\n\n"
        "## Frequently used nested fields\n\n"
        f"{_lines(_CORE_NESTED_FIELDS)}\n\n"
        "## Query family dictionary\n\n"
        f"{query_family_lines}\n"
    )


def _schema_docs(manifest: dict[str, Any]) -> str:
    return (
        "# Schema documentation\n\n"
        "The release ships two primary record collections:\n\n"
        "- `questions.jsonl`: question items governed by `schemas/question_item.schema.json`\n"
        "- `scenarios.jsonl`: scenario records governed by `schemas/scenario_record.schema.json`\n\n"
        "## Validation contract\n\n"
        "- Every line in `questions.jsonl` must validate against the frozen question schema.\n"
        "- Every line in `scenarios.jsonl` must validate against the frozen scenario schema.\n"
        "- Every `gold_answer` must also validate against the per-item `response_schema` embedded in its question item.\n\n"
        "## Versioning\n\n"
        f"- Dataset version: `{manifest['dataset_version']}`\n"
        f"- Frozen schema versions copied from the source repository: `{json.dumps(manifest['schema_versions'], ensure_ascii=False)}`\n"
        "- Dataset version and schema version are tracked separately so the data collection can be frozen without claiming a new wire format when the schema is unchanged.\n\n"
        "## Interoperability notes\n\n"
        "- JSONL is the archival source of truth for line-oriented processing.\n"
        "- Parquet mirrors are provided for analytical workloads.\n"
        "- The scenario artifact is intentionally richer than the question artifact so benchmark consumers can choose between compact question-only evaluation and full scenario replay.\n"
    )


def _quality_report(
    manifest: dict[str, Any],
    summary: dict[str, Any],
    validation: dict[str, Any],
    cross_validation: dict[str, Any],
    dataset_cfg: dict[str, Any],
) -> str:
    mutation_lines = "\n".join(
        f"- `{mutation}`: {count}"
        for mutation, count in sorted(summary["by_mutation"].items())
    ) or "- None recorded."
    split_lines = "\n".join(
        f"- `{split}`: {count} questions"
        for split, count in sorted(summary["by_split"].items())
    )
    case_success_lines = "\n".join(
        f"- `{case}`: solved={summary['scenario_success_by_case'].get(case, 0)}, failed={summary['scenario_failure_by_case'].get(case, 0)}, attempts={summary['scenario_attempts_by_case'].get(case, 0)}"
        for case in sorted(summary["scenario_attempts_by_case"])
    )
    return (
        "# Quality report\n\n"
        "## Coverage statistics\n\n"
        f"- Question items: {summary['num_questions']}\n"
        f"- Solved scenarios: {summary['num_scenarios']}\n"
        f"- Failed scenarios logged: {summary['num_failed_scenarios']}\n"
        f"- Cases covered: {', '.join(manifest['cases'])}\n"
        f"- Query families covered: {', '.join(manifest['query_families'])}\n\n"
        "## Split policy\n\n"
        f"- Deterministic scenario-level assignment using stable hashing with target ratios {_split_ratio_text(dict(dataset_cfg.get('split_ratios', {})))}.\n"
        "- All questions derived from the same scenario inherit the same split.\n"
        f"- Stored split counts in this release:\n{split_lines}\n\n"
        "## Scenario rejection and failure policy\n\n"
        "- Each scenario seed is retried with mutation regeneration up to the solver retry limit from `configs/solver.yaml`.\n"
        "- Retry-exhausted scenarios are written to `failed_scenarios.jsonl` instead of being silently omitted.\n"
        f"- This release recorded {summary['num_failed_scenarios']} failed scenarios.\n\n"
        "## Leakage analysis\n\n"
        f"- Question IDs unique: `{validation['question_ids_unique']}`\n"
        f"- Scenario IDs unique: `{validation['scenario_ids_unique']}`\n"
        f"- Questions referencing unknown scenarios: `{not validation['questions_reference_known_scenarios']}`\n"
        f"- Scenario IDs appearing in multiple question splits: {validation['scenario_ids_in_multiple_question_splits']}\n"
        f"- Split consistency check passed: `{validation['split_consistency_ok']}`\n"
        "- Since split assignment is scenario-level and persisted before question expansion, this release has no intended cross-split duplication of a scenario's questions.\n\n"
        "## Solver assumptions and caveats\n\n"
        "- The AC solver assumes exactly one slack bus.\n"
        "- Generator reactive power limits are not enforced by the current in-repo solver.\n"
        "- AC results come from an in-repo Newton-Raphson polar solver; DC results come from an in-repo linear DC solver.\n"
        "- Scenario records include `data_quality_flags` so inherited source-case artifacts remain visible instead of being silently normalized away.\n"
        "- Voltage-violation questions exclude buses already flagged as source-case voltage-limit inconsistencies.\n"
        "- Scenarios are perturbation-based benchmark cases, not operational dispatch studies.\n\n"
        "## Mutation coverage\n\n"
        f"{mutation_lines}\n\n"
        "## Scenario solve status by case\n\n"
        f"{case_success_lines}\n\n"
        "## Validation of the frozen release\n\n"
        f"- Manifest counts match files: `{validation['manifest_counts_match_files']}`\n"
        f"- Scenario records validated: {validation['num_scenarios_validated']}\n"
        f"- Question items validated: {validation['num_questions_validated']}\n"
        f"- Gold answers validated against response schemas: {validation['num_gold_answers_validated']}\n"
        f"- Validation digest: `{validation['validation_digest']}`\n\n"
        "## External pandapower cross-validation\n\n"
        f"- Cross-validation passed for all scenarios: `{cross_validation['all_passed']}`\n"
        f"- Scenarios cross-validated: {cross_validation['num_scenarios']}\n"
        f"- Failed scenarios under tolerance checks: {cross_validation['num_failed']}\n"
        f"- Scenarios requiring temporary base_kV fill before pandapower conversion: {cross_validation['num_scenarios_with_base_kv_fill']}\n"
    )


def _submission_framing(manifest: dict[str, Any], summary: dict[str, Any]) -> str:
    return (
        "# Submission framing notes\n\n"
        "## Recommended paper positioning\n\n"
        "- Present `pfbench` as a released dataset collection of solved, structured power-flow benchmark artifacts.\n"
        "- Treat the source repository and factory code as the supporting method used to create and validate the release.\n"
        "- Keep the archival focus on the frozen package in this directory and the external repository record that will host it.\n\n"
        "## Evidence the paper can center\n\n"
        f"- Frozen release size: {summary['num_scenarios']} solved scenarios and {summary['num_questions']} question items.\n"
        f"- Coverage across {len(manifest['cases'])} network cases and {len(manifest['query_families'])} structured query families.\n"
        "- Explicit scenario-level provenance, full post-mutation network state, and AC/DC power-flow results.\n"
        "- Schema validation, checksums, release manifest, and transparent failed-scenario logging.\n\n"
        "## Suggested manuscript emphasis\n\n"
        "- Motivation for structured power-flow benchmark datasets.\n"
        "- Source case selection and perturbation protocol.\n"
        "- File inventory, schemas, and intended reuse patterns.\n"
        "- Quality control: validation, split policy, leakage controls, and limitations.\n"
        "- Access instructions pointing to the deposited release package and DOI.\n\n"
        "## What should remain secondary\n\n"
        "- Internal code organization of the factory.\n"
        "- CLI ergonomics.\n"
        "- Future evaluation extensions that are not part of the frozen dataset release.\n"
    )


def _fair_metadata(
    manifest: dict[str, Any],
    summary: dict[str, Any],
    validation: dict[str, Any],
    cross_validation: dict[str, Any],
    dataset_cfg: dict[str, Any],
    release_dir: Path,
) -> dict[str, Any]:
    return {
        "title": f"pfbench v{manifest['dataset_version']}",
        "dataset_id": manifest["dataset_id"],
        "version": manifest["dataset_version"],
        "release_status": "frozen_local_package",
        "release_timestamp": manifest["generated_at"],
        "description": (
            "Structured power-flow benchmark release containing full scenario records, "
            "question items, schemas, validation summaries, and release documentation."
        ),
        "subjects": ["power systems", "benchmark datasets", "power flow", "structured evaluation"],
        "language": "en",
        "format": ["jsonl", "parquet", "json", "markdown", "yaml", "text"],
        "access": {
            "current_location": ".",
            "upload_required": True,
            "access_instructions": (
                "Upload this directory unchanged to the target repository and then add the assigned DOI or URL "
                "to the manuscript and project README."
            ),
        },
        "interoperability": {
            "schemas_path": "schemas/",
            "question_schema": "schemas/question_item.schema.json",
            "scenario_schema": "schemas/scenario_record.schema.json",
            "parquet_exports_included": True,
        },
        "reuse": {
            "intended_use": [
                "offline benchmark evaluation",
                "structured-output tool-use evaluation",
                "dataset descriptor publication",
            ],
            "limitations": [
                "single-slack-bus solver assumption",
                "reactive power limits not enforced",
                "derived from benchmark cases rather than operational utility data",
            ],
            "license_note": "See LICENSE_AND_REDISTRIBUTION.md for upstream attribution and redistribution guidance.",
        },
        "coverage": {
            "cases": manifest["cases"],
            "num_scenarios": summary["num_scenarios"],
            "num_questions": summary["num_questions"],
            "query_families": manifest["query_families"],
            "split_ratios_target": dict(dataset_cfg.get("split_ratios", {})),
            "split_counts_observed": summary["by_split"],
        },
        "quality_control": {
            "validation_passed": validation["validation_passed"],
            "manifest_counts_match_files": validation["manifest_counts_match_files"],
            "question_ids_unique": validation["question_ids_unique"],
            "scenario_ids_unique": validation["scenario_ids_unique"],
            "scenario_split_leakage_count": validation["scenario_ids_in_multiple_question_splits"],
            "pandapower_cross_validation_all_passed": cross_validation["all_passed"],
            "pandapower_cross_validation_failed_count": cross_validation["num_failed"],
        },
        "files": _file_inventory(release_dir),
    }


def _write_checksums(release_dir: Path) -> Path:
    checksum_path = release_dir / "CHECKSUMS.sha256"
    lines = []
    for path in sorted(p for p in release_dir.rglob("*") if p.is_file() and p.name != checksum_path.name):
        lines.append(f"{_sha256(path)}  {path.relative_to(release_dir).as_posix()}")
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksum_path


def build_release_package(config_path: Path, release_dir: Path) -> dict[str, Any]:
    """Build a frozen dataset release package in a self-contained directory."""

    release_dir.mkdir(parents=True, exist_ok=True)
    (release_dir / "configs").mkdir(parents=True, exist_ok=True)
    (release_dir / "schemas").mkdir(parents=True, exist_ok=True)

    questions_path = release_dir / "questions.jsonl"
    bundle = generate_dataset_bundle(config_path=config_path, out_path=questions_path)
    manifest = dict(bundle["manifest"])
    manifest.update({
        "package_root": ".",
        "questions_path": "questions.jsonl",
        "scenarios_path": "scenarios.jsonl",
        "failed_scenarios_path": "failed_scenarios.jsonl",
        "report_path": "report.md",
        "validation_summary_path": "VALIDATION_SUMMARY.json",
        "cross_validation_summary_path": "CROSS_VALIDATION_SUMMARY.json",
        "cross_validation_details_path": "cross_validation_results.jsonl",
        "cross_validation_report_path": "CROSS_VALIDATION_REPORT.md",
        "fair_metadata_path": "FAIR_METADATA.json",
        "checksums_path": "CHECKSUMS.sha256",
    })
    _write_json(release_dir / "manifest.json", manifest)
    bundle["manifest"] = manifest

    if bundle["questions"]:
        _write_json(release_dir / "reference_question_item.json", bundle["questions"][0])
    if bundle["scenarios"]:
        _write_json(release_dir / "reference_scenario_record.json", bundle["scenarios"][0])

    summary, report_path = write_report(
        dataset_path=questions_path,
        report_path=release_dir / "report.md",
    )

    _copy_text_file(config_path, release_dir / "configs" / "generation_config.yaml")
    _copy_text_file(repo_root() / "configs" / "solver.yaml", release_dir / "configs" / "solver.yaml")
    _copy_text_file(repo_root() / "configs" / "validation.yaml", release_dir / "configs" / "validation.yaml")
    _copy_text_file(repo_root() / "schemas" / "question_item.schema.json", release_dir / "schemas" / "question_item.schema.json")
    _copy_text_file(repo_root() / "schemas" / "scenario_record.schema.json", release_dir / "schemas" / "scenario_record.schema.json")

    dataset_cfg = load_yaml(config_path).get("dataset", {})
    validation = _validate_release(
        questions_path=questions_path,
        scenarios_path=release_dir / "scenarios.jsonl",
        failed_scenarios_path=release_dir / "failed_scenarios.jsonl",
        manifest=manifest,
    )
    _write_json(release_dir / "VALIDATION_SUMMARY.json", validation)
    cross_validation, _ = cross_validate_scenarios(
        scenarios_path=release_dir / "scenarios.jsonl",
        config_path=repo_root() / "configs" / "validation.yaml",
        summary_path=release_dir / "CROSS_VALIDATION_SUMMARY.json",
        details_path=release_dir / "cross_validation_results.jsonl",
        report_path=release_dir / "CROSS_VALIDATION_REPORT.md",
    )
    if not cross_validation["all_passed"]:
        raise RuntimeError(
            "Pandapower cross-validation failed for one or more scenarios. "
            "Inspect CROSS_VALIDATION_SUMMARY.json and cross_validation_results.jsonl."
        )

    (release_dir / "RELEASE_NOTES.md").write_text(
        _release_notes(manifest=manifest, summary=summary, validation=validation),
        encoding="utf-8",
    )
    (release_dir / "LICENSE_AND_REDISTRIBUTION.md").write_text(
        _license_and_redistribution(),
        encoding="utf-8",
    )
    (release_dir / "FIELD_DICTIONARY.md").write_text(_field_dictionary(), encoding="utf-8")
    (release_dir / "SCHEMA_DOCS.md").write_text(_schema_docs(manifest=manifest), encoding="utf-8")
    (release_dir / "QUALITY_REPORT.md").write_text(
        _quality_report(
            manifest=manifest,
            summary=summary,
            validation=validation,
            cross_validation=cross_validation,
            dataset_cfg=dataset_cfg,
        ),
        encoding="utf-8",
    )
    (release_dir / "SUBMISSION_FRAMING.md").write_text(
        _submission_framing(manifest=manifest, summary=summary),
        encoding="utf-8",
    )
    (release_dir / "VERSION").write_text(f"{manifest['dataset_version']}\n", encoding="utf-8")
    (release_dir / "README.md").write_text(
        _release_readme(
            manifest=manifest,
            summary=summary,
            validation=validation,
            cross_validation=cross_validation,
            dataset_cfg=dataset_cfg,
            release_dir=release_dir,
        ),
        encoding="utf-8",
    )

    fair_metadata = _fair_metadata(
        manifest=manifest,
        summary=summary,
        validation=validation,
        cross_validation=cross_validation,
        dataset_cfg=dataset_cfg,
        release_dir=release_dir,
    )
    _write_json(release_dir / "FAIR_METADATA.json", fair_metadata)
    fair_metadata = _fair_metadata(
        manifest=manifest,
        summary=summary,
        validation=validation,
        cross_validation=cross_validation,
        dataset_cfg=dataset_cfg,
        release_dir=release_dir,
    )
    _write_json(release_dir / "FAIR_METADATA.json", fair_metadata)

    checksum_path = _write_checksums(release_dir)

    return {
        "bundle": bundle,
        "manifest": manifest,
        "summary": summary,
        "validation": validation,
        "cross_validation": cross_validation,
        "questions_path": questions_path,
        "report_path": report_path,
        "checksum_path": checksum_path,
        "release_dir": release_dir,
    }
