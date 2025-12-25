PYTHON ?= python3
VENV ?= .venv

.PHONY: install install-dev lint format test

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

install-dev: install
	$(VENV)/bin/pip install -r requirements-dev.txt

lint:
	$(VENV)/bin/ruff check .

format:
	$(VENV)/bin/ruff format .

test:
	$(VENV)/bin/pytest
