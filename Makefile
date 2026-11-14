PY ?= .venv/bin/python

.PHONY: data captions stage_a stage_b report test costs

test:
	$(PY) -m pytest -q

data:
	@echo "data target: see dynmem/stage_a/navqa.py and dynmem/stage_b/zenodo.py"

captions:
	@echo "captions target: not implemented yet"

stage_a:
	@echo "stage_a target: not implemented yet"

stage_b:
	@echo "stage_b target: not implemented yet"

costs:
	$(PY) -m dynmem.costs

report:
	$(PY) -m dynmem.report.make_figures
