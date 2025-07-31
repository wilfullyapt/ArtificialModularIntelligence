.PHONY: help run dev idev clean test lint docs cli

SOURCE_DIR := $(shell pwd)
ARGS ?=

UNAME := $(shell uname -s)
ifneq ($(UNAME),Linux)
	$(error This Makefile only supports Linux. Windows and MacOS are not supported.)
endif

RED    = \033[31m
GREEN  = \033[32m
YELLOW = \033[33m
BLUE   = \033[34m
PURPLE = \033[35m
CYAN   = \033[36m
WHITE  = \033[37m
RESET  = \033[0m

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
	@echo "  test         - Run all tests with coverage."
	@echo "  test-cli     - Run CLI-specific tests."
	@echo "  lint         - Run linting checks."
	@echo "  docs         - Build documentation."
	@echo "  clean        - Remove temporary files and caches."

cli:
	@echo "$(YELLOW)Building the AMI binary from source...$(RESET)"
	$(MAKE) -C cli SOURCE_DIR="$(SOURCE_DIR)"
	@echo "$(YELLOW)Installing AMI CLI binary...$(RESET)"
	mkdir -p $(HOME)/.local/bin
	cp cli/ami $(HOME)/.local/bin/ami
	@echo "$(GREEN)  --==  DONE  ==--$(RESET)"

install: cli
	@echo "Syncing UV environment..."
	uv sync
	@echo "Installation complete. Run 'ami' to use the CLI."

dev:									# `make dev ARGS="--ai --gui"`
	uv run python -m ami.dev $(ARGS)
idev:									# `make idev ARGS="--backend"`
	uv run python -i -m ami.dev $(ARGS)

test:				# Run all tests
	uv run pytest --cov=ami --cov-report=term-missing -v

test-cli:			# Run CLI tests specifically
	uv run python cli/test_cli.py

lint:				# Lint code
	uv run flake8 ami tests

docs:				# Build documentation
	uv run sphinx-build -b html docs docs/_build

clean:				# Clean up
	find . -type d -name "__pycache__" -exec rm -r {} + || true
	find . -type f -name "*.pyc" -delete || true
	rm -rf .pytest_cache .coverage *.egg-info dist build .venv
	rm -rf docs/_build
	$(MAKE) -C cli clean
