VENV := .venv

.PHONY: bootstrap
bootstrap:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

.PHONY: run
run:
	.venv/bin/python main.py

.PHONY: test
test:
	.venv/bin/pytest

.PHONY: testw
testw:
	arelo -d 2s -t 'oasbuilder' -t 'tests' -p '**/*.py' -i '.venv' -i '.tmp' -i '.pytest_cache' -- make test

.PHONY: watch
watch:
	arelo -p 'main.py' -i '.venv' -i '.tmp' -i '.pytest_cache' -- make run

.PHONY: preview
preview:
	open --new -a "Google Chrome" --args --new-window $(PWD)/.build/index.html
