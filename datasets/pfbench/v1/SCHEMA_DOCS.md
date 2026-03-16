# Schema documentation

The release ships two primary record collections:

- `questions.jsonl`: question items governed by `schemas/question_item.schema.json`
- `scenarios.jsonl`: scenario records governed by `schemas/scenario_record.schema.json`

## Validation contract

- Every line in `questions.jsonl` must validate against the frozen question schema.
- Every line in `scenarios.jsonl` must validate against the frozen scenario schema.
- Every `gold_answer` must also validate against the per-item `response_schema` embedded in its question item.

## Versioning

- Dataset version: `1.1.0`
- Frozen schema versions copied from the source repository: `{"question_item": "0.3.0", "scenario_record": "0.3.0"}`
- Dataset version and schema version are tracked separately so the data collection can be frozen without claiming a new wire format when the schema is unchanged.

## Interoperability notes

- JSONL is the archival source of truth for line-oriented processing.
- Parquet mirrors are provided for analytical workloads.
- The scenario artifact is intentionally richer than the question artifact so benchmark consumers can choose between compact question-only evaluation and full scenario replay.
