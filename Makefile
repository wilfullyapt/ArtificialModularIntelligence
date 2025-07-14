.PHONY: help run dev idev clean test lint docs

SOURCE_DIR := $(shell pwd)
ARGS ?=

UNAME := $(shell uname -s)
ifneq ($(UNAME),Linux)
	$(error This Makefile only supports Linux. Windows and MacOS are not supported.)
endif

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Installation:"
	@echo "  install      - Install dependencies for the project"
	@echo ""
	@echo "Developing AMI:"
	@echo "  dev          - Run AMI in development mode."
	@echo "                 ARGS can be accepted here to control the dev run"
	@echo "                 example: make dev ARGS='--ai / --gui / --backend / --debug'"
	@echo "  idev         - Run AMI in interactive development mode."
	@echo "                 ARGS can be accepted here to control the dev run"
	@echo "                 example: make dev ARGS='--ai / --gui / --backend / --debug'"
	@echo ""
	@echo "Development functions:"
	@echo "  test         - Run tests with coverage."
	@echo "  lint         - Run linting checks."
	@echo "  docs         - Build documentation."
	@echo "  clean        - Remove temporary files and caches."

cli: cli/ami		# Compile and install the AMI cli
	cp cli/ami $(HOME)/.local/bin/ami

cli/ami: cli/main.c
	gcc -Wall -Wextra -o cli/ami cli/main.c -DSOURCE_DIR=\"$(SOURCE_DIR)\"

install: cli cli/ami
	@echo "Syncing UV environment..."
	uv sync
	@echo "Installing AMI CLI binary..."
	mkdir -p $(HOME)/.local/bin
	cp cli/ami $(HOME)/.local/bin/ami
	@echo "Installation complete. Run 'ami' to use the CLI."

dev:									# `make dev ARGS="--ai --gui"`
	uv run python -m ami.dev $(ARGS)
idev:									# `make idev ARGS="--backend"`
	uv run python -i -m ami.dev $(ARGS)

test:				# Run tests
	uv run pytest --cov=ami --cov-report=term-missing -v

lint:				# Lint code
	uv run flake8 ami tests

docs:				# Build documentation
	uv run sphinx-build -b html docs docs/_build

clean:				# Clean up
	find . -type d -name "__pycache__" -exec rm -r {} + || true
	find . -type f -name "*.pyc" -delete || true
	rm -rf .pytest_cache .coverage *.egg-info dist build .venv
	rm -rf docs/_build
	rm -f cli/ami
