# pfbench Scientific Writing Development Guide

## Purpose of this file

This document is a detailed internal writing brief for the current `pfbench` frozen release. It is meant to support scientific writing, especially a data-paper style manuscript, by consolidating:

- the exact release facts
- the generation and validation protocol
- the artifact inventory
- supported and unsupported claims
- writing-safe language and framing
- tables, figures, and section plans to include in a manuscript

This file is not itself the manuscript. It is a development note that should reduce ambiguity while drafting the paper and assembling the repository or data-repository metadata.

## Current authoritative release snapshot

The current frozen release lives at:

- `datasets/pfbench/v1/`

Important versioning note:

- The release directory name is `v1`.
- The internal dataset version recorded in the release artifacts is `1.1.0`.
- If this dataset is deposited externally, the title and DOI metadata should use `pfbench v1.1.0` unless you intentionally rename the folder before deposition.

Primary machine-readable release metadata:

- `datasets/pfbench/v1/manifest.json`
- `datasets/pfbench/v1/VALIDATION_SUMMARY.json`
- `datasets/pfbench/v1/FAIR_METADATA.json`
- `datasets/pfbench/v1/CHECKSUMS.sha256`

Primary human-readable release metadata:

- `datasets/pfbench/v1/README.md`
- `datasets/pfbench/v1/QUALITY_REPORT.md`
- `datasets/pfbench/v1/RELEASE_NOTES.md`
- `datasets/pfbench/v1/LICENSE_AND_REDISTRIBUTION.md`
- `datasets/pfbench/v1/FIELD_DICTIONARY.md`
- `datasets/pfbench/v1/SCHEMA_DOCS.md`
- `datasets/pfbench/v1/SUBMISSION_FRAMING.md`

## Executive summary for writing

The current release is a structured benchmark dataset for power-flow reasoning over reproducibly perturbed transmission test cases. The release contains:

- `1060` solved scenarios
- `10600` question items
- `7` benchmark cases
- `10` structured query families
- `0` failed scenarios in the released package
- explicit scenario-level provenance
- full post-mutation input state
- full stored AC and DC power-flow results
- JSONL and Parquet exports
- frozen schemas, checksums, and release documentation

This is strong enough to support a dataset-focused paper if the paper centers the released collection rather than the software implementation alone.

## Exact release facts

The following statements are directly supported by the frozen artifacts and are safe to reuse in the manuscript after stylistic editing.

### Release identity

| Item | Value |
| --- | --- |
| Dataset ID | `pfbench` |
| Dataset version | `1.1.0` |
| Release directory | `datasets/pfbench/v1/` |
| Frozen timestamp recorded in artifacts | `2026-03-16T00:00:00Z` |
| Question schema version | `0.3.0` |
| Scenario schema version | `0.3.0` |
| Solver config digest | `1e327091a96546e4` |
| Validation digest | `47d30c89ce58d5fe` |

### Dataset scale

| Item | Value |
| --- | --- |
| Number of question items | `10600` |
| Number of solved scenarios | `1060` |
| Number of failed scenarios recorded | `0` |
| Questions per scenario | `10` |
| Release package size on disk | about `233M` |

### Included benchmark cases

| Case | Solved scenarios | Question items |
| --- | ---: | ---: |
| `case14` | `220` | `2200` |
| `case30` | `220` | `2200` |
| `case39` | `190` | `1900` |
| `case57` | `190` | `1900` |
| `case118` | `150` | `1500` |
| `case145` | `60` | `600` |
| `case300` | `30` | `300` |

### Included query families

Each solved scenario yields one question per family.

| Query family | Count | Interpretation |
| --- | ---: | --- |
| `direct_bus_vm` | `1060` | retrieve AC voltage magnitude at a target bus |
| `direct_bus_va` | `1060` | retrieve AC voltage angle at a target bus |
| `argmin_bus_vm` | `1060` | identify the bus with minimum AC voltage magnitude |
| `argmax_bus_va_abs` | `1060` | identify the bus with largest absolute AC voltage angle |
| `direct_branch_p_from` | `1060` | retrieve AC from-side active branch flow |
| `direct_branch_q_from` | `1060` | retrieve AC from-side reactive branch flow |
| `max_branch_abs_p_from` | `1060` | identify the branch with largest absolute AC from-side active flow |
| `max_branch_abs_q_from` | `1060` | identify the branch with largest absolute AC from-side reactive flow |
| `compare_ac_dc_branch_p_from` | `1060` | compare AC and DC from-side active branch flow |
| `is_voltage_violation_present` | `1060` | determine whether any bus voltage violation exists |

