# Pandapower cross-validation report

- Validation engine: `pandapower 3.2.1`
- Scenarios validated: 25
- Passed all tolerances: 25
- Failed one or more tolerances: 0
- All passed: `True`
- Scenarios requiring temporary base_kV fill for pandapower conversion: 5

## Metric summary

- `ac_branch_p_from_mw`: max_abs_diff=4.99911e-07, tolerance=0.001, within_tolerance=25/25, worst_scenario_id=`scn_case39_8180351a5f5d`
- `ac_branch_p_to_mw`: max_abs_diff=4.99125e-07, tolerance=0.001, within_tolerance=25/25, worst_scenario_id=`scn_case57_bb0ebea95d23`
- `ac_branch_q_from_mvar`: max_abs_diff=4.99785e-07, tolerance=0.01, within_tolerance=25/25, worst_scenario_id=`scn_case39_68424c80198c`
- `ac_branch_q_to_mvar`: max_abs_diff=4.99997e-07, tolerance=0.01, within_tolerance=25/25, worst_scenario_id=`scn_case30_97d865e19197`
- `ac_bus_pg_mw`: max_abs_diff=4.82202e-07, tolerance=0.0001, within_tolerance=25/25, worst_scenario_id=`scn_case39_fb586811a2c9`
- `ac_bus_qg_mvar`: max_abs_diff=4.98782e-07, tolerance=0.01, within_tolerance=25/25, worst_scenario_id=`scn_case39_6cc8bfdf6e1b`
- `ac_bus_va_deg`: max_abs_diff=4.99288e-07, tolerance=0.01, within_tolerance=25/25, worst_scenario_id=`scn_case30_37c235ef723d`
- `ac_bus_vm_pu`: max_abs_diff=4.99112e-07, tolerance=0.0001, within_tolerance=25/25, worst_scenario_id=`scn_case118_37ef47f8b820`
- `dc_branch_p_from_mw`: max_abs_diff=4.99996e-07, tolerance=0.001, within_tolerance=25/25, worst_scenario_id=`scn_case57_67cce90c6c73`
- `dc_branch_p_to_mw`: max_abs_diff=4.99996e-07, tolerance=0.001, within_tolerance=25/25, worst_scenario_id=`scn_case57_67cce90c6c73`
- `dc_bus_pg_mw`: max_abs_diff=2.89901e-12, tolerance=0.0001, within_tolerance=25/25, worst_scenario_id=`scn_case118_8f30eb1d5c18`
- `dc_bus_va_deg`: max_abs_diff=4.9981e-07, tolerance=0.01, within_tolerance=25/25, worst_scenario_id=`scn_case39_df265c5e01fc`

## Failed scenarios

- None
