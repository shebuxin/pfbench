# Datasets

Generated release packages live under this directory.

- The current IEEE Data Description style release directory is `datasets/pfbench/IEEE_Data_Description`.
- Build that frozen release locally with `pfbench build-release --config configs/release_v1.yaml --out datasets/pfbench/IEEE_Data_Description`.
- Large generated payloads are intentionally ignored by Git and should be uploaded to an external data repository instead of the source repository.
- Keep release metadata, checksums, copied configs, and copied schemas together with the generated package when depositing a frozen version.
