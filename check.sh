#!/bin/sh

set -e

# Format code

black .

# Run unit and integration tests
python test_require.py

# Run ruff linter
ruff check .

# Run mypy type checker
mypy .

echo "All tests and linters passed!" 