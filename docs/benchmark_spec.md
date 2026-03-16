# Benchmark specification

## Canonical artifact

The canonical artifact in the current project is the **scenario record**.

### Why

If you only keep question / answer pairs, but do not keep:

- original case information
- bus partition
- post-mutation input state
- AC/DC results

then the benchmark is hard for a reviewer to regard as engineering-complete.

## Required scenario record fields

- `grid_reference`
- `base_grid_snapshot`
- `scenario_spec`
- `scenario_input_state`
- `powerflow_results`

## Required question item fields

- `scenario_id`
- `query_family`
- `prompt`
- `gold_answer`
- `grader`
- `response_schema`
- `scenario_digest`
- `provenance`
- `metadata`

## Current benchmark mode

Current questions default to:

- `tool_or_structured_context_required`

That means they are not pure closed-book QA; they assume access to either the scenario record or a solver tool.

## Current Phase 1 question families

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
