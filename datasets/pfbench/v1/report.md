# pfbench report

- Number of questions: 10600
- Number of scenarios: 1060
- Number of failed scenarios: 0

## Question counts by case

- case118: 1500
- case14: 2200
- case145: 600
- case30: 2200
- case300: 300
- case39: 1900
- case57: 1900

## Question counts by split

- dev: 7280
- private_test: 1740
- public_test: 1580

## Question counts by query family

- argmax_bus_va_abs: 1060
- argmin_bus_vm: 1060
- compare_ac_dc_branch_p_from: 1060
- direct_branch_p_from: 1060
- direct_branch_q_from: 1060
- direct_bus_va: 1060
- direct_bus_vm: 1060
- is_voltage_violation_present: 1060
- max_branch_abs_p_from: 1060
- max_branch_abs_q_from: 1060

## Scenario solve status by case

- case118: success=150, failed=0, success_rate=100.00%
- case14: success=220, failed=0, success_rate=100.00%
- case145: success=60, failed=0, success_rate=100.00%
- case30: success=220, failed=0, success_rate=100.00%
- case300: success=30, failed=0, success_rate=100.00%
- case39: success=190, failed=0, success_rate=100.00%
- case57: success=190, failed=0, success_rate=100.00%

## Mutation counts

- line_outage: 493
- scale_bus_load: 2641
- set_tap_ratio: 427

## Scenario metric ranges

- Total load P (MW): min=186.193040, max=291192.158000
- Total scheduled generation P (MW): min=189.210000, max=343735.100000
- Voltage magnitude (p.u.): min=-0.000000, max=1.218589
- Absolute branch P_from (MW): min=0.000000, max=9841.729512
- Absolute branch Q_from (MVAr): min=0.000000, max=3004.012358

## Scenario completeness

- has_ac_results: 1060/1060
- has_base_grid_snapshot: 1060/1060
- has_bus_partition: 1060/1060
- has_dc_results: 1060/1060
- has_mutated_branch_snapshot: 1060/1060
- has_mutated_bus_snapshot: 1060/1060
- has_mutated_generator_snapshot: 1060/1060
- has_scenario_input_state: 1060/1060

## Notes

- Scenario records include base grid snapshot, scenario input state, and AC/DC power flow results.
- Question items reference scenario_id and keep benchmark-specific fields compact.
