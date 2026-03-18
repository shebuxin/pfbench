# pfbench

`pfbench` is a reproducible **power-flow benchmark release and dataset factory** for structured evaluation of power-system tasks.

The repository is organized to support an IEEE Data Description style release: the primary artifact is a **frozen dataset package**, while the codebase provides the generation, validation, and packaging pipeline used to produce that artifact.

## Release Focus

The current release model is built around two linked artifacts:

- **Scenario records**: engineering-complete solved power-flow scenarios with base-case reference, mutation specification, post-mutation input state, AC/DC solver outputs, provenance, and quality flags.
- **Question items**: benchmark-facing tasks derived from scenario records, each with a prompt, response schema, solver-derived gold answer, and programmatic grading rule.

This separation is deliberate:

- gold answers come only from solver outputs
- scenario records preserve engineering state
- question items keep the evaluation interface compact
- grading is programmatic

## Current Frozen Release

The current frozen release directory is `datasets/pfbench/IEEE_Data_Description`.

Its dataset configuration remains:

- dataset identifier: `pfbench`
- dataset version: `1.1.0`
- solved scenarios: `1060`
- question items: `10600`
- failed scenarios recorded: `0`
- benchmark cases: `case14`, `case30`, `case39`, `case57`, `case118`, `case145`, `case300`
- query families: `10`
- scenario schema version: `0.5.0`
- question schema version: `0.3.0`
- approximate package size: `250 MB`

The release package is intended to be uploaded unchanged to an external data repository.

## Validation Posture

The repository now supports a stronger validation story suitable for data release:

- schema validation for scenario records and question items
- validation of each `gold_answer` against its item-specific `response_schema`
- uniqueness and split-leakage checks at release build time
- explicit scenario completeness checks
- external **pandapower cross-validation** against frozen scenario solves
- copied configs and schemas inside the frozen release for standalone verification
- checksum generation for archival integrity

The pandapower cross-validation compares our stored AC/DC results against an independently solved pandapower reconstruction of the same mutated scenario. The release path is configured so that cross-validation artifacts are first-class outputs, not an afterthought.

## Scenario Record Contents

Each scenario record includes:

- `grid_reference`
- `base_grid_snapshot`
- `scenario_spec`
- `scenario_input_state`
- `data_quality_flags`
- `powerflow_results`
- `provenance`
- `metadata`

Important retained quality annotations include:

- missing source-case `base_kv` metadata
- inherited source-case voltage-limit inconsistencies
- inherited source-case generator reactive-limit inconsistencies
- missing branch ratings
- AC/DC power-balance residuals

AC summaries also expose explicit shunt-demand and shunt-injection terms so reactive and active balance semantics are interpretable without reverse-engineering solver internals.

## Question Families

The current Phase 1 benchmark families are:

- `direct_bus_vm`
- `direct_bus_va`
- `argmin_bus_vm`
- `argmax_bus_va_abs`
- `direct_branch_p_from`
- `direct_branch_q_from`
- `max_branch_abs_p_from`
- `max_branch_abs_q_from`
- `compare_ac_dc_branch_p_from`
- `is_voltage_violation_present`

The current evaluation mode is `tool_or_structured_context_required`, meaning the benchmark is intended for systems that can inspect the scenario record or an equivalent structured context.

## Supported Cases

Always available built-in cases:

- `case14`
- `case30`

Additional cases loaded through `pandapower` conversion:

- `case39`
- `case57`
- `case118`
- `case145`
- `case300`
- `case89pegase`
- `case_illinois200`

## Quick Start

Use **conda**.

```bash
conda env create -f environment.yml
conda activate pfbench
```

Basic local workflow:

```bash
pfbench doctor
pfbench generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl
pfbench cross-validate --scenarios examples/demo_scenarios.jsonl
pfbench report --dataset examples/demo_questions.jsonl
pytest -q
```

Build the frozen release package:

```bash
pfbench build-release --config configs/release_v1.yaml --out datasets/pfbench/IEEE_Data_Description
```

Equivalent module-entrypoint commands are also supported:

```bash
python -m pfbench.cli doctor
python -m pfbench.cli generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl
python -m pfbench.cli cross-validate --scenarios examples/demo_scenarios.jsonl
python -m pfbench.cli report --dataset examples/demo_questions.jsonl
python -m pfbench.cli build-release --config configs/release_v1.yaml --out datasets/pfbench/IEEE_Data_Description
```

