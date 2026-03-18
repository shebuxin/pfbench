# PowerFlowBench Development Phase Plan (for Codex execution)

> Target repository: `pfbench_repo_v2`
>
> Goal: move the current repository from a “phase prototype” to a “deliverable dataset factory -> runnable benchmark -> tool-use agent evaluation platform”.
>
> Usage: **have Codex execute only one phase at a time**. Do not move to the next phase until all acceptance commands for the current phase pass.

---

## 0. Current status at a glance

Based on the current repository snapshot, `pfbench_repo_v2` already contains these core components:

- `src/pfbench/powerflow/scenario.py`
- `src/pfbench/powerflow/solver.py`
- `src/pfbench/generation/questions.py`
- `src/pfbench/generation/factory.py`
- `src/pfbench/grading/core.py`
- `src/pfbench/cli.py`
- example artifacts under `examples/` and `reports/`
- `environment.yml`

But the earlier snapshot also had an obvious issue: **README and the CLI / factory path referenced directories and modules that were missing or incomplete**. Before building outward, the repository first needed a self-consistency repair pass.

### Items that Phase 0 should verify first

These were referenced by README or imports and needed to be checked and filled in during Phase 0:

- `AGENTS.md`
- `pyproject.toml`
- `Makefile`
- `configs/dataset.yaml`
- `configs/solver.yaml`
- `schemas/question_item.schema.json`
- `schemas/scenario_record.schema.json`
- `src/pfbench/__init__.py`
- `src/pfbench/utils.py`
- `src/pfbench/io/__init__.py`
- `src/pfbench/evaluation/__init__.py`
- `src/pfbench/powerflow/cases.py`
- `tests/`

If a file actually existed but the docs were stale, Phase 0 should repair the README rather than preserve inconsistency.

---

## 1. Phases and levels

| Phase | Level | System role | Target outcome | Depends on LLM | Typical paper type |
|---|---|---|---|---|---|
| Phase 0 | L0 | Repository self-consistency and engineering baseline | installable, runnable, testable | No | engineering baseline |
| Phase 1 | L1 | Dataset Factory | full scenario/question dataset generation | No | dataset / data descriptor |
| Phase 2 | L2 | Benchmark Runner | run models and score them automatically | Yes | benchmark paper |
| Phase 3 | L3 | Agent Benchmark | evaluate tool use and planning ability | Yes | agent benchmark |
| Phase 4 (optional) | L4 | Release and paper polish | reproducible release with complete docs | Optional | submission / open source |

Recommended order: `Phase 0 -> Phase 1`, then `Phase 2 -> Phase 3`.

---

## 2. Global constraints for every phase

### 2.1 Engineering constraints

1. Use `conda` consistently.
2. Keep the default Python version at `3.11`.
3. Every new dependency must be added to `environment.yml`.
4. Every CLI feature must support `python -m pfbench.cli ...`.
5. If a console script exists, also support `pfbench ...`.
6. Every phase must end with real validation; do not stop at “code written”.
7. Keep `scenario artifact` and `question artifact` separate.
8. `gold_answer` must come only from solver truth, never from an LLM.
9. Keep random behavior deterministic through explicit seeds.
10. All JSONL / JSON outputs must align with schemas.

### 2.2 Data design constraints

1. **Keep original grid reference information.**
2. **Keep slack / PV / PQ bus partition information.**
3. **Keep the full post-mutation input state.**
4. **Keep the new post-mutation power-flow results.**
5. **Keep data and solve provenance**, at minimum: `seed`, solver config, solver version or implementation name, generation time, schema version.
6. **Do not duplicate the entire scenario inside each question; question items must reference scenario records through `scenario_id`.**
7. Keep both AC and DC results whenever possible.

### 2.3 Codex execution constraints

Principles for Codex:

- Execute only one phase at a time.
- Read this file first, then `README.md` and `AGENTS.md`.
- Emit a short execution plan of 5-10 bullets before making major changes.
- Prefer repairing the repository so it runs cleanly before adding more complexity.
- After each small module, immediately run a minimal verification command.
- If README and code disagree, make the repository self-consistent and update the docs.

---

## 3. Recommended repository shape after Phase 0

