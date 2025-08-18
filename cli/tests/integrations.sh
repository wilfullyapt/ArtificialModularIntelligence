#!/bin/bash

set -e  # Exit on error

# Setup temp dir and mock repo
TEST_DIR=/tmp/ami_test
rm -rf $TEST_DIR
mkdir -p $TEST_DIR/repo/cli/source $TEST_DIR/repo/cli/include
cd $TEST_DIR/repo

# Mock git repo with tags
git init
echo "Mock ami.py" > ami.py
git add ami.py
git commit -m "Initial"
git tag v1.0.0
# Simulate CLI change
echo "// Mock change" >> cli/source/commands.c
git add .
git commit -m "CLI change"
git tag v1.1.0
# Mock failing test
echo "test: false" > Makefile  # Simulates make test failing

# Build binary in test env
cp -r /path/to/your/cli/code/* cli/  # Copy your real code
cd cli
make clean && make

# Test safe-update (expect rollback on test fail)
./ami --source-dir $TEST_DIR/repo safe-update
if [ $? -eq 0 ]; then echo "FAIL: Update should fail"; exit 1; fi
# Check rollback happened (e.g., git tag == v1.0.0)
CURRENT_TAG=$(git -C $TEST_DIR/repo describe --tags --abbrev=0)
if [ "$CURRENT_TAG" != "v1.0.0" ]; then echo "FAIL: Rollback failed"; exit 1; fi

# Test plugin install
./ami plugin install user/mock-repo  # Mock, will fail but check log_error
if [ $? -eq 0 ]; then echo "FAIL: Install invalid repo should fail"; exit 1; fi

# Test run (mock Python success)
echo "#!/usr/bin/env python3\necho 'Mock run'" > $TEST_DIR/repo/ami.py
chmod +x $TEST_DIR/repo/ami.py
./ami run | grep "Mock run" || { echo "FAIL: Run failed"; exit 1; }

# Add more: autostart (check file created, but don't enable), rollback, etc.

echo "All tests passed!"
rm -rf $TEST_DIR
