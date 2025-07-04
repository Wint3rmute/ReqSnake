#!/bin/sh

set -e

source .venv/bin/activate

# Format code

python -m ruff format .

# Run mypy type checker
python -m mypy .

# Run unit and integration tests
python test_reqsnake.py

# Run ruff linter
python -m ruff check .

echo "All tests and linters passed!" 