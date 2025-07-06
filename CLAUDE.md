# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ReqSnake is a MkDocs plugin that automatically extracts and displays requirements from Markdown documentation using blockquote syntax.

## Core Architecture

- **`mkdocs_reqsnake/models.py`** - Core data models which make up the application
- **`mkdocs_reqsnake/plugin.py`** - MkDocs plugin integration via `on_files()` hook
- **`mkdocs_reqsnake/*.py`** - Other Python files which work together with `models.py` and `plugin.py`

### Requirements Syntax

```markdown
> REQ-ID-123
>
> Requirement description here
>
> critical
>
> child-of: PARENT-REQ-1
```

## Development Commands

```bash
# Run all checks (formatting, linting, type checking, tests)
./check.sh

# Testing with MkDocs
mkdocs build
```

### Implementation Notes

- Always run `./check.sh` before committing
- Maintain strict typing with mypy
- Never do manual testing, always write automated tests