### Split counts

The split policy is deterministic and scenario-level. All questions derived from the same scenario remain in the same split.

| Split | Question items |
| --- | ---: |
| `dev` | `7280` |
| `public_test` | `1580` |
| `private_test` | `1740` |

Target split ratios in the release config:

- `dev = 0.70`
- `public_test = 0.15`
- `private_test = 0.15`

### Mutation counts in the released scenarios

These are aggregate counts across all released scenarios.

| Mutation op | Count |
| --- | ---: |
| `scale_bus_load` | `2641` |
| `line_outage` | `493` |
| `set_tap_ratio` | `427` |

### Aggregate scenario metric ranges

These values come from `datasets/pfbench/v1/report.md`.

| Metric | Min | Max |
| --- | ---: | ---: |
| Total load P (MW) | `186.193040` | `291192.158000` |
| Total scheduled generation P (MW) | `189.210000` | `343735.100000` |
| Voltage magnitude (p.u.) | `-0.000000` | `1.218589` |
| Absolute branch P_from (MW) | `0.000000` | `9841.729512` |
| Absolute branch Q_from (MVAr) | `0.000000` | `3004.012358` |

Note for writing:

- The `-0.000000` minimum voltage magnitude is a floating-point presentation artifact. In prose, avoid making a strong physical claim from that exact printed value.

## What the dataset is

At the current stage, `pfbench` is a reproducible benchmark dataset factory whose released artifacts focus on structured power-flow tasks. The release is not just a question-answer corpus. The canonical engineering artifact is the scenario record.

This matters for the paper:

- A paper that only describes the question JSONL would undersell the actual contribution.
- The stronger contribution is the released collection of scenario records, question items, schemas, and validation artifacts.
- The codebase is a supporting generation method and reproducibility mechanism, not the primary data object.

## High-level benchmark design

The benchmark pipeline is:

1. load a standard base transmission test case
2. sample a deterministic mutation specification from an explicit seed
3. apply the mutation to create a scenario
4. solve the mutated network with AC and DC power flow
5. store the full scenario record
6. derive structured benchmark questions from solver truth
7. validate artifacts against schemas
8. write a frozen release package with checksums and release notes

The key design principle is strict separation of concerns:

- solver provides truth
- scenario record preserves engineering state
- question item provides benchmark-facing interface
- grader provides automatic evaluation

## What is stored in the release

### Benchmark data files

These are the benchmark data collections themselves:

- `datasets/pfbench/v1/questions.jsonl`
- `datasets/pfbench/v1/questions.parquet`
- `datasets/pfbench/v1/scenarios.jsonl`
- `datasets/pfbench/v1/scenarios.parquet`
- `datasets/pfbench/v1/failed_scenarios.jsonl`
- `datasets/pfbench/v1/failed_scenarios.parquet`

### Supporting release metadata

These files provide archival, validation, and reuse support:

- `datasets/pfbench/v1/manifest.json`
- `datasets/pfbench/v1/report.md`
- `datasets/pfbench/v1/reference_question_item.json`
- `datasets/pfbench/v1/reference_scenario_record.json`
- `datasets/pfbench/v1/VALIDATION_SUMMARY.json`
- `datasets/pfbench/v1/FAIR_METADATA.json`
- `datasets/pfbench/v1/CHECKSUMS.sha256`
- `datasets/pfbench/v1/README.md`
- `datasets/pfbench/v1/RELEASE_NOTES.md`
- `datasets/pfbench/v1/LICENSE_AND_REDISTRIBUTION.md`
- `datasets/pfbench/v1/FIELD_DICTIONARY.md`
- `datasets/pfbench/v1/SCHEMA_DOCS.md`
- `datasets/pfbench/v1/QUALITY_REPORT.md`
- `datasets/pfbench/v1/SUBMISSION_FRAMING.md`
- `datasets/pfbench/v1/VERSION`
- `datasets/pfbench/v1/configs/generation_config.yaml`
- `datasets/pfbench/v1/configs/solver.yaml`
- `datasets/pfbench/v1/schemas/question_item.schema.json`
- `datasets/pfbench/v1/schemas/scenario_record.schema.json`

