"""Requirements validation logic for ReqSnake."""

from pathlib import Path
from typing import Dict, List, Set

from .exceptions import (
    CircularDependencyError,
    CompletionValidationError,
    DuplicateRequirementError,
)
from .models import ParsedRequirement, Requirement


def validate_requirements(parsed_requirements: List[ParsedRequirement]) -> None:
    """Run all validation checks on parsed requirements.

    Args:
        parsed_requirements: List of ParsedRequirement objects to validate.

    Raises:
        ValidationError: If any validation fails.

    """
    if not parsed_requirements:
        return

    # Extract just the requirements for validation functions
    requirements = [pr.requirement for pr in parsed_requirements]

    # Run all validations
    validate_no_duplicate_ids(parsed_requirements)
    validate_no_cycles(requirements)
    validate_completed_children(requirements)


def validate_no_duplicate_ids(parsed_requirements: List[ParsedRequirement]) -> None:
    """Validate that no duplicate requirement IDs exist across files.

    Args:
        parsed_requirements: List of ParsedRequirement objects to validate.

    Raises:
        DuplicateRequirementError: If duplicate requirement IDs are found.

    """
    seen_ids: Dict[str, Path] = {}

    for parsed_req in parsed_requirements:
        req_id = parsed_req.requirement.req_id
        source_file = parsed_req.source_file

        if req_id in seen_ids:
            first_file = seen_ids[req_id]
            raise DuplicateRequirementError(
                f"Duplicate requirement ID '{req_id}' found in '{source_file}'. "
                f"First defined in '{first_file}'."
            )
        seen_ids[req_id] = source_file


def validate_no_cycles(requirements: List[Requirement]) -> None:
    """Validate that no circular dependencies exist in the requirements graph.

    Args:
        requirements: List of Requirement objects to validate.

    Raises:
        CircularDependencyError: If a circular dependency is detected.

    """
    # Build adjacency list: parent_id -> [child_id1, child_id2, ...]
    # This represents the dependency tree structure
    adj: Dict[str, List[str]] = {}
    for req in requirements:
        # Initialize empty list for each requirement
        if req.req_id not in adj:
            adj[req.req_id] = []
        # Add this requirement as a child of each of its parents
        for parent_id in req.parents:
            if parent_id not in adj:
                adj[parent_id] = []
            adj[parent_id].append(req.req_id)

    visiting: Set[str] = set()  # For the current traversal path
    visited: Set[str] = set()  # For all nodes ever visited

    def visit(req_id: str, path: List[str]) -> None:
        visiting.add(req_id)
        path.append(req_id)

        for child_id in adj.get(req_id, []):
            if child_id in visiting:
                path.append(child_id)
                raise CircularDependencyError(
                    f"Circular dependency detected: {' -> '.join(path)} (REQ-PARSER-15)"
                )
            if child_id not in visited:
                visit(child_id, path)

        path.pop()
        visiting.remove(req_id)
        visited.add(req_id)

    for req in requirements:
        if req.req_id not in visited:
            visit(req.req_id, [])


def validate_completed_children(requirements: List[Requirement]) -> None:
    """Validate that completed requirements don't have incomplete children.

    Args:
        requirements: List of Requirement objects to validate.

    Raises:
        CompletionValidationError: If completed requirements have incomplete children.

    """
    req_dict = {r.req_id: r for r in requirements}

    # Build parent -> children mapping
    children_map: Dict[str, List[str]] = {}
    for req in requirements:
        # Initialize empty list for each requirement
        if req.req_id not in children_map:
            children_map[req.req_id] = []
        # Add this requirement as a child of each of its parents
        for parent_id in req.parents:
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(req.req_id)

    errors: List[tuple[str, str]] = []

    for req in requirements:
        if req.completed:
            # Check if all children of this requirement are completed
            for child_id in children_map.get(req.req_id, []):
                child = req_dict.get(child_id)
                if child is not None and not child.completed:
                    errors.append((req.req_id, child_id))

    if errors:
        msg = "The following requirements are marked as completed but have incomplete children:\n"
        for parent_id, child_id in errors:
            msg += f"  - {parent_id} (incomplete child: {child_id})\n"
        raise CompletionValidationError(msg)
