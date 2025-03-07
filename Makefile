SHELL=/bin/bash

.PHONY: help install dev prod clean test

GREEN=$(shell tput -Txterm setaf 2)
YELLOW=$(shell tput -Txterm setaf 3)
RED=$(shell tput -Txterm setaf 1)
BLUE=$(shell tput -Txterm setaf 6)
RESET=$(shell tput -Txterm sgr0)

OS := $(shell uname -s)

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies using Poetry"
	@echo "  make dev        - Run the project in development mode"
	@echo "  make prod       - Run the project in production mode"
	@echo "  make clean      - Remove virtual environment and cached files"
	@echo "  make test       - Run tests (if applicable)"


check_sysreq:
	@echo "$(GREEN)Installing AMI ...$(RESET)"

install:
	@echo "$(GREEN)Installing AMI ...$(RESET)"
	@poetry install

check-python:
	@echo "Checking Python version..."
	@PYTHON_VERSION=$$(python3 --version | cut -d" " -f2); \
	MAJOR_MINOR=$$(echo $$PYTHON_VERSION | cut -d. -f1,2); \
	if [ "$$(printf '%s\n' "$$MAJOR_MINOR" "$(PYTHON_REQUIRED)" | sort -V | head -n1)" != "$(PYTHON_REQUIRED)" ]; then \
		echo "Error: Python $(PYTHON_REQUIRED) or higher is required. Found: $$PYTHON_VERSION"; \
		exit 1; \
	else \
		echo "Python $$PYTHON_VERSION is compatible."; \
	fi

# Check Poetry version
check-poetry:
	@echo "Checking Poetry version..."
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "Poetry not found. Installing Poetry..."; \
		pip install poetry; \
	fi; \
	POETRY_VERSION=$$(poetry --version | cut -d" " -f3 | tr -d ')'); \
	if [ "$$(printf '%s\n' "$$POETRY_VERSION" "$(POETRY_REQUIRED)" | sort -V | head -n1)" != "$(POETRY_REQUIRED)" ]; then \
		echo "Error: Poetry $(POETRY_REQUIRED) or higher is required. Found: $$POETRY_VERSION"; \
		echo "Please update Poetry with: pip install --upgrade poetry"; \
		exit 1; \
	else \
		echo "Poetry $$POETRY_VERSION is compatible."; \
	fi

run:
	@echo "$(GREEN)Running AMI$(RESET)"
	@poetry run ami

dev:
	@echo "$(GREEN)Starting AMI in dev mode! LFG!$(RESET)"
	poetry run dev
idev:
	@echo "$(GREEN)Starting AMI in interactive dev mode! LET FUCKING GO! FULL DEV MODE!!$(RESET)"
	poetry run python -i -m ami.main --dev

clean:
	@echo "$(BLUE)Cleaning all temp files$(RESET)"
	rm -rf .pytest_cache __pycache__ *.pyc
	find . -type d -name '__pycache__' -exec rm -r {} +
	find . -type f -name '*.pyc' -exec rm -f {} +
	rm -rf dist build *.egg-info

test:
	@echo "$(YELLOW) Running tests ...$(RESET)"
	poetry run pytest

docs:
	poetry run sphinx-build -b html docs docs/_build

