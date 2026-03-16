# pfbench report

- Number of questions: 1240
- Number of scenarios: 124
- Number of failed scenarios: 0

## Question counts by case

- case118: 160
- case14: 240
- case145: 120
- case30: 240
- case300: 80
- case39: 200
- case57: 200

## Question counts by split

- dev: 860
- private_test: 170
- public_test: 210

## Question counts by query family

- argmax_bus_va_abs: 124
- argmin_bus_vm: 124
- compare_ac_dc_branch_p_from: 124
- direct_branch_p_from: 124
- direct_branch_q_from: 124
- direct_bus_va: 124
- direct_bus_vm: 124
- is_voltage_violation_present: 124
- max_branch_abs_p_from: 124
- max_branch_abs_q_from: 124

## Scenario solve status by case

- case118: success=16, failed=0, success_rate=100.00%
- case14: success=24, failed=0, success_rate=100.00%
- case145: success=12, failed=0, success_rate=100.00%
- case30: success=24, failed=0, success_rate=100.00%
- case300: success=8, failed=0, success_rate=100.00%
- case39: success=20, failed=0, success_rate=100.00%
- case57: success=20, failed=0, success_rate=100.00%

## Mutation counts

- line_outage: 60
- scale_bus_load: 315
- set_tap_ratio: 53

## Scenario metric ranges

- Total load P (MW): min=187.381500, max=283190.431800
- Total scheduled generation P (MW): min=189.210000, max=343735.100000
- Voltage magnitude (p.u.): min=0.672034, max=1.211626
- Absolute branch P_from (MW): min=0.000000, max=3706.409069
- Absolute branch Q_from (MVAr): min=0.000000, max=1593.444379

## Scenario completeness

- has_ac_results: 124/124
- has_base_grid_snapshot: 124/124
- has_bus_partition: 124/124
- has_dc_results: 124/124
- has_mutated_branch_snapshot: 124/124
- has_mutated_bus_snapshot: 124/124
- has_mutated_generator_snapshot: 124/124
- has_scenario_input_state: 124/124

## Notes

- Scenario records include base grid snapshot, scenario input state, and AC/DC power flow results.
- Question items reference scenario_id and keep benchmark-specific fields compact.
