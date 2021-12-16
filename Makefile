VENV := .venv
poetry-run := poetry run

.PHONY: default
default: bootstrap

.PHONY: bootstrap
bootstrap:
	poetry install

.PHONY: run
run:
	$(poetry-run) python main.py

.PHONY: test
test:
	$(poetry-run) pytest

.PHONY: testw
testw:
	arelo -d 2s -t 'oasbuilder' -t 'tests' -p '**/*.py' -i $(VENV) -i '.tmp' -i '.pytest_cache' -- make test

.PHONY: watch
watch:
	arelo -p 'main.py' -i $(VENV) -i '.tmp' -i '.pytest_cache' -- make run

.PHONY: preview
preview:
	open --new -a "Google Chrome" --args --new-window $(PWD)/.build/index.html
