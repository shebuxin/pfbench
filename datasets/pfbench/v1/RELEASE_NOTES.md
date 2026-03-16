# Release notes for pfbench v1.0.0

## Scope

- Frozen release date encoded in artifacts: `2026-03-15T00:00:00Z`
- Solved scenarios shipped: 124
- Question items shipped: 1240
- Failed scenarios recorded for transparency: 0
- Cases included: case14, case30, case39, case57, case118, case145, case300
- Query families included: direct_bus_vm, direct_bus_va, argmin_bus_vm, argmax_bus_va_abs, direct_branch_p_from, direct_branch_q_from, max_branch_abs_p_from, max_branch_abs_q_from, compare_ac_dc_branch_p_from, is_voltage_violation_present

## Release guarantees

- File names and checksums in this directory define the frozen release boundary.
- `manifest.json`, `VALIDATION_SUMMARY.json`, and `CHECKSUMS.sha256` should be archived with the dataset.
- Scenario and question schemas are copied into `schemas/` so external users do not need the source repository to validate records.

## Validation summary

- Validation passed: `True`
- Manifest counts match stored files: `True`
- Question IDs unique: `True`
- Scenario IDs unique: `True`
- Cross-split scenario leakage detected: `0` scenarios

## Suggested citation practice

- Cite the dataset version, external repository DOI, and the accompanying data paper once available.
- Treat the code repository as a companion method artifact rather than the canonical data archive.
