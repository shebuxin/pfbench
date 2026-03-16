# Architecture

In phase-1, `pfbench` is split into four layers:

## 1. Case layer

Built-in MATPOWER-style transmission test cases plus pandapower-backed conversion for larger standard cases.

## 2. Scenario layer

Turn a base case into a reproducible scenario:

- load scaling
- connected line outage
- transformer tap adjustment

## 3. Solver layer

Run the following on each scenario:

- AC Newton-Raphson power flow
- DC power flow

And export:

- bus results
- generator results
- branch results
- system summary

## 4. Benchmark layer

Extract structured questions from solver truth:

- direct numeric
- direct angle / flow values
- argmin
- argmax
- AC/DC comparison
- voltage violation detection

The outputs are split into:

- `*_scenarios.jsonl`
- `*_questions.jsonl`
- `*_manifest.json`
