"""
CLI Test Runner

This script runs all CLI tests with a single command.
It compiles the C binary if needed and runs both unit and integration tests.
"""

import subprocess
import sys
from pathlib import Path

def ensure_cli_binary():
    """Ensure the CLI binary is compiled."""
    cli_path = Path(__file__).parent / "ami"
    if not cli_path.exists():
        print("CLI binary not found. Compiling...")
        result = subprocess.run(["make", "cli"], cwd=Path(__file__).parent.parent)
        if result.returncode != 0:
            print("Failed to compile CLI binary")
            return False
    return True


def run_tests():
    """Run all CLI tests."""
    if not ensure_cli_binary():
        return False
    
    project_root = Path(__file__).parent.parent
    
    # Run CLI-specific tests
    print("Running CLI tests...")
    result = subprocess.run([
        "uv", "run", "pytest", 
        "tests/cli/", 
        "-v", 
        "--cov=ami.cli",
        "--cov-report=term-missing"
    ], cwd=project_root)
    
    if result.returncode != 0:
        print("CLI tests failed")
        return False
    
    print("All CLI tests passed!")
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
