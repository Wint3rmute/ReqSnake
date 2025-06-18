#!/bin/sh

git add -A && git commit -m "AI is running checks"

set -e

# Format code

black .

# Run mypy type checker
mypy .

# Run unit and integration tests
python test_require.py

# Run ruff linter
ruff check .

echo "All tests and linters passed!" 