## Demo Artifacts

`generate-demo` writes:

- `examples/demo_questions.jsonl`
- `examples/demo_scenarios.jsonl`
- `examples/demo_failed_scenarios.jsonl`
- `examples/demo_manifest.json`
- `examples/reference_question_item.json`
- `examples/reference_scenario_record.json`

`cross-validate` writes:

- `examples/demo_cross_validation_summary.json`
- `examples/demo_cross_validation_results.jsonl`
- `examples/demo_cross_validation_report.md`

`report` writes:

- `reports/pfbench_demo_report.md`

## Frozen Release Package

The submission-oriented release workflow writes an archive-style directory:

- `datasets/pfbench/IEEE_Data_Description/questions.jsonl`
- `datasets/pfbench/IEEE_Data_Description/scenarios.jsonl`
- `datasets/pfbench/IEEE_Data_Description/failed_scenarios.jsonl`
- `datasets/pfbench/IEEE_Data_Description/questions.parquet`
- `datasets/pfbench/IEEE_Data_Description/scenarios.parquet`
- `datasets/pfbench/IEEE_Data_Description/manifest.json`
- `datasets/pfbench/IEEE_Data_Description/report.md`
- `datasets/pfbench/IEEE_Data_Description/VALIDATION_SUMMARY.json`
- `datasets/pfbench/IEEE_Data_Description/CROSS_VALIDATION_SUMMARY.json`
- `datasets/pfbench/IEEE_Data_Description/cross_validation_results.jsonl`
- `datasets/pfbench/IEEE_Data_Description/CROSS_VALIDATION_REPORT.md`
- `datasets/pfbench/IEEE_Data_Description/FAIR_METADATA.json`
- `datasets/pfbench/IEEE_Data_Description/CHECKSUMS.sha256`
- `datasets/pfbench/IEEE_Data_Description/README.md`
- `datasets/pfbench/IEEE_Data_Description/RELEASE_NOTES.md`
- `datasets/pfbench/IEEE_Data_Description/LICENSE_AND_REDISTRIBUTION.md`
- `datasets/pfbench/IEEE_Data_Description/FIELD_DICTIONARY.md`
- `datasets/pfbench/IEEE_Data_Description/SCHEMA_DOCS.md`
- `datasets/pfbench/IEEE_Data_Description/QUALITY_REPORT.md`
- `datasets/pfbench/IEEE_Data_Description/SUBMISSION_FRAMING.md`
- copied `configs/` and `schemas/` for standalone validation

Repository note:

- large generated JSONL and Parquet payloads under `datasets/pfbench/` are intentionally not tracked in Git
- the source repository is the generation method, not the long-term storage location for bulk release files
- the recommended publication path is to deposit the frozen release package in an external archive and cite that deposited version in the paper

## Repository Layout

```text
pfbench/
├─ README.md
├─ environment.yml
├─ pyproject.toml
├─ Makefile
├─ configs/
├─ docs/
├─ schemas/
├─ src/pfbench/
├─ tests/
├─ examples/
├─ reports/
└─ datasets/
```

Core code layout:

- `src/pfbench/powerflow/`: case loading, scenario mutation, AC/DC solver
- `src/pfbench/generation/`: scenario and question artifact generation
- `src/pfbench/validation/`: pandapower-based external cross-validation
- `src/pfbench/evaluation/`: reporting and leaderboard utilities
- `src/pfbench/release.py`: frozen release package builder
- `src/pfbench/io/`: YAML, JSONL, and export helpers

## Scope and Limitations

- The benchmark is derived from standard benchmark cases, not utility operational data.
- The current in-repository AC solver assumes exactly one slack bus.
- Generator reactive-power limits are not enforced by the in-repository AC solver.
- Some source-case artifacts are preserved rather than normalized away; these are exposed through `data_quality_flags`.
- `is_voltage_violation_present` excludes buses already flagged as inherited source-case voltage-limit inconsistencies.
- Extended cases depend on `pandapower` being installed in the active environment.

## Citation and Release Use

For an IEEE Data Description style submission, the intended citation object is the **frozen dataset package**, with this repository cited as the supporting generation and validation codebase.

Until external deposition is finalized, repository-local placeholders and release metadata should be treated as pre-publication material.
