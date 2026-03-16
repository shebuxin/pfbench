# Quality report

## Coverage statistics

- Question items: 1240
- Solved scenarios: 124
- Failed scenarios logged: 0
- Cases covered: case14, case30, case39, case57, case118, case145, case300
- Query families covered: direct_bus_vm, direct_bus_va, argmin_bus_vm, argmax_bus_va_abs, direct_branch_p_from, direct_branch_q_from, max_branch_abs_p_from, max_branch_abs_q_from, compare_ac_dc_branch_p_from, is_voltage_violation_present

## Split policy

- Deterministic scenario-level assignment using stable hashing with target ratios dev=70%, public_test=15%, private_test=15%.
- All questions derived from the same scenario inherit the same split.
- Stored split counts in this release:
- `dev`: 860 questions
- `private_test`: 170 questions
- `public_test`: 210 questions

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
- Scenarios are perturbation-based benchmark cases, not operational dispatch studies.

## Mutation coverage

- `line_outage`: 60
- `scale_bus_load`: 315
- `set_tap_ratio`: 53

## Scenario solve status by case

- `case118`: solved=16, failed=0, attempts=16
- `case14`: solved=24, failed=0, attempts=24
- `case145`: solved=12, failed=0, attempts=12
- `case30`: solved=24, failed=0, attempts=24
- `case300`: solved=8, failed=0, attempts=8
- `case39`: solved=20, failed=0, attempts=20
- `case57`: solved=20, failed=0, attempts=20

## Validation of the frozen release

- Manifest counts match files: `True`
- Scenario records validated: 124
- Question items validated: 1240
- Gold answers validated against response schemas: 1240
- Validation digest: `d439235c5907cc1a`
