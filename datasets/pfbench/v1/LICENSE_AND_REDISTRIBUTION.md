# License and redistribution guidance

## What this release contains

- Derived scenario records generated from MATPOWER-style network data and pandapower-backed converted cases.
- Derived question items whose gold answers come from solver outputs on those frozen scenarios.
- Supporting schemas, manifests, reports, and documentation generated within this repository.

## Upstream source projects

- MATPOWER is distributed under the BSD 3-Clause license.
- pandapower is distributed under the BSD 3-Clause license.
- This release uses built-in MATPOWER-style test cases and pandapower network conversions as upstream engineering references.

## Redistribution note

- This package distributes derived benchmark artifacts, not a copy of the full MATPOWER or pandapower source repositories.
- Users who separately redistribute upstream case files, source code, or modified network libraries should review the original upstream license text and attribution requirements.
- Before public deposition, keep the upstream project names in the release metadata and manuscript so provenance remains visible.

## Recommended attribution in the paper and repository record

- State that the benchmark scenarios are derived from MATPOWER-style cases and pandapower-backed converted networks.
- Cite the MATPOWER project and the pandapower project in the manuscript reference list.
- Preserve `grid_reference.source_library` and `grid_reference.source_url` fields in downstream repackaging.

## Limitation

- This document clarifies dataset provenance and redistribution posture, but it is not legal advice.
