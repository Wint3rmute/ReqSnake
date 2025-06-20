#!/bin/sh

set -e

# Format code

black .

# Run mypy type checker
mypy .

# Run unit and integration tests
python test_reqsnake.py

# Run ruff linter
ruff check .

echo "All tests and linters passed!" 