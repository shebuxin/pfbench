# Datasets

Frozen dataset releases live under this directory.

- `datasets/pfbench/v1/` is the first submission-ready release package.
- Treat release directories as immutable once uploaded to an external repository.
- Use `pfbench build-release --config configs/release_v1.yaml --out datasets/pfbench/v1` to regenerate locally before deposit.
- Large generated `*.jsonl` and `*.parquet` payloads are intentionally excluded from Git tracking because the archival data package should live in an external data repository rather than in the source-code host.
- The repository keeps compact release metadata and documentation under `datasets/pfbench/v1/`; rebuild the full payload locally before upload.
