.PHONY: help run dev idev clean test lint docs

ARGS ?=

# Check for Linux
UNAME := $(shell uname -s)
ifneq ($(UNAME),Linux)
	$(error This Makefile only supports Linux. Windows and MacOS are not supported.)
endif

# Default target
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Installation:"
	@echo "  all          - Full installation and setup (recommended)"
	@echo "  install      - Install project in development mode"
	@echo ""
	@echo "Virtual Environment:"
	@echo "  activate     - Show instructions to activate the virtual environment"
	@echo ""
	@echo "Running the App:"
	@echo "  dev          - Run the app in development mode"
	@echo "  prod         - Run the app in production mode"
	@echo ""
	@echo "Development:"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with Black"
	@echo "  typecheck    - Run static type checking with mypy"
	@echo "  grpc-gen     - Generate gRPC Python files"
	@echo "  docs         - Build Sphinx documentation"
	@echo "  clean        - Remove temporary files and caches"

run:
	uv run python -m ami.main --verbose
dev:									# `make dev ARGS="--ai --gui"`
	uv run python -m ami.dev $(ARGS)
idev:									# `make idev ARGS="--backend"`
	uv run python -i -m ami.dev $(ARGS)

clean:				# Clean up
	find . -type d -name "__pycache__" -exec rm -r {} + || true
	find . -type f -name "*.pyc" -delete || true
	rm -rf .pytest_cache .coverage *.egg-info dist build .venv
	rm -rf docs/_build

test:				# Run tests
	uv run pytest --cov=ami --cov-report=term-missing -v

lint:				# Lint code
	uv run flake8 ami tests

docs:				# Build documentation
	uv run sphinx-build -b html docs docs/_build
