#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate the virtual environment
source "${SCRIPT_DIR}/venv/bin/activate"

# Print confirmation
echo "Virtual environment activated. You can deactivate it by running 'deactivate'"