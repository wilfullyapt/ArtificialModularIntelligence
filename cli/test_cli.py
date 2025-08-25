
#!/usr/bin/env python3
"""
CLI Test Runner

This script runs all CLI tests with a single command.
It compiles the C binary if needed and runs both unit and integration tests.
"""

import subprocess
import sys
from pathlib import Path
import os

def ensure_cli_binary():
    """Ensure the CLI binary is compiled."""
    cli_dir = Path(__file__).parent
    cli_path = cli_dir / "ami"
    
    if not cli_path.exists():
        print("CLI binary not found. Compiling...")
        result = subprocess.run(["make", "clean"], cwd=cli_dir)
        result = subprocess.run(["make"], cwd=cli_dir)
        if result.returncode != 0:
            print("Failed to compile CLI binary")
            return False
    return True

def run_c_tests():
    """Run C unit tests."""
    cli_dir = Path(__file__).parent
    print("Running C unit tests...")
    
    # Create test temp directory
    os.makedirs(cli_dir / "test" / "tmp", exist_ok=True)
    
    result = subprocess.run(["make", "test"], cwd=cli_dir)
    if result.returncode != 0:
        print("C unit tests failed")
        return False
    return True

def run_python_tests():
    """Run Python integration tests."""
    project_root = Path(__file__).parent.parent
    
    print("Running Python CLI tests...")
    result = subprocess.run([
        "uv", "run", "pytest", 
        "tests/cli/", 
        "-v", 
        "--cov=ami.cli",
        "--cov-report=term-missing"
    ], cwd=project_root)
    
    if result.returncode != 0:
        print("Python CLI tests failed")
        return False
    return True

def run_tests():
    """Run all CLI tests."""
    if not ensure_cli_binary():
        return False
    
    if not run_c_tests():
        return False
        
    if not run_python_tests():
        return False
    
    print("All CLI tests passed!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