## Data model

### Scenario record

The scenario record is the engineering-complete artifact. Each record contains:

- `dataset_id`
- `scenario_id`
- `source_case`
- `split`
- `grid_reference`
- `base_grid_snapshot`
- `scenario_spec`
- `scenario_input_state`
- `powerflow_results`
- `provenance`
- `metadata`

Important nested content in each scenario record:

- `grid_reference`
  - base-case identity
  - source library information
  - base MVA
  - counts
  - digest of source data
- `base_grid_snapshot`
  - pre-mutation buses
  - pre-mutation generators
  - pre-mutation branches
  - bus partition
- `scenario_spec`
  - seed
  - source case
  - solver modes
  - exact mutation list
- `scenario_input_state`
  - post-mutation slack/PV/PQ bus partition
  - post-mutation buses, generators, branches
  - bus loads
  - generator setpoints
  - branch state
  - totals
- `powerflow_results.ac`
  - solver name
  - bus results
  - generator results
  - branch results
  - system summary
- `powerflow_results.dc`
  - solver name
  - bus results
  - generator results
  - branch results
  - system summary

### Question item

The question item is the benchmark-facing artifact. Each item contains:

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

Interpretation:

- the scenario record stores the full engineering state
- the question item stores a compact evaluation task
- question items reference scenarios through `scenario_id`
- questions do not duplicate the entire network state

### Evaluation mode

The current release uses:

- `tool_or_structured_context_required`

Meaning:

- the benchmark is not intended as closed-book natural-language QA
- systems are expected to operate with either the provided scenario record or a structured solver-like context

This distinction is worth making explicit in the paper.

## Case sources and provenance

The current release uses:

- built-in MATPOWER-style cases reorganized into repository-native data structures for offline reproducible generation
- pandapower-backed converted larger standard cases

Built-in cases in the repository:

- `case14`
- `case30`

Pandapower-backed cases supported in the environment:

- `case39`
- `case57`
- `case118`
- `case145`
- `case300`
- `case89pegase`
- `case_illinois200`

Cases actually used in the current release:

- `case14`
- `case30`
- `case39`
- `case57`
- `case118`
- `case145`
- `case300`

For paper language, the safest claim is:

- the release is derived from standard MATPOWER-style benchmark cases and pandapower-backed network conversions

## Scenario generation protocol

The release generation logic is driven by seeded perturbation of a base transmission case.

### Determinism

All scenario generation is explicitly seeded.

Deterministic components include:

- per-scenario seed derivation
- split assignment
- bus and branch target selection inside question generation
- scenario identifiers derived from the structured mutation specification

### Mutation operations

The current release uses three perturbation classes.

#### 1. `scale_bus_load`

For selected buses with non-zero active or reactive load:

- active load is multiplied by a factor sampled uniformly in `[0.9, 1.15]`
- reactive load is multiplied by a factor sampled uniformly in `[0.9, 1.15]`
- values are rounded for stable serialization

The number of load mutations per scenario is:

- `2` or `3`, bounded by the number of buses with load

#### 2. `line_outage`

With probability `0.45`, the generator attempts to disable one active branch, subject to a connectivity check:

- only active branches are candidates
- the selected outage must preserve overall network connectivity
- if a candidate outage disconnects the network, another candidate is tried

#### 3. `set_tap_ratio`

With probability `0.5`, the generator attempts one transformer tap modification:

- only active branches with nontrivial tap ratio are candidates
- the new tap ratio is sampled by scaling the base ratio by a factor in `[0.96, 1.04]`

### Mutation summary text

Each scenario includes a human-readable summary of the applied changes in `metadata.scenario_text`, which is used by the question prompt construction.

## Solvers and numerical configuration

### AC solver

The AC solve path is an in-repo Newton-Raphson solver in polar coordinates.

Recorded solver name:

- `newton_raphson_polar`

Configured AC settings:

- tolerance: `1.0e-8`
- max iterations: `30`

### DC solver

The DC solve path is an in-repo linear DC power-flow solver.

Recorded solver name:

- `dc_power_flow`

