# Data provenance

The built-in transmission test case values in this repository come from the standard public format of the official MATPOWER case data, reorganized into repository-native data structures so benchmarks can be generated offline, reproducibly, and under test.

Currently built in:

- `case14`
- `case30`

Pandapower-backed converted cases currently supported in the environment:

- `case39`
- `case57`
- `case118`
- `case145`
- `case300`
- `case89pegase`
- `case_illinois200`

The repository keeps source URLs, data digests, and case names so they can be traced and audited later.

Before publicly releasing a dataset, you should separately review and add:

- upstream license / redistribution terms
- version numbers or commit hashes
- a provenance table in the paper
