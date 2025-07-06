# Architecture of ReqSnake

This document describes the architecture of ReqSnake, a MkDocs plugin for requirements management. It serves as a guide for developers who want to understand, extend, or contribute to the codebase.

## Overview

ReqSnake is a **MkDocs plugin** that transforms Markdown documentation into a requirements management system. It extracts requirements from blockquote syntax, validates relationships, and generates interactive documentation with traceability diagrams.

### Core Principles

- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **MkDocs Integration**: Clean integration with MkDocs plugin lifecycle
- **Type Safety**: Comprehensive type hints throughout the codebase
- **Testability**: Modular design enables comprehensive unit and integration testing

## System Architecture

### Data Flow Pipeline

```
Markdown Files → Parser → Validator → Generator → MkDocs Pages
     ↓              ↓         ↓           ↓
  (.md files) (Requirements) (Validated) (Additional markdown)
```

### Module Responsibilities

| Module          | Purpose                                              | Key Components                                |
| --------------- | ---------------------------------------------------- | --------------------------------------------- |
| `plugin.py`     | MkDocs integration and lifecycle management          | `ReqSnakePlugin`, `on_files()` hook           |
| `parser.py`     | Extract requirements from Markdown blockquotes       | `parse_requirements_from_content()`           |
| `models.py`     | Core data structures                                 | `Requirement`, `ParsedRequirement`            |
| `validator.py`  | Validate requirement relationships and detect cycles | `validate_requirements()`                     |
| `generator.py`  | Generate requirement pages and index                 | Modular generation architecture               |
| `utils.py`      | Utility functions                                    | File filtering, `.requirementsignore` support |
| `exceptions.py` | Custom exception hierarchy                           | MkDocs-compatible error handling              |

## Testing Architecture

### Unit Tests (`tests/unit/`)

Test individual components in isolation:

- **`test_models.py`**: Data model behavior and validation
- **`test_parser.py`**: Parsing logic and edge cases
- **`test_generator.py`**: Content generation and diagram creation
- **`test_validator.py`**: Requirement validation rules
- **`test_utils.py`**: Utility functions and file filtering

### Integration Tests (`tests/integration/`)

Test component interactions and end-to-end workflows:

- **`test_plugin_integration_simple.py`**: Basic plugin lifecycle
- **`test_ignore_integration.py`**: File filtering functionality

**Testing approach:**

- Fixtures for reusable test data (`tests/fixtures/`)
- Temporary directories for file system tests
- Mock MkDocs objects for plugin testing
- Comprehensive edge case coverage

## Extension Points

### Adding New Diagram Types

1. Create new generator inheriting from `MermaidGenerator`
2. Implement `generate()` method
3. Add to `RequirementPageGenerator`
4. Add corresponding tests

### Adding New Validation Rules

1. Add validation logic to `validator.py`
2. Define custom exception in `exceptions.py`
3. Add comprehensive test coverage
4. Update documentation

### Adding New Requirement Attributes

1. Update `Requirement` dataclass in `models.py`
2. Update parser logic in `parser.py`
3. Update generation logic if needed
4. Add tests for new attribute handling

## File Organization Best Practices

```
mkdocs_reqsnake/
├── __init__.py          # Package exports
├── plugin.py            # START HERE: Main entry point
├── models.py            # Core data structures
├── parser.py            # Markdown → Requirements
├── validator.py         # Requirements validation
├── generator.py         # Requirements → HTML
├── utils.py             # Cross-cutting utilities
└── exceptions.py        # Error handling
```

**For new developers:**

- Start reading from `plugin.py` to understand the overall flow
- Examine `models.py` to understand the data structures
- Follow the pipeline: `parser.py` → `validator.py` → `generator.py`
- Check `tests/` for examples of how components interact

## Development Workflow

1. **Setup**: Install in development mode with test dependencies
2. **Testing**: Run `./check.sh` for comprehensive validation
3. **Changes**: Follow the module responsibility boundaries
4. **Documentation**: Update architecture docs for significant changes
5. **Requirements**: Use ReqSnake to track your own requirement changes!
