#!/bin/sh

set -e

# Format code
python -m ruff format .

# Run ruff linter
python -m ruff check .

# Run mypy type checker
python -m mypy mkdocs_reqsnake/

pytest --cov=mkdocs_reqsnake --cov-report=term-missing --cov-fail-under=90 .

echo "All tests and linters passed!" 