```text
pfbench_repo_v2/
├─ AGENTS.md
├─ README.md
├─ environment.yml
├─ pyproject.toml
├─ Makefile
├─ configs/
│  ├─ dataset.yaml
│  └─ solver.yaml
├─ schemas/
│  ├─ question_item.schema.json
│  └─ scenario_record.schema.json
├─ docs/
│  ├─ architecture.md
│  ├─ benchmark_spec.md
│  └─ data_provenance.md
├─ src/pfbench/
│  ├─ __init__.py
│  ├─ cli.py
│  ├─ utils.py
│  ├─ io/
│  │  └─ __init__.py
│  ├─ evaluation/
│  │  └─ __init__.py
│  ├─ powerflow/
│  │  ├─ cases.py
│  │  ├─ scenario.py
│  │  └─ solver.py
│  ├─ generation/
│  │  ├─ factory.py
│  │  └─ questions.py
│  └─ grading/
│     └─ core.py
├─ tests/
├─ datasets/
├─ examples/
├─ reports/
└─ runs/
```

---

# Phase 0 - Repository self-consistency and engineering baseline (L0)

## Goal

Repair the repository until it is **installable, runnable, testable, and doc/code consistent**.

## Why this comes first

The repository already had core solver / scenario / generation code, but the import chain and README references were not fully closed. Extending features on top of that would waste time and create confusion.

## Phase 0 task list

### 0.1 Repair files and the import chain

Verify and fill in:

- `src/pfbench/__init__.py`
- `src/pfbench/utils.py`
- `src/pfbench/io/__init__.py`
- `src/pfbench/evaluation/__init__.py`
- `src/pfbench/powerflow/cases.py`
- `configs/dataset.yaml`
- `configs/solver.yaml`
- `schemas/question_item.schema.json`
- `schemas/scenario_record.schema.json`
- `pyproject.toml`
- `AGENTS.md`
- `tests/`

### 0.2 Environment and packaging

- Keep `environment.yml` as the primary conda entrypoint.
- Configure `pyproject.toml` with:
  - package name `pfbench`
  - Python `>=3.11,<3.12`
  - console script: `pfbench = pfbench.cli:main`
- Ensure `pip install -e .` works.

### 0.3 CLI self-check loop

Make sure these commands work:

```bash
python -m pfbench.cli doctor
python -m pfbench.cli generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl
python -m pfbench.cli report --dataset examples/demo_questions.jsonl
```

And, if the console script is configured:

```bash
pfbench doctor
pfbench generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl
pfbench report --dataset examples/demo_questions.jsonl
```

### 0.4 Add tests

At minimum:

- `test_imports.py`: core modules import correctly
- `test_cli_smoke.py`: core CLI commands run
- `test_cases.py`: `case14` / `case30` load correctly
- `test_schema_validation.py`: scenario/question outputs validate against schema

### 0.5 Repair documentation

- README must not reference files that do not exist.
- README commands must be real commands that run in the current repo.
- `AGENTS.md` must clearly say:
  - use conda
  - Phase 0 / Phase 1 come first
  - gold answers come only from solver truth

## Phase 0 acceptance commands

```bash
conda env create -f environment.yml || conda env update -f environment.yml --prune
conda activate pfbench
pip install -e .
python -m pfbench.cli doctor
python -m pfbench.cli generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl
python -m pfbench.cli report --dataset examples/demo_questions.jsonl
pytest -q
```

## Phase 0 completion standard

All of the following must be true:

- import errors are gone
- `doctor / generate-demo / report` run successfully
- `pytest -q` is fully green
- README matches the actual repository
- `examples/` can generate demo question and scenario files

## Codex execution prompt for Phase 0

```text
Execute Phase 0: repair the current pfbench_repo_v2 until it is self-consistent, installable, runnable, and testable.

Requirements:
1. Audit the import chain across README, CLI, factory, solver, and scenario.
2. Fill in missing files that are referenced by the current repository snapshot.
3. Configure pyproject.toml and the console script.
4. Add minimal but real tests.
5. Run doctor / generate-demo / report / pytest and fix failures.
6. Do not add OpenAI integration and do not let an LLM generate gold truth.
7. At the end, report: which files changed, which commands passed, and what limitations remain.
```

---

# Phase 1 - Dataset Factory stabilization and expansion (L1)

## Goal

Upgrade the repository into a **deliverable power-flow benchmark dataset factory**.

## Phase 1 focus

1. fully generate `scenario records`
2. stably generate `question items`
3. complete dataset manifest / report
4. expand tests and perturbation coverage
5. make the system reproducible and reviewable at paper quality

## Phase 1 task list

### 1.1 Stabilize the Scenario Record schema

Ensure `scenario_record` includes at least:

- `scenario_id`
- `dataset_id`
- `source_case`
- `split`
- `grid_reference`
- `base_grid_snapshot`
- `scenario_spec`
- `scenario_input_state`
- `powerflow_results`
- `metadata`

Where:

#### `grid_reference`

