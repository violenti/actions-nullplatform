.PHONY: test test-list test-plan install-hooks

install-hooks:
	pre-commit install

test:
	python3 tests/act/run.py

test-list:
	python3 tests/act/run.py --list

test-plan:
	python3 tests/act/run.py --dry-run
