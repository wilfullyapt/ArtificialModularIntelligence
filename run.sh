#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d "venv" ]; then
    if [ -f "venv/bin/activate" ]; then
        echo "Activating virtual environment"
        source venv/bin/activate
    else
        echo "Virtual environment found but activate script is missing"
    fi
else
    echo "Virtual environment not found"
fi

# Check if the -d flag is provided
if [ "$1" == "-d" ]; then
    echo "Running in dev mode (ami.dev)"
    python -i -m ami.dev
elif [ "$1" == "-l" ]; then
    echo "Running pylint"
    shift  # Remove the -l argument
    if [ $# -gt 0 ]; then
        echo "Running pylint on specified directories/files: $@"
        pylint "$@"
    else
        echo "Running pylint on ami directory (excluding headspace/core)"
        pylint ami --ignore=core
    fi
else
    echo "Running in normal mode (ami.ami)"
    python -m ami.ami
fi

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Deactivating virtual environment"
    deactivate
fi
