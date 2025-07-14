.PHONY: help install dev prod clean test lint format typecheck grpc-gen docs all activate

# Variables
PYTHON ?= python3
VENV = venv
PROTO_DIR ?= ami/protos
GENERATED_DIR ?= ami/protos/generated
PORT ?= 54996

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
	@echo "  dev          - Run the app in development mode (port: $(PORT))"
	@echo "  prod         - Run the app in production mode (port: $(PORT))"
	@echo ""
	@echo "Development:"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with Black"
	@echo "  typecheck    - Run static type checking with mypy"
	@echo "  grpc-gen     - Generate gRPC Python files"
	@echo "  docs         - Build Sphinx documentation"
	@echo "  clean        - Remove temporary files and caches"

# Full installation and setup
all: install grpc-gen

# Show activation instructions
activate:
	@echo "To activate the virtual environment, run:"
	@echo "  source ./activate.sh"
	@echo ""
	@echo "Or manually with:"
	@echo "  source venv/bin/activate"
	@echo ""
	@echo "You can deactivate it anytime by running 'deactivate'"

# Install project in development mode
install:
	@echo "Running install.sh script..."
	@bash install.sh


# Production mode
prod:
	. $(VENV)/bin/activate && gunicorn -w 4 -b 0.0.0.0:$(PORT) ami.main:app

run:
	venv/bin/python -m ami.main --verbose

dev:
	venv/bin/python -m ami.dev
idev:
	venv/bin/python -i -m ami.dev

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -r {} + || true
	find . -type f -name "*.pyc" -delete || true
	rm -rf .pytest_cache .coverage *.egg-info dist build $(VENV)
	rm -rf docs/_build

# Run tests
test:
	. $(VENV)/bin/activate && pytest --cov=ami --cov-report=term-missing -v

# Lint code
lint:
	. $(VENV)/bin/activate && flake8 ami tests

# Format code
format:
	. $(VENV)/bin/activate && black ami tests

# Type checking
typecheck:
	. $(VENV)/bin/activate && mypy ami

# Build documentation
docs:
	. $(VENV)/bin/activate && sphinx-build -b html docs docs/_build