Configured DC settings:

- enabled: `true`

### Retry policy

Scenario generation uses a retry loop when a sampled scenario does not solve successfully.

Configured retry setting:

- maximum attempts per scenario seed: `8`

The release records retry-exhausted scenarios in:

- `failed_scenarios.jsonl`

In the current release:

- `0` failed scenarios were recorded

## Exact question families and what they test

The question families mix direct retrieval, extremum identification, cross-model comparison, and simple system-state diagnosis.

### Direct retrieval families

- `direct_bus_vm`
- `direct_bus_va`
- `direct_branch_p_from`
- `direct_branch_q_from`

These test whether the evaluated system can retrieve and return specific numerical values from the solved network state.

### Extremum families

- `argmin_bus_vm`
- `argmax_bus_va_abs`
- `max_branch_abs_p_from`
- `max_branch_abs_q_from`

These require a search or aggregation step over the relevant result tables.

### Cross-model comparison family

- `compare_ac_dc_branch_p_from`

This tests whether the evaluated system can align AC and DC outputs for the same branch and return a structured comparison.

### Condition-detection family

- `is_voltage_violation_present`

This tests whether the evaluated system can compare AC bus voltage magnitudes against stored per-bus voltage limits and identify whether violations exist.

## Automatic grading

The release is designed for automatic scoring.

Supported grader categories in the current implementation include:

- `json_numeric_tolerance`
- `json_exact`
- `ranking`
- `argmax`
- `argmin`

In the current release, question items use programmatic grading backed by solver-derived `gold_answer` and explicit `response_schema`.

Important writing point:

- The release does not rely on an LLM as the source of truth.
- The release does not require an LLM judge to compute the reference label.

That is a strong methodological point for the manuscript.

## Quality control and validation

The current release supports a strong validation story for a data paper.

### Structural validation

The following checks passed for the frozen release:

- all `1060` scenario records validated against the scenario schema
- all `10600` question items validated against the question schema
- all `10600` question `gold_answer` objects validated against their per-item `response_schema`

### Identity and leakage checks

The frozen release records:

- `question_ids_unique = true`
- `scenario_ids_unique = true`
- `questions_reference_known_scenarios = true`
- `scenario_ids_in_multiple_question_splits = 0`
- `split_consistency_ok = true`

This is important for the writing:

- it supports a clean statement that no cross-split scenario leakage was detected in the frozen release

### Completeness checks

Every released scenario includes:

- base grid snapshot
- scenario input state
- bus partition
- AC results
- DC results
- mutated bus, generator, and branch snapshots

The completeness counts are `1060/1060` for all of these categories.

### Checksum verification

The release includes `CHECKSUMS.sha256`, and all files in the frozen package verified successfully against it during local validation.

### Test-suite status

At the time of preparing this guide:

- `conda run -n pfbench pytest -q` passed with `14` tests

The tests cover:

- imports
- CLI smoke behavior
- case loading
- generation pipeline behavior
- schema validation
- release-package creation

## FAIR and reuse posture

The release has a reasonably strong FAIR posture for a local frozen package.

### Findability

The release contains:

- versioning
- manifest
- file inventory
- explicit case coverage
- schema files

### Accessibility

The package is organized as a self-contained directory for upload to a third-party repository.

Current access note:

- it is a frozen local package awaiting external deposition

### Interoperability

The release provides:

- JSONL archival artifacts
- Parquet mirrors
- JSON schemas
- explicit field dictionary

### Reuse

The release includes:

- provenance
- release notes
- a license and redistribution guidance document
- intended-use and limitations notes

## Licensing and redistribution

The release documentation states:

- MATPOWER is distributed under a BSD 3-Clause license
- pandapower is distributed under a BSD 3-Clause license

The current package distributes derived benchmark artifacts rather than the full upstream source repositories.

Writing guidance:

- do not overclaim legal completeness
- describe the release as containing derived benchmark artifacts based on standard MATPOWER-style cases and pandapower-backed conversions
- preserve upstream attribution in the paper and external deposition metadata
- keep the phrase that the redistribution note is guidance rather than legal advice

## Claims you can make confidently

These are strongly supported by the current artifacts and implementation.

### Safe strong claims

