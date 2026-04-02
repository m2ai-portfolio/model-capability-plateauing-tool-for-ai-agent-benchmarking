#!/bin/bash
set -e

echo "Setting up Model Capability Plateauing Tool..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -q click pytest

echo "Setup complete! Run 'python -m benchmarks.cli --help' for usage."
echo "Dev server not applicable - this is a CLI tool."
echo "Run tests with: pytest"
