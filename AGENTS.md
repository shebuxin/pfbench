# AGENTS.md

This repository is used to build a **power-flow benchmark / dataset**.

## Goals

The primary goal of any automation agent working in this repository is not to have an LLM invent questions. It is to guarantee:

1. reproducible scenarios
2. verifiable solver truth
3. stable dataset schemas
4. passing CLI and tests
5. report generation

## Non-negotiable constraints

1. **Use conda consistently for environment management.**
   - Default environment name: `pfbench`
   - Dependency changes must be synced to `environment.yml`

2. **Gold answers must come only from solver outputs.**
   - Do not use an LLM as the source of truth

3. **Store scenario records separately from question items.**
   - scenarios store complete engineering information
   - questions store the minimal benchmark-facing task interface

4. **Scenario records must contain the following fields:**
   - `base_grid_snapshot`
   - `scenario_input_state`
   - `powerflow_results`
   - bus partition
   - provenance / metadata needed to reproduce the solve

5. **Every new question family must prioritize programmatic grading.**
   - exact match
   - numeric tolerance
   - ranking / argmax / argmin

6. **Any change that affects reproducibility must include tests.**

7. **If a new external case source is added, provenance must be documented clearly.**

8. **Phase 0 and Phase 1 must remain the first priority.**
   - finish engineering self-consistency first
   - finish dataset-factory stability second
   - do not jump ahead to LLM benchmark features before the local factory is solid

## Definition of done

A task is only complete when all of the following are true:

1. the code style is consistent and readable
2. the CLI commands run
3. the relevant tests pass
4. the README is updated
5. schemas / configs / examples are aligned
6. at least one openable example artifact is produced

## Priorities

From highest to lowest:

1. reproducibility
2. verifiability
3. artifact generation
4. extensibility
5. nice-but-nonessential abstractions