- The dataset is reproducible with explicit seeding.
- Gold answers are solver-derived.
- Scenario records retain original grid reference information, base-grid snapshot, post-mutation input state, and AC/DC solve results.
- The benchmark supports automatic grading with structured schemas.
- The release is archived as a frozen package with manifest, schemas, checksums, and validation summary.
- The release contains `1060` solved scenarios and `10600` question items across `7` benchmark cases and `10` query families.
- The split assignment is deterministic and scenario-level.
- No cross-split scenario leakage was detected in the frozen release.

### Safe moderate claims

- The release is suitable as a benchmark for structured reasoning and tool-assisted evaluation over solved power-flow scenarios.
- The release is appropriate for a dataset descriptor or data-paper submission if deposited to a persistent external repository with DOI.

## Claims you should avoid or qualify

Do not present the release as something it is not.

### Claims to avoid

- Do not claim the release represents operational utility grid data.
- Do not claim the solver enforces generator reactive power limits.
- Do not claim the release covers all standard benchmark systems.
- Do not claim the benchmark is primarily about free-form natural-language answering.
- Do not claim legal review has been completed unless that review actually occurs outside this repository work.

### Claims to qualify carefully

- If you discuss physical realism, qualify that the scenarios are perturbation-based benchmark cases.
- If you discuss generalization, distinguish between benchmark-case diversity and real-world deployment.
- If you discuss robustness, note that the current release includes only the implemented mutation families.

## Core limitations to state in the manuscript

These should be stated explicitly instead of being hidden.

1. The AC and DC solvers are in-repo implementations designed for reproducible benchmark generation, not full production-grade power-system analysis suites.
2. The AC solver assumes exactly one slack bus.
3. Generator reactive power limits are not enforced.
4. The scenario family currently covers load scaling, connected line outages, and transformer tap changes; it does not yet cover broader action sets such as generator redispatch or generator outages.
5. The release is derived from standard benchmark cases rather than operational utility networks.
6. The benchmark mode assumes access to structured scenario context or tools rather than pure closed-book language answering.
7. The current package is prepared locally and still needs third-party deposition and DOI assignment for final publication workflow.

## Recommended manuscript framing

The paper should present:

- a released dataset collection of structured power-flow benchmark artifacts

The paper should not primarily present:

- a software engineering repository write-up
- a CLI tutorial
- a future roadmap for agent evaluation

### Recommended positioning sentence

Use something close to this idea in your own words:

- `pfbench` is a released collection of reproducibly generated power-flow benchmark scenarios and structured evaluation questions, with solver-derived ground truth, explicit schemas, and frozen archival metadata.

### Recommended secondary framing

Use the source repository as:

- the generation method
- the reproducibility mechanism
- the validation implementation

## Suggested manuscript outline

### 1. Introduction

Key points to cover:

- why structured benchmark datasets are needed for power-flow-related AI evaluation
- why solver-derived truth matters
- why storing scenario state matters more than question-answer pairs alone
- why reproducibility and automatic grading are central

### 2. Dataset motivation and scope

Key points:

- target tasks involve reasoning over solved power-flow scenarios
- benchmark is designed for structured outputs
- benchmark is intended for tool-assisted or structured-context evaluation
- benchmark is not an unconstrained natural-language QA corpus

### 3. Source cases and generation pipeline

Key points:

- base-case sources
- seeded perturbation protocol
- mutation families
- AC/DC solve generation
- scenario-level and question-level artifact separation

### 4. Data records and schemas

Key points:

- scenario record as canonical engineering artifact
- question item as benchmark interface
- schemas and field dictionary
- JSONL and Parquet formats

### 5. Data quality and validation

Key points:

- schema validation
- split integrity
- uniqueness checks
- completeness checks
- checksum-based release integrity
- failed-scenario logging policy

### 6. Reuse potential and intended applications

Key points:

- benchmark evaluation
- structured-output testing
- tool-use and retrieval experiments
- data descriptor and downstream benchmark slicing

### 7. Limitations

Key points:

- solver assumptions
- mutation family scope
- benchmark-case rather than operational data
- need for external persistent deposition

### 8. Access and versioning

Key points:

- frozen release package
- recommended external DOI deposition
- version and checksum practice

## Suggested tables for the paper

### Table 1. Release overview

Suggested columns:

