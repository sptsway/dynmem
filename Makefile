PY ?= .venv/bin/python

.PHONY: data captions stage_a stage_b report perception test costs

test:
	$(PY) -m pytest -q

data:
	$(PY) -m dynmem.stage_b.zenodo

captions:
	@echo "captions target: not implemented yet"

stage_a:
	@echo "stage_a target: not implemented yet"

stage_b:
	$(PY) -m dynmem.stage_b.run --split test --agent local_baseline --out results/stage_b_local \
		--timelines 1 2 3 --n-per-type 12 --sources gt_event pred_event --blind

costs:
	$(PY) -m dynmem.costs

report:
	$(PY) -m dynmem.report.make_figures --split test
	$(PY) -m dynmem.report.make_summary

perception:
	$(PY) -m dynmem.report.perception