At minimum:

- `case_name`
- `source`
- `baseMVA`
- `counts`: `num_buses / num_generators / num_branches`

#### `base_grid_snapshot`

At minimum:

- `buses`
- `generators`
- `branches`

#### `scenario_input_state`

At minimum:

- `bus_partition`
  - `slack_bus_ids`
  - `pv_bus_ids`
  - `pq_bus_ids`
- `buses`
- `generators`
- `branches`
- `bus_loads`
- `generator_setpoints`
- `branch_state`
- `totals`

#### `powerflow_results`

At minimum:

- `ac`
  - `bus_results`
  - `generator_results`
  - `branch_results`
  - `system_summary`
- `dc`
  - `bus_results`
  - `generator_results`
  - `branch_results`
  - `system_summary`

#### `metadata` / provenance

At minimum:

- `seed`
- `mutation_ops`
- `scenario_text`
- `solver_name_ac`
- `solver_name_dc`
- `solver_config_digest`
- `schema_versions`
- `generated_at`
- `dataset_version`

### 1.2 Stabilize the Question Item schema

Ensure `question_item` includes at least:

- `question_id`
- `dataset_id`
- `scenario_id`
- `source_case`
- `split`
- `query_family`
- `prompt`
- `response_schema`
- `gold_answer`
- `grader`
- `scenario_digest`
- `provenance`
- `metadata`

### 1.3 Expand question families

Extend coverage to at least:

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

### 1.4 Expand case coverage

Beyond `case14 / case30`, prioritize additional built-in cases that Codex can access immediately after installing `pandapower`, with no external download.

#### First batch (required in this phase)

- `case39`
- `case57`
- `case118`
- `case145`
- `case300`

Requirements:

1. Every new case must go through a unified case loader.
2. Do not hand-copy these case datasets into the repo; prefer `pandapower.networks.<case_name>()`.
3. For every added case, add:
   - loader test
   - scenario generation test
   - AC power-flow smoke test
   - dataset export smoke test
4. Add a configurable case whitelist in `configs/dataset.yaml`.
5. Add per-case sample counts and solve-success statistics to the report.

#### Second batch (optional but recommended)

- `case89pegase`
- `case_illinois200`

Requirements:

1. Only add these after the first batch is stable.
2. Watch runtime and reduce default sample counts if needed for larger cases.
3. Record average solve time for these cases separately.

#### Third batch (do not enable by default; only leave hooks)

- `case1354pegase`
- `case1888rte`
- `case2869pegase`
- `case3120sp`

Requirements:

1. Add registry hooks and smoke tests first.
2. Do not include them in the default demo dataset.
3. Enable them only through `--large-cases` or dedicated configs.
4. Add timeouts and failure logging for very large systems.

#### Implementation requirements

1. Build a unified case registry, for example:
   - `src/pfbench/powerflow/cases.py`
2. Expose a unified interface such as:
   - `load_case(case_name: str) -> GridModel`
3. All case names must be validated by the registry; do not scatter hard-coded case names across business logic.
4. Update README with supported case lists and tiered support.
5. Default demo generation should use:
   - `case14`
   - `case30`
   - `case39`
   - `case57`
   - `case118`

#### Acceptance standard

These commands must pass:

```bash
pytest
pfbench doctor
pfbench generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl
pfbench report --dataset examples/demo_questions.jsonl
```

And:

- the demo dataset must cover at least 5 cases
- each case must generate at least 5 scenarios
- the report must show per-case sample counts and solve success rate

### 1.5 Expand scenario perturbations

Currently available:

- load scaling
- line outage
- tap adjustment

Recommended additions:

- generator redispatch within limits
- generator outage
- shunt change
- multiple load perturbations in one scenario
- N-1 branch contingency family

### 1.5.1 Stabilize split and version strategy

To avoid leakage and version confusion:

- fix `dataset_version`
- fix `schema_version`
- fix the split assignment algorithm
- support deterministic split assignment from `scenario_id`
- avoid placing the same scenario family in both public and private test where possible

Recommended export layout:

```text
datasets/<dataset_id>/<dataset_version>/
├─ questions.jsonl
├─ scenarios.jsonl
├─ manifest.json
└─ report.md
```

### 1.6 Strengthen solver validation

Add tests for:

- rerunning the same `scenario_id` gives identical results
- AC / DC result fields are complete
- outage scenarios remain connected or are rejected correctly
- bus partition is valid
- generator / branch result counts match the snapshot element counts

### 1.7 Strengthen reporting

`report` should output at least:

