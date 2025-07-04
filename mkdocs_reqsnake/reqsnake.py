#!/usr/bin/env python3
"""reqsnake.py - Backward compatibility module for ReqSnake.

This module provides backward compatibility for the original API.
The actual implementation has been split into focused modules.
"""

__version__ = "1.0.0"

__all__ = [
    "Requirement",
    "ParsedRequirement",
    "DiffType",
    "parse_requirements_from_files",
    "parse_requirements_from_markdown",
    "validate_requirements",
    "generate_requirement_page_content",
    "generate_requirement_index_content",
    "progress_bar",
    "diff_requirements",
    "ReqSnakeError",
    "ParseError",
    "ValidationError",
    "DuplicateRequirementError",
    "CircularDependencyError",
    "CompletionValidationError",
    "InvalidRequirementIdError",
    "UnknownAttributeError",
    "_parse_requirements_from_markdown",
    "_progress_bar",
    "_diff_requirements",
    "_validate_no_cycles",
    "_validate_completed_children",
    "_validate_duplicate_ids",
]

# Re-export from new modules for backward compatibility
from typing import List

from .models import Requirement, ParsedRequirement, DiffType
from .parser import parse_requirements_from_files, parse_requirements_from_markdown
from .validator import validate_requirements
from .generator import (
    generate_requirement_page_content,
    generate_requirement_index_content,
)
from .utils import progress_bar, diff_requirements
from .exceptions import (
    ReqSnakeError,
    ParseError,
    ValidationError,
    DuplicateRequirementError,
    CircularDependencyError,
    CompletionValidationError,
    InvalidRequirementIdError,
    UnknownAttributeError,
)

# Backward compatibility aliases
_parse_requirements_from_markdown = parse_requirements_from_markdown
_progress_bar = progress_bar
_diff_requirements = diff_requirements


# For backward compatibility, expose the old function names
def _validate_no_cycles(requirements: List[Requirement]) -> None:
    """Backward compatibility function."""
    from .validator import validate_no_cycles

    return validate_no_cycles(requirements)


def _validate_completed_children(requirements: List[Requirement]) -> None:
    """Backward compatibility function."""
    from .validator import validate_completed_children

    return validate_completed_children(requirements)


def _validate_duplicate_ids(parsed_requirements: List[ParsedRequirement]) -> None:
    """Backward compatibility function."""
    from .validator import validate_no_duplicate_ids

    return validate_no_duplicate_ids(parsed_requirements)