- version
- number of scenarios
- number of questions
- number of cases
- number of query families
- number of failed scenarios
- schemas included
- formats included

### Table 2. Case coverage

Suggested columns:

- case name
- source route
- number of buses or nominal case scale if you want to compute it separately
- solved scenarios
- question items

Current counts are already available in this guide.

### Table 3. Query family taxonomy

Suggested columns:

- query family
- task type
- required result table
- response type
- grading type

### Table 4. Release validation summary

Suggested columns:

- validation check
- result
- evidence file

Suggested rows:

- scenario schema validation
- question schema validation
- gold answer validation
- unique scenario IDs
- unique question IDs
- split leakage check
- checksum verification

### Table 5. Limitations and scope boundaries

Suggested columns:

- limitation
- practical effect
- why it exists in the current release
- future work direction

## Suggested figures for the paper

### Figure 1. Pipeline overview

Suggested diagram:

- base case
- scenario mutation
- scenario input snapshot
- AC/DC solve
- scenario record
- question generation
- automatic grading
- frozen release package

### Figure 2. Data model relationship

Suggested diagram:

- one scenario record
- multiple question items referencing the same `scenario_id`
- provenance and schema validation overlay

### Figure 3. Case and question-family coverage

Suggested visual:

- heatmap or grouped bar chart showing cases on one axis and question families on the other

### Figure 4. Split composition

Suggested visual:

- scenario-level or question-level split distribution across `dev`, `public_test`, and `private_test`

## Suggested phrases and wording constraints

### Good wording patterns

- solver-derived ground truth
- structured scenario records
- reproducibly generated benchmark scenarios
- automatic grading with schema-constrained outputs
- frozen release package with checksums and manifest
- deterministic split assignment

### Wording to avoid

- intelligent dataset
- realistic grid operations benchmark without qualification
- fully validated engineering simulator
- natural-language power systems benchmark without qualification

## Reproducibility commands to cite or keep in the supplement

Environment and tests:

```bash
conda env create -f environment.yml
conda activate pfbench
pytest -q
```

Release build:

```bash
pfbench build-release --config configs/release_v1.yaml --out datasets/pfbench/v1
```

Report generation:

```bash
pfbench report --dataset datasets/pfbench/v1/questions.jsonl
```

Checksum verification:

```bash
cd datasets/pfbench/v1
sha256sum -c CHECKSUMS.sha256
```

## Concrete file citations to use while drafting

Use these repo files as the writing source of truth:

- release summary and counts: `datasets/pfbench/v1/manifest.json`
- file inventory and intended use: `datasets/pfbench/v1/README.md`
- validation and leakage checks: `datasets/pfbench/v1/VALIDATION_SUMMARY.json`
- quality and limitations: `datasets/pfbench/v1/QUALITY_REPORT.md`
- FAIR-style metadata: `datasets/pfbench/v1/FAIR_METADATA.json`
- release versioning notes: `datasets/pfbench/v1/RELEASE_NOTES.md`
- provenance and redistribution wording: `datasets/pfbench/v1/LICENSE_AND_REDISTRIBUTION.md`
- field definitions: `datasets/pfbench/v1/FIELD_DICTIONARY.md`
- schema overview: `datasets/pfbench/v1/SCHEMA_DOCS.md`
- submission emphasis: `datasets/pfbench/v1/SUBMISSION_FRAMING.md`
- architecture summary: `docs/architecture.md`
- benchmark design intent: `docs/benchmark_spec.md`
- provenance note: `docs/data_provenance.md`

## Recommended pre-submission cleanup

These are not blockers for local writing, but they should be considered before final external deposition.

1. Align the external deposited package name with the internal version `1.1.0`.
2. Add the external DOI, accession URL, and citation metadata after upload.
3. Review upstream attribution and redistribution wording one more time before public release.
4. Consider whether to expose per-case network scale metadata in the paper tables.
5. Decide whether the paper will cite the source code repository separately as companion software.

## Bottom-line interpretation for the manuscript

The strongest paper claim is not that `pfbench` is a generic power-systems software stack. The strongest claim is that `pfbench v1.1.0` is a released, reproducible, structured benchmark dataset collection for power-flow evaluation, with solver-derived labels, engineering-complete scenario records, automatic grading support, and archival release metadata.

That is the center of gravity the paper should keep.
