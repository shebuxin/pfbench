# pfbench

`pfbench` is a reproducible **power-flow benchmark dataset factory**.

Phase 0 and Phase 1 in this repository focus on a trusted local pipeline:

```text
base case
-> scenario mutation
-> scenario input snapshot
-> AC/DC power-flow solve
-> scenario record
-> question generation
-> programmatic grading
-> report
```

The design principle is strict:

- gold answers come only from solver truth
- scenario records keep the engineering state
- question items keep the benchmark-facing interface
- LLM work is a later phase, not the source of truth

## Phase 0 / Phase 1 status

The repository now supports:

- runnable conda environment and editable package install
- `python -m pfbench.cli ...` and `pfbench ...` CLI entrypoints
- deterministic scenario generation from seeds
- separate `scenario record` and `question item` artifacts
- AC and DC power-flow results stored in scenario records
- schema validation for scenarios and questions
- reference examples, demo bundle, manifest, and Markdown report
- reproducibility, CLI smoke, case loader, schema, and solver tests

## Supported cases

Always available built-in cases:

- `case14`
- `case30`

Extended cases available through `pandapower` conversion:

- `case39`
- `case57`
- `case118`
- `case145`
- `case300`
- `case89pegase`
- `case_illinois200`

The default demo dataset uses:

- `case14`
- `case30`
- `case39`
- `case57`
- `case118`

## Supported question families

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

## Scenario record contents

Each scenario record includes:

- `grid_reference`
- `base_grid_snapshot`
- `scenario_spec`
- `scenario_input_state`
  - bus partition
  - mutated buses / generators / branches
  - bus loads
  - generator setpoints
  - branch state
  - system totals
- `powerflow_results.ac`
  - bus / generator / branch results
  - system summary
- `powerflow_results.dc`
  - bus / generator / branch results
  - system summary
- `provenance`
- `metadata`

## Question item contents

Each question item includes:

- `dataset_id`
- `scenario_id`
- `question_id`
- `source_case`
- `split`
- `query_family`
- `evaluation_mode`
- `prompt`
- `response_schema`
- `gold_answer`
- `grader`
- `scenario_digest`
- `provenance`
- `metadata`

## Environment

Use **conda**.

```bash
conda env create -f environment.yml
conda activate pfbench
```

The environment includes an editable install, so the `pfbench` CLI is available immediately.

## Quick start

```bash
conda activate pfbench

pfbench doctor
pfbench generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl
pfbench report --dataset examples/demo_questions.jsonl
pfbench build-release --config configs/release_v1.yaml --out datasets/pfbench/v1
pytest -q
```

You can run the same commands through the module entrypoint:

```bash
python -m pfbench.cli doctor
python -m pfbench.cli generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl
python -m pfbench.cli report --dataset examples/demo_questions.jsonl
python -m pfbench.cli build-release --config configs/release_v1.yaml --out datasets/pfbench/v1
```

## Demo outputs

`generate-demo` writes:

- `examples/demo_questions.jsonl`
- `examples/demo_scenarios.jsonl`
- `examples/demo_failed_scenarios.jsonl`
- `examples/demo_manifest.json`
- `examples/reference_question_item.json`
- `examples/reference_scenario_record.json`

`report` writes:

- `reports/pfbench_demo_report.md`

## Frozen release package

The submission-ready release workflow writes an independent archive-style directory:

- `datasets/pfbench/v1/questions.jsonl`
- `datasets/pfbench/v1/scenarios.jsonl`
- `datasets/pfbench/v1/failed_scenarios.jsonl`
- `datasets/pfbench/v1/manifest.json`
- `datasets/pfbench/v1/report.md`
- `datasets/pfbench/v1/FAIR_METADATA.json`
- `datasets/pfbench/v1/VALIDATION_SUMMARY.json`
- `datasets/pfbench/v1/CHECKSUMS.sha256`
- `datasets/pfbench/v1/README.md`
- `datasets/pfbench/v1/RELEASE_NOTES.md`
- `datasets/pfbench/v1/LICENSE_AND_REDISTRIBUTION.md`
- `datasets/pfbench/v1/FIELD_DICTIONARY.md`
- `datasets/pfbench/v1/SCHEMA_DOCS.md`
- `datasets/pfbench/v1/QUALITY_REPORT.md`
- `datasets/pfbench/v1/SUBMISSION_FRAMING.md`
- copied `configs/` and `schemas/` for standalone validation

This folder is meant to be uploaded unchanged to the eventual third-party data repository.

Repository note:

- large generated `questions.jsonl`, `scenarios.jsonl`, and Parquet payloads under `datasets/pfbench/` are intentionally not tracked in Git
- generate them locally with `pfbench build-release ...` or obtain them from the external data repository after deposition
- the Git repository keeps the compact release metadata, documentation, configs, schemas, and reference items

## Default demo scale

The default config currently generates:

- 5 cases
- 5 scenarios per case
- 10 question families per scenario
- 250 question items total when all scenarios solve successfully

## Repository structure

```text
pfbench/
├─ AGENTS.md
├─ CODEX_PHASE_PLAN.md
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
└─ reports/
```

Core code layout:

- `src/pfbench/powerflow/`: case loading, scenario mutations, solver
- `src/pfbench/generation/`: scenario/question artifact generation
- `src/pfbench/grading/`: programmatic grading
- `src/pfbench/evaluation/`: reporting
- `src/pfbench/io/`: config and JSONL helpers

## Notes

- Gold answers are solver-derived only.
- Scenario generation is deterministic with respect to the configured seed.
- Extended cases rely on `pandapower` being installed in the active environment.
- The current solver assumes a single slack bus and does not enforce generator reactive power limits.
- The frozen release package is the primary archival artifact for a data-paper submission; the codebase is the supporting generation method.
- Later phases can add OpenAI runner and agent benchmark functionality without changing the Phase 1 truth pipeline.
