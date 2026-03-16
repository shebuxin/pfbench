# Quality report

## Coverage statistics

- Question items: 10600
- Solved scenarios: 1060
- Failed scenarios logged: 0
- Cases covered: case14, case30, case39, case57, case118, case145, case300
- Query families covered: direct_bus_vm, direct_bus_va, argmin_bus_vm, argmax_bus_va_abs, direct_branch_p_from, direct_branch_q_from, max_branch_abs_p_from, max_branch_abs_q_from, compare_ac_dc_branch_p_from, is_voltage_violation_present

## Split policy

- Deterministic scenario-level assignment using stable hashing with target ratios dev=70%, public_test=15%, private_test=15%.
- All questions derived from the same scenario inherit the same split.
- Stored split counts in this release:
- `dev`: 7280 questions
- `private_test`: 1740 questions
- `public_test`: 1580 questions

## Scenario rejection and failure policy

- Each scenario seed is retried with mutation regeneration up to the solver retry limit from `configs/solver.yaml`.
- Retry-exhausted scenarios are written to `failed_scenarios.jsonl` instead of being silently omitted.
- This release recorded 0 failed scenarios.

## Leakage analysis

- Question IDs unique: `True`
- Scenario IDs unique: `True`
- Questions referencing unknown scenarios: `False`
- Scenario IDs appearing in multiple question splits: 0
- Split consistency check passed: `True`
- Since split assignment is scenario-level and persisted before question expansion, this release has no intended cross-split duplication of a scenario's questions.

## Solver assumptions and caveats

- The AC solver assumes exactly one slack bus.
- Generator reactive power limits are not enforced by the current in-repo solver.
- AC results come from an in-repo Newton-Raphson polar solver; DC results come from an in-repo linear DC solver.
- Scenario records include `data_quality_flags` so inherited source-case artifacts remain visible instead of being silently normalized away.
- Voltage-violation questions exclude buses already flagged as source-case voltage-limit inconsistencies.
- Scenarios are perturbation-based benchmark cases, not operational dispatch studies.

## Mutation coverage

- `line_outage`: 493
- `scale_bus_load`: 2641
- `set_tap_ratio`: 427

## Scenario solve status by case

- `case118`: solved=150, failed=0, attempts=150
- `case14`: solved=220, failed=0, attempts=220
- `case145`: solved=60, failed=0, attempts=60
- `case30`: solved=220, failed=0, attempts=220
- `case300`: solved=30, failed=0, attempts=30
- `case39`: solved=190, failed=0, attempts=190
- `case57`: solved=190, failed=0, attempts=190

## Validation of the frozen release

- Manifest counts match files: `True`
- Scenario records validated: 1060
- Question items validated: 10600
- Gold answers validated against response schemas: 10600
- Validation digest: `47d30c89ce58d5fe`
