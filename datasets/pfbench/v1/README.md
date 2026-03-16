# pfbench v1.1.0

This directory is the frozen dataset release package for the Phase 1 `pfbench` benchmark collection. It is intended to be uploaded unchanged to a third-party data repository.

## Release summary

- Dataset ID: `pfbench`
- Dataset version: `1.1.0`
- Freeze timestamp recorded in artifacts: `2026-03-16T00:00:00Z`
- Questions: 10600
- Solved scenarios: 1060
- Failed scenarios logged: 0
- Cases: case14, case30, case39, case57, case118, case145, case300
- Query families: direct_bus_vm, direct_bus_va, argmin_bus_vm, argmax_bus_va_abs, direct_branch_p_from, direct_branch_q_from, max_branch_abs_p_from, max_branch_abs_q_from, compare_ac_dc_branch_p_from, is_voltage_violation_present
- Split policy: deterministic hash-based assignment at scenario level with target ratios dev=70%, public_test=15%, private_test=15%
- Validation status: `validation_passed=True`

## Intended use

- Evaluate structured reasoning, tool use, and retrieval over solved power-flow scenarios.
- Benchmark systems that can read scenario records and return JSON matching the provided response schema.
- Support data-paper release, offline benchmarking, and reproducible downstream slicing by case, split, and query family.

## Not intended for

- Replacing production grid studies or operational planning tools.
- Training a generative model to infer unconstrained grid physics from text alone.
- Claims about generator reactive limit handling, contingency screening, or market realism beyond the frozen scenario definitions.

## Access instructions

1. Upload this directory as-is to the chosen data repository.
2. Preserve file names, checksums, and directory structure.
3. After deposit, update the repository landing page or manuscript with the persistent DOI/URL assigned by the host platform.
4. Cite the release version and the external repository record, not just the source code repository.

## File inventory

- `questions.jsonl`: Question item collection for benchmark evaluation.
- `questions.parquet`: Columnar export of the question item collection.
- `scenarios.jsonl`: Full scenario records with mutated network state and AC/DC results.
- `scenarios.parquet`: Columnar export of the scenario record collection.
- `failed_scenarios.jsonl`: Retry-exhausted scenarios kept for diagnostics and transparency.
- `failed_scenarios.parquet`: Columnar export of the failed scenario log.
- `manifest.json`: Release manifest with counts, paths, schema versions, and solver configuration digest.
- `report.md`: Human-readable summary report with coverage counts and metric ranges.
- `reference_question_item.json`: One frozen question record for quick inspection.
- `reference_scenario_record.json`: One frozen scenario record for quick inspection.
- `VALIDATION_SUMMARY.json`: Structured validation results for the frozen release.
- `FAIR_METADATA.json`: Release-level metadata focused on findability, accessibility, interoperability, and reuse.
- `README.md`: Dataset card and access guide for the release package.
- `RELEASE_NOTES.md`: Release-specific notes for version tracking and downstream repositories.
- `LICENSE_AND_REDISTRIBUTION.md`: Redistribution and attribution guidance for derived case data.
- `FIELD_DICTIONARY.md`: Field-level descriptions for question and scenario artifacts.
- `SCHEMA_DOCS.md`: Schema overview for release consumers.
- `QUALITY_REPORT.md`: Data quality, validation, and known-limitations summary.
- `SUBMISSION_FRAMING.md`: Paper-positioning notes that keep the dataset release as the primary artifact.
- `VERSION`: Plain-text release version.
- `configs/generation_config.yaml`: Exact generation config used to build the frozen release.
- `configs/solver.yaml`: Exact solver config used to build the frozen release.
- `schemas/question_item.schema.json`: Frozen question schema for release consumers.
- `schemas/scenario_record.schema.json`: Frozen scenario schema for release consumers.
- `CHECKSUMS.sha256`: SHA-256 checksums for every shipped file in the release package.

## Coverage by case

- `case118`: 1500 questions, 150 solved scenarios
- `case14`: 2200 questions, 220 solved scenarios
- `case145`: 600 questions, 60 solved scenarios
- `case30`: 2200 questions, 220 solved scenarios
- `case300`: 300 questions, 30 solved scenarios
- `case39`: 1900 questions, 190 solved scenarios
- `case57`: 1900 questions, 190 solved scenarios

## Coverage by query family

- `argmax_bus_va_abs`: 1060 questions
- `argmin_bus_vm`: 1060 questions
- `compare_ac_dc_branch_p_from`: 1060 questions
- `direct_branch_p_from`: 1060 questions
- `direct_branch_q_from`: 1060 questions
- `direct_bus_va`: 1060 questions
- `direct_bus_vm`: 1060 questions
- `is_voltage_violation_present`: 1060 questions
- `max_branch_abs_p_from`: 1060 questions
- `max_branch_abs_q_from`: 1060 questions

## Caveats

- Gold answers come only from the in-repo solvers and stored scenario records.
- The AC solver assumes exactly one slack bus and does not enforce generator reactive power limits.
- Scenario records preserve source-case fidelity and explicitly flag inherited metadata inconsistencies such as missing nominal voltages or pre-existing limit violations.
- Failed scenarios are preserved instead of silently dropped, but the current default release recorded zero failed scenarios.
- The code repository is a supporting generation artifact; the dataset collection in this directory is the primary archival object for a data-paper submission.
