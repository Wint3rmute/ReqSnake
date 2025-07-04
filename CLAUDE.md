# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ReqSnake is a MkDocs plugin that automatically extracts and displays
requirements from Markdown documentation using blockquote syntax. It's written
in Python and provides both a standalone CLI tool and a MkDocs plugin
interface.

## Core Architecture

### Main Components

- **`mkdocs_reqsnake/reqsnake.py`** - Core requirements parsing and management logic

  - Contains `Requirement` dataclass and parsing functions
  - Provides Python API functions: `reqsnake_init()`, `reqsnake_check()`, `reqsnake_lock()`, `reqsnake_status()`
  - Handles requirement validation, dependency checking, and lockfile management
  - CLI interface for standalone usage

- **`mkdocs_reqsnake/plugin.py`** - MkDocs plugin implementation
  - Integrates with MkDocs build process via `on_files()` hook
  - Generates requirement pages and index automatically
  - Uses `_parse_requirements_from_markdown()` to extract requirements from documentation

### Key Data Structures

- **`Requirement`** - Core dataclass representing a requirement with fields:

  - `req_id`: Unique identifier (format: `<STRING>-<NUMBER>`)
  - `description`: Human-readable description
  - `critical`: Boolean flag for critical requirements
  - `children`: List of parent requirement IDs (creates dependency tree)
  - `completed`: Boolean completion status

- **`StatusResult`** - Contains requirements with file associations and completion statistics

### Requirements Syntax

Requirements are defined in Markdown blockquotes with this format:

```markdown
> REQ-ID-123
> Requirement description here
> critical
> child-of: PARENT-REQ-1
> completed
```

## Development Commands

### Environment Setup

```bash
# Activate virtual environment (if using one)
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"
```

### Core Development Workflow

```bash
# Run all checks (formatting, linting, type checking, tests)
./check.sh

# Individual commands:
python -m ruff format .          # Format code
python -m mypy .                 # Type checking
python -m ruff check .           # Linting
python test_reqsnake.py          # Core functionality tests
python test_mkdocs_plugin.py     # MkDocs plugin tests
```

### Testing with MkDocs

```bash
# Build documentation site
mkdocs build

# Serve locally for development
mkdocs serve
```

## Key Files and Configurations

- **`setup.py`** - Package configuration with dependencies: `mkdocs>=1.6`, `mkdocs-material>=9.6`
- **`mkdocs.yml`** - Test MkDocs configuration using the plugin
- **`mypy.ini`** - Type checking configuration (strict mode enabled)
- **`pyproject.toml`** - Ruff linting configuration
- **`check.sh`** - Main development script that runs all checks

## Testing Strategy

The project uses two main test files:

- **`test_reqsnake.py`** - Unit and integration tests for core functionality
- **`test_mkdocs_plugin.py`** - Tests for MkDocs plugin integration

Tests create temporary directories and test the full workflow including file parsing, lockfile generation, and requirement validation.

## Important Implementation Details

### Requirement Parsing

- Uses regex `BLOCKQUOTE_PATTERN` to extract blockquotes from Markdown
- Enforces strict ID format: `<STRING>-<NUMBER>` with ASCII characters only
- Validates dependency cycles and completion constraints
- Supports `.requirementsignore` files (gitignore-style patterns)

### MkDocs Integration

- Plugin hooks into `on_files()` to generate pages during build
- Creates individual requirement pages under `./reqsnake/` path
- Generates a requirements index page automatically

### Validation Rules

- No duplicate requirement IDs across files
- No circular dependencies in requirement hierarchy
- Completed requirements cannot have incomplete children
- Unknown attributes in requirements cause validation errors

## Common Patterns

When working with this codebase:

1. Always run `./check.sh` before committing changes
2. Use the Python API functions for extending functionality
3. Follow the existing error handling patterns with descriptive ValueError messages
4. Maintain the strict typing with mypy
