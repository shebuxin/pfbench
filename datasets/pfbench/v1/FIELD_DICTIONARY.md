# Field dictionary

## Question item top-level fields

- `dataset_id`: Dataset family identifier shared across all question items in the release.
- `scenario_id`: Stable pointer to the parent scenario record.
- `question_id`: Stable question identifier derived from scenario and query family.
- `source_case`: Base network case name before perturbation.
- `split`: Deterministic evaluation split assigned at scenario level.
- `query_family`: Question template family used to derive the prompt and gold answer.
- `evaluation_mode`: Benchmark contract. Phase 1 expects tool use or structured context, not free-form guessing.
- `prompt`: Natural-language instruction shown to the evaluated system.
- `response_schema`: JSON schema that valid model outputs must satisfy.
- `gold_answer`: Solver-derived reference answer for the question.
- `grader`: Programmatic grading configuration for exact or tolerance-based scoring.
- `scenario_digest`: Compact summary of the parent scenario state for benchmark consumers.
- `provenance`: Question-level lineage including the scenario artifact name and dataset version.
- `metadata`: Benchmark-facing metadata such as target element identifiers and solver mode.

## Scenario record top-level fields

- `dataset_id`: Dataset family identifier shared across the release.
- `scenario_id`: Stable scenario identifier derived from case, seed, and mutations.
- `source_case`: Base network case used before perturbation.
- `split`: Deterministic split assigned before question expansion.
- `grid_reference`: Reference metadata for the original network, including counts and a base-grid digest.
- `base_grid_snapshot`: Original network state before mutations are applied.
- `scenario_spec`: Canonical mutation specification including seed and solver modes.
- `scenario_input_state`: Full post-mutation network input state used by the solvers.
- `data_quality_flags`: Scenario-level quality annotations for inherited source-case artifacts and solver balance residuals.
- `powerflow_results`: AC and DC power-flow outputs for the mutated network.
- `provenance`: Scenario-level lineage including schema versions and solver configuration digest.
- `metadata`: Operational metadata such as mutation names, scenario text, and generation timestamp.

## Frequently used nested fields

- `scenario_input_state.bus_partition`: Slack/PV/PQ bus partition after mutation, preserved explicitly for reproducibility.
- `scenario_input_state.bus_loads`: Per-bus aggregated active and reactive load values after mutation.
- `scenario_input_state.generator_setpoints`: Generator dispatch and voltage setpoints entering the solve.
- `scenario_input_state.branch_state`: Per-branch topology state and tap/phase-shift parameters entering the solve.
- `scenario_input_state.totals`: Scenario-level system totals such as total load, scheduled generation, and active branch count.
- `data_quality_flags`: Inherited source-case issues and per-scenario power-balance residuals recorded for downstream filtering.
- `powerflow_results.ac.bus_results`: AC bus voltage and injection results.
- `powerflow_results.ac.generator_results`: AC generator injection results.
- `powerflow_results.ac.branch_results`: AC branch from/to-side flow results.
- `powerflow_results.dc.branch_results`: DC branch flow results used in AC/DC comparison questions.
- `powerflow_results.ac.system_summary`: Scenario-level AC convergence and balance summary.
- `powerflow_results.dc.system_summary`: Scenario-level DC convergence and balance summary.

## Query family dictionary

- `argmax_bus_va_abs`: Identify the bus with largest absolute AC voltage angle.
- `argmin_bus_vm`: Identify the bus with minimum AC voltage magnitude.
- `compare_ac_dc_branch_p_from`: Compare AC and DC from-side active branch flow for the same active branch.
- `direct_branch_p_from`: Direct retrieval of AC from-side active branch flow.
- `direct_branch_q_from`: Direct retrieval of AC from-side reactive branch flow.
- `direct_bus_va`: Direct retrieval of AC bus voltage angle.
- `direct_bus_vm`: Direct retrieval of AC bus voltage magnitude.
- `is_voltage_violation_present`: Detect whether any AC bus voltage limit violations are present after excluding inherited source-case limit inconsistencies.
- `max_branch_abs_p_from`: Identify the branch with largest absolute AC from-side active flow.
- `max_branch_abs_q_from`: Identify the branch with largest absolute AC from-side reactive flow.
