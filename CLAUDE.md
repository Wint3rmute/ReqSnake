# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ReqSnake is a MkDocs plugin that automatically extracts and displays requirements from Markdown documentation using blockquote syntax.

## Core Architecture

- **`mkdocs_reqsnake/models.py`** - Core data models (Requirement, ParsedRequirement)
- **`mkdocs_reqsnake/plugin.py`** - MkDocs plugin integration via `on_nav()` hook
- **`mkdocs_reqsnake/parser.py`** - Markdown parsing logic for extracting requirements
- **`mkdocs_reqsnake/validator.py`** - Requirements validation (cycles, completion, missing parents)
- **`mkdocs_reqsnake/generator.py`** - Content generation for requirement pages and index
- **`mkdocs_reqsnake/utils.py`** - Utility functions for .requirementsignore file handling
- **`mkdocs_reqsnake/exceptions.py`** - Custom exception classes

### Requirements Syntax

```markdown
> REQ-ID-123
> Requirement description here
> critical
> child-of: PARENT-REQ-1
> completed
```

## Development Commands

```bash
# Run all checks (formatting, linting, type checking, tests)
./check.sh

# Testing with MkDocs
mkdocs build
mkdocs serve
```

## Key Features

### Page Generation (`mkdocs_reqsnake/generator.py`)

- **Mermaid diagrams**: Interactive flowcharts with parent-child relationships using `graph LR` layout
- **Enhanced nodes**: Show requirement ID + first 4 words of description
- **Color coding**: Parents (blue), current (orange), children (purple) - dark mode compatible
- **Completion tracking**: Status summaries in all sections (e.g., "Parents (1/3 completed)")
- **Critical indicators**: Warning appears above description for visibility

### File Filtering (`.requirementsignore`)

- **Gitignore-style patterns**: Support for `*.tmp`, `build/`, `test_*.md` patterns
- **Automatic discovery**: Loads `.requirementsignore` from project root automatically
- **Graceful fallback**: Continues processing if ignore file is missing or unreadable
- **Logging**: Reports number of ignored files during build

### Implementation Notes

- Always run `./check.sh` before committing
- Maintain strict typing with mypy
- Use helper functions `_truncate_description()` and `_get_requirement_by_id()`
- Clickable navigation uses site-relative paths `/reqsnake/{req_id}`

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (\*.md) or README files. Only create documentation files if explicitly requested by the User.
