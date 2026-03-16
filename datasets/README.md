# Datasets

Generated release packages live under this directory.

- Build a frozen release locally with `pfbench build-release --config configs/release_v1.yaml --out datasets/pfbench/v1`.
- Large generated payloads are intentionally ignored by Git and should be uploaded to an external data repository instead of the source repository.
- Keep release metadata, checksums, and copied schemas together with the generated package when depositing a frozen version.