- number of questions
- number of scenarios
- case coverage
- query family distribution
- split distribution
- mutation distribution
- total load / total generation ranges
- voltage range
- branch flow range

### 1.8 Generate formal example artifacts

At minimum:

- `examples/reference_scenario_record.json`
- `examples/reference_question_item.json`
- `examples/demo_scenarios.jsonl`
- `examples/demo_questions.jsonl`
- `examples/demo_manifest.json`
- `reports/pfbench_demo_report.md`

## Phase 1 acceptance commands

```bash
conda activate pfbench
pip install -e .
python -m pfbench.cli doctor
python -m pfbench.cli generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl
python -m pfbench.cli report --dataset examples/demo_questions.jsonl
pytest -q
```

If console commands are available, these must also work:

```bash
pfbench doctor
pfbench generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl
pfbench report --dataset examples/demo_questions.jsonl
```

## Phase 1 completion standard

- `scenario record` and `question item` schemas are stable
- the demo dataset is reproducible
- example files are complete
- README accurately describes the current capabilities
- at least two or more of `case14 / case30 / case57 / case118` are covered
- tests pass

## Codex execution prompt for Phase 1

```text
Execute Phase 1: upgrade the repository into a stable PowerFlow dataset factory.

Requirements:
1. Do not break the interfaces already passing in Phase 0; prefer backward-compatible changes.
2. Stabilize scenario/question schemas and enforce schema validation.
3. Expand query families, scenario mutations, case coverage, and reporting.
4. Add at least 1-2 more standard test systems.
5. Generate reference scenario/question files and demo JSONL / manifest / report artifacts.
6. Add reproducibility tests.
7. At the end, report: supported cases, supported query families, and current solver assumptions.
```

---

# Phase 2 - LLM Benchmark Runner (L2)

## Goal

Upgrade the repository from a dataset factory into a **platform that can run benchmark evaluations on large models**.

## Design principles

1. **LLMs must not generate ground truth**. They may only:
   - rewrite question wording
   - answer as the model under test
   - assist with grading only in controlled open-ended settings
2. Start with “model answers + programmatic grading”; do not jump directly to LLM judge workflows.
3. Prefer structured outputs over free-form text.
4. Keep all prediction logs for replay and auditing.

## Phase 2 task list

### 2.1 Add directories and files

Recommended additions:

```text
src/pfbench/llm/
├─ __init__.py
├─ client.py
├─ prompts.py
├─ renderer.py
├─ runner.py
└─ schemas.py

prompts/
├─ render_question.md
├─ paraphrase_question.md
├─ solve_structured.md
└─ judge_open_ended.md

runs/
└─ .gitkeep
```

### 2.2 OpenAI integration

Implement a minimal client that supports:

- reading `OPENAI_API_KEY` from the environment
- reading `configs/openai.yaml`
- selecting model name
- selecting temperature / max output tokens
- returning structured JSON

### 2.3 Question rendering and rewriting

From structured `question item` objects, generate:

- standard Chinese rendering
- standard English rendering
- concise variant
- verbose variant
- distractor-information variant

Requirements:

- **semantics must stay fixed**
- numeric content and constraints must not change
- outputs must stay compatible with `response_schema`

### 2.4 Model evaluation pipeline

Add a CLI such as:

```bash
python -m pfbench.cli eval-openai --dataset examples/demo_questions.jsonl --model gpt-5.4 --out runs/gpt54_demo_predictions.jsonl
```

Flow:

1. read dataset
2. call the model per question
3. save predictions
4. score with the existing grader
5. summarize metrics

### 2.5 Prediction log format

Each prediction record should include at least:

- `question_id`
- `scenario_id`
- `model`
- `prompt_variant`
- `raw_response`
- `parsed_response`
- `grading`
- `latency_ms`
- `timestamp`
- `request_id` when available
- `cost_fields`, including token usage when available

### 2.5.1 Robustness requirements

- limited retry on API errors
- record parse failures
- distinguish `model_error`, `parse_error`, and `grader_error`
- support resume / restart without rewriting completed predictions

### 2.6 Leaderboard / report

Add:

- overall accuracy
- per-query-family accuracy
- per-case accuracy
- per-split accuracy
- structured-output parse success rate

## Phase 2 acceptance commands

```bash
conda activate pfbench
pip install -e .
python -m pfbench.cli eval-openai --dataset examples/demo_questions.jsonl --model gpt-5.4 --out runs/gpt54_demo_predictions.jsonl
python -m pfbench.cli leaderboard --predictions runs/gpt54_demo_predictions.jsonl
pytest -q
```

## Phase 2 completion standard

