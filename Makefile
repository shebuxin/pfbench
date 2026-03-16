PYTHON ?= python

.PHONY: doctor test generate report phase0 phase1

doctor:
	$(PYTHON) -m pfbench.cli doctor

test:
	pytest -q

generate:
	$(PYTHON) -m pfbench.cli generate-demo --config configs/dataset.yaml --out examples/demo_questions.jsonl

report:
	$(PYTHON) -m pfbench.cli report --dataset examples/demo_questions.jsonl

phase0: doctor generate report test

phase1: phase0
