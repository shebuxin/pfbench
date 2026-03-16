# pfbench report

- Number of questions: 250
- Number of scenarios: 25
- Number of failed scenarios: 0

## Question counts by case

- case118: 50
- case14: 50
- case30: 50
- case39: 50
- case57: 50

## Question counts by split

- dev: 150
- private_test: 40
- public_test: 60

## Question counts by query family

- argmax_bus_va_abs: 25
- argmin_bus_vm: 25
- compare_ac_dc_branch_p_from: 25
- direct_branch_p_from: 25
- direct_branch_q_from: 25
- direct_bus_va: 25
- direct_bus_vm: 25
- is_voltage_violation_present: 25
- max_branch_abs_p_from: 25
- max_branch_abs_q_from: 25

## Scenario solve status by case

- case118: success=5, failed=0, success_rate=100.00%
- case14: success=5, failed=0, success_rate=100.00%
- case30: success=5, failed=0, success_rate=100.00%
- case39: success=5, failed=0, success_rate=100.00%
- case57: success=5, failed=0, success_rate=100.00%

## Mutation counts

- line_outage: 9
- scale_bus_load: 64
- set_tap_ratio: 12

## Scenario metric ranges

- Total load P (MW): min=189.029870, max=6321.532255
- Total scheduled generation P (MW): min=189.210000, max=5620.000000
- Voltage magnitude (p.u.): min=0.677408, max=1.090000
- Absolute branch P_from (MW): min=0.000000, max=824.766969
- Absolute branch Q_from (MVAr): min=0.000000, max=213.062819
- Absolute AC power-balance residual (MW): min=0.000000, max=0.000006
- Absolute DC power-balance residual (MW): min=0.000000, max=0.000000

## Scenario completeness

- has_ac_results: 25/25
- has_base_grid_snapshot: 25/25
- has_bus_partition: 25/25
- has_dc_results: 25/25
- has_mutated_branch_snapshot: 25/25
- has_mutated_bus_snapshot: 25/25
- has_mutated_generator_snapshot: 25/25
- has_scenario_input_state: 25/25

## Data quality flags

- scenarios_with_base_kv_missing: 5/25
- scenarios_with_missing_branch_ratings: 5/25
- scenarios_with_source_generator_q_limit_inconsistency: 10/25
- scenarios_with_source_voltage_limit_inconsistency: 10/25

## Notes

- Scenario records include base grid snapshot, scenario input state, and AC/DC power flow results.
- Scenario records also carry explicit data-quality flags for inherited source-case artifacts and balance residuals.
- Question items reference scenario_id and keep benchmark-specific fields compact.