- at least one OpenAI model can run end-to-end on the benchmark
- prediction logs are readable and auditable JSONL
- automatic scoring produces metrics
- question paraphrase / render variants stay compatible with gold schema
- README includes an LLM benchmark section

## Codex execution prompt for Phase 2

```text
Execute Phase 2: add an LLM benchmark runner to pfbench without breaking the solver-truth pipeline.

Requirements:
1. Use the modern OpenAI API, not an obsolete assistant workflow.
2. Prefer structured outputs over free-text parsing.
3. Start with “model answers + programmatic grading + metrics report”.
4. Keep both raw_response and parsed_response.
5. Do not let the LLM participate in gold truth generation.
6. At the end, explain: how to configure the API key, how to run evaluation, and which files are produced.
```

---

# Phase 3 - Tool-use / Agent Benchmark (L3)

## Goal

Upgrade the repository into an **agent benchmark for correct tool use and solve planning**.

## Why this is a separate phase

At this stage, the evaluation target is no longer just “is the final answer correct?” but also:

- did the model realize it needed a tool?
- did it call the tool correctly?
- were the arguments correct?
- did it make redundant or invalid calls?
- was the final answer correct?

## Phase 3 task list

### 3.1 Expose the solver as a tool protocol

Example tool schema:

```json
{
  "name": "solve_powerflow",
  "description": "Solve AC or DC power flow for a named case and scenario specification.",
  "input_schema": {
    "type": "object",
    "properties": {
      "case_name": {"type": "string"},
      "scenario_id": {"type": "string"},
      "mode": {"type": "string", "enum": ["ac", "dc"]}
    },
    "required": ["case_name", "scenario_id", "mode"],
    "additionalProperties": false
  }
}
```

### 3.2 Add agent-style question families

For example:

- “You may call the solver tool. Find the minimum-voltage bus.”
- “Compare AC and DC flow on this branch.”
- “Determine whether this scenario has a voltage violation, and explain why.”

### 3.3 Record tool-call traces

Each agent run should include at least:

- `question_id`
- `tool_calls`
- `num_tool_calls`
- `tool_arguments`
- `tool_outputs`
- `final_answer`
- `grading`

### 3.4 Define agent metrics

At minimum:

- final answer accuracy
- tool call success rate
- valid argument rate
- unnecessary tool call rate
- average calls per question
- no-tool hallucination rate

### 3.4.1 Agent runtime mode

Start with the minimal version:

- one tool: `solve_powerflow`
- single-turn questions
- 1-3 tool calls max
- no multi-agent coordination

Only after that is stable should you consider:

- multiple tools
- multi-step planning
- more open explanation questions

### 3.5 Extend reporting

Add:

- per-tool metrics
- per-query-family tool-use metrics
- failure case analysis

## Phase 3 acceptance commands

```bash
conda activate pfbench
pip install -e .
python -m pfbench.cli eval-agent --dataset examples/demo_questions.jsonl --model gpt-5.4 --out runs/gpt54_agent_predictions.jsonl
python -m pfbench.cli leaderboard --predictions runs/gpt54_agent_predictions.jsonl
pytest -q
```

## Phase 3 completion standard

- the solver can be called as a model tool
- tool-use traces are fully recorded
- the metrics include both accuracy and tool-use behavior
- at least one demo agent run is reproducible

## Codex execution prompt for Phase 3

```text
Execute Phase 3: extend pfbench into an agent benchmark that evaluates tool-use capability.

Requirements:
1. Use the existing solver as the only truth tool; do not add another black-box solver.
2. Record complete tool-call traces.
3. Distinguish between “answer correctness” and “tool-use correctness” in the metrics.
4. Build the single-tool version first.
5. At the end, provide: tool schema, agent run example, and tool-use metrics example.
```

---

# Phase 4 (optional) - Release and paper polish (L4)

## Goal

Move the project from “runnable” to **publicly releasable, paper-ready, and reproducible by others**.

## Phase 4 task list

### 4.1 Documentation

Add:

- data structure overview
- schema explanations
- definition of each query family
- definition of each mutation family
- reproducibility guide
- solver assumptions / limitations

### 4.2 Open-source readiness

- `LICENSE`
- `CITATION.cff`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- baseline result table

### 4.3 Fix experiment definitions

- fix dataset version
- fix benchmark split
- fix baseline command
- fix output schema

### 4.4 Export paper assets

Automatically generate:

- data statistics table
- case coverage table
- query family distribution table
- baseline result table
- error analysis table

## Phase 4 completion standard

- an external researcher can reproduce from README alone
- baseline results can be rerun
- code and data versions are explicit
