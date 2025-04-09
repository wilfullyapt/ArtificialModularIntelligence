# Agent Installation and Testing Guide

## Installation Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/wilfullyapt/ArtificialModularIntelligence.git
   cd ArtificialModularIntelligence
   ```

2. Run the full installation (creates virtual environment and installs dependencies):
   ```bash
   make all
   ```

3. Activate the virtual environment:
   ```bash
   source ./activate.sh
   ```

4. Verify the installation by running the development server:
   ```bash
   make dev
   ```

Note: This project is designed to run on Linux only. Windows and MacOS are not supported.

## Running Tests

1. Ensure your virtual environment is activated:
   ```bash
   source ./activate.sh
   ```

2. Run all tests with coverage report:
   ```bash
   make test
   ```

3. Run specific test suites:
   ```bash
   # Run only unit tests
   pytest tests/unit

   # Run only integration tests
   pytest tests/integration
   ```

4. Run code quality checks:
   ```bash
   # Run all checks
   make lint
   make typecheck

   # Format code
   make format
   ```

5. Generate test coverage report:
   ```bash
   pytest --cov=ami --cov-report=html
   # Open htmlcov/index.html in your browser to view the report
   ```