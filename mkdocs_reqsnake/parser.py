"""Requirements parsing logic for ReqSnake."""

import re
from pathlib import Path

from mkdocs.exceptions import PluginError

from .exceptions import InvalidRequirementIdError, ParseError, UnknownAttributeError
from .models import ParsedRequirement, Requirement

# Regex for blockquotes: matches contiguous blockquote lines
BLOCKQUOTE_PATTERN = re.compile(
    r"(^> .*(?:\n>.*)*)",  # Match '> ' block and following '> ...' lines
    re.MULTILINE,
)


def parse_requirements_from_markdown(md_text: str) -> list[Requirement]:
    """Parse requirements from Markdown text using block-quote syntax.

    Args:
        md_text: The Markdown text to parse.

    Returns:
        A list of parsed Requirement objects.

    Raises:
        ParseError: If parsing fails.
        InvalidRequirementIdError: If requirement ID format is invalid.
        UnknownAttributeError: If unknown attributes are found.

    """
    # Remove HTML comments (REQ-PARSER-17)
    md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.DOTALL)

    requirements: list[Requirement] = []

    for block in BLOCKQUOTE_PATTERN.findall(md_text):
        try:
            requirement = _parse_single_requirement_block(block)
            if requirement:
                requirements.append(requirement)
        except (InvalidRequirementIdError, UnknownAttributeError) as e:
            raise ParseError(f"Failed to parse requirement block: {e}") from e

    return requirements


def _parse_single_requirement_block(block: str) -> Requirement | None:
    """Parse a single requirement block.

    Args:
        block: The blockquote block text.

    Returns:
        Parsed Requirement or None if block should be ignored.

    Raises:
        InvalidRequirementIdError: If requirement ID format is invalid.
        UnknownAttributeError: If unknown attributes are found.

    """
    # Only consider lines starting with '>' (REQ-PARSER-12)
    lines = [line[2:].strip() for line in block.split("\n") if line.startswith(">")]

    # Remove empty lines (REQ-PARSER-7)
    lines = [line for line in lines if line.strip()]

    # Skip blockquotes with only an ID or only a description (REQ-PARSER-6)
    if len(lines) < 2:
        return None

    req_id = lines[0]

    # Heuristic: if the potential ID contains spaces, it's not a requirement.
    if " " in req_id:
        return None

    # Validate requirement ID format
    _validate_requirement_id(req_id)

    description = lines[1]
    critical = False
    completed = False
    parents: list[str] = []
    seen_parents: set[str] = set()

    # Process attributes
    for line in lines[2:]:
        critical, completed = _process_attribute_line(
            line, req_id, seen_parents, parents, critical, completed
        )

    return Requirement(req_id, description, critical, parents, completed)


def _validate_requirement_id(req_id: str) -> None:
    """Validate requirement ID format.

    Args:
        req_id: The requirement ID to validate.

    Raises:
        InvalidRequirementIdError: If ID format is invalid.

    """
    # Enforce REQ-CORE-6: ID must be ASCII only, then <STRING>-<NUMBER>
    if not all(ord(c) < 128 for c in req_id):
        raise InvalidRequirementIdError(
            f"Requirement ID '{req_id}' contains non-ASCII characters, "
            f"which are not allowed. (REQ-CORE-6)"
        )

    if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*-\d+$", req_id):
        raise InvalidRequirementIdError(
            f"Requirement ID '{req_id}' does not match the required format "
            f"'<STRING>-<NUMBER>' (REQ-CORE-6)"
        )


def _process_attribute_line(
    line: str,
    req_id: str,
    seen_parents: set[str],
    parents: list[str],
    critical: bool,
    completed: bool,
) -> tuple[bool, bool]:
    """Process a single attribute line.

    Args:
        line: The attribute line to process.
        req_id: The requirement ID for error messages.
        seen_parents: Set of already seen parent IDs.
        parents: List to append parent IDs to.
        critical: Current critical flag.
        completed: Current completed flag.

    Returns:
        Tuple of (critical, completed) flags.

    Raises:
        UnknownAttributeError: If unknown attribute is found.

    """
    norm = line.strip().lower()

    if norm == "critical":
        return True, completed
    elif norm == "completed":
        return critical, True
    elif norm.startswith("child-of"):
        _process_child_of_line(line, req_id, seen_parents, parents)
        return critical, completed
    else:
        # REQ-PARSER-10: raise errors on unknown attributes
        raise PluginError(f"Unknown attribute '{line.strip()}' in requirement {req_id}")


def _process_child_of_line(
    line: str, req_id: str, seen_parents: set[str], parents: list[str]
) -> None:
    """Process a child-of attribute line.

    Args:
        line: The child-of line to process.
        req_id: The requirement ID for error messages.
        seen_parents: Set of already seen parent IDs.
        parents: List to append parent ID to.

    Raises:
        ParseError: If duplicate child-of line is found.

    """
    after = line[len("child-of") :].lstrip()
    if after.startswith(":"):
        after = after[1:].lstrip()

    parent_id = after.strip()
    if parent_id:
        norm_parent_id = parent_id.upper()
        if norm_parent_id in seen_parents:
            raise ParseError(
                f"Duplicate parent ID '{parent_id}' in requirement '{req_id}' "
                f"(case-insensitive, whitespace-insensitive)"
            )
        seen_parents.add(norm_parent_id)
        parents.append(parent_id)


def parse_requirements_from_files(
    file_data: list[tuple[str, str]],
) -> list[ParsedRequirement]:
    """Parse requirements from a list of (file_path, content) tuples.

    Args:
        file_data: List of (file_path, content_string) tuples.

    Returns:
        List of ParsedRequirement objects with file associations.

    Raises:
        ParseError: If parsing fails.

    """
    all_parsed_reqs: list[ParsedRequirement] = []

    for file_path, content in file_data:
        try:
            reqs = parse_requirements_from_markdown(content)
            all_parsed_reqs.extend(
                [
                    ParsedRequirement(requirement=req, source_file=Path(str(file_path)))
                    for req in reqs
                ]
            )
        except ParseError as e:
            raise ParseError(f"Error in file '{file_path}': {e}") from e

    return all_parsed_reqs
