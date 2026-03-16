PYTHON ?= python

.PHONY: doctor test generate report build-release eval-openai eval-agent leaderboard phase0 phase1 phase2 phase3 phase4

doctor:
	$(PYTHON) -m pfbench.cli doctor

test:
	pytest -q

generate:
	$(PYTHON) -m pfbench.cli generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl

report:
	$(PYTHON) -m pfbench.cli report --dataset examples/demo_questions.jsonl

build-release:
	$(PYTHON) -m pfbench.cli build-release --config configs/release_v1.yaml --out datasets/pfbench/v1

eval-openai:
	$(PYTHON) -m pfbench.cli eval-openai --dataset examples/demo_questions.jsonl --out runs/demo_predictions.jsonl

eval-agent:
	$(PYTHON) -m pfbench.cli eval-agent --dataset examples/demo_questions.jsonl --out runs/demo_agent_predictions.jsonl

leaderboard:
	$(PYTHON) -m pfbench.cli leaderboard --predictions runs/demo_predictions.jsonl

phase0: doctor generate report test

phase1: phase0

phase2: phase1

phase3: phase2

phase4: phase3
