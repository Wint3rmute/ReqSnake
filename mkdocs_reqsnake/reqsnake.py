#! /usr/bin/env python3
"""reqsnake.py - Core requirements parsing and validation for ReqSnake.

This module provides the core functionality for parsing requirements from Markdown files
and validating them. It's designed to work as part of the MkDocs plugin.
"""

import re
from typing import Optional, Any, Set, Tuple, Dict, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum, auto

__version__ = "1.0.0"


# =============================================================================
# CORE DATA MODELS
# =============================================================================


@dataclass(frozen=True)
class Requirement:
    """Represent a requirement parsed from a Markdown block-quote.

    Attributes:
        req_id (str): The unique identifier of the requirement.
        description (str): A short description of the requirement.
        critical (bool): Whether the requirement is marked as critical.
        children (list[str]): List of child requirement IDs.
        completed (bool): Whether the requirement is completed.

    """

    req_id: str
    description: str
    critical: bool = False
    children: list[str] = field(default_factory=list)
    completed: bool = False

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Requirement":
        """Create a Requirement from a dictionary."""
        return Requirement(
            req_id=data["req_id"],
            description=data["description"],
            critical=data.get("critical", False),
            children=data.get("children", []),
            completed=data.get("completed", False),
        )

    def to_pretty_string(self) -> str:
        """Return a human-readable, multi-line string representation of the requirement."""
        lines = [f"{self.req_id}: {self.description}\n\n"]
        if self.critical:
            lines.append("**⚠️ critical**\n\n")
        if self.completed:
            lines.append("✅ completed\n\n")
        if self.children:
            lines.append(f"### Children\n\n")
            for child in self.children:
                lines.append(f"- {child}\n")
        return "".join(lines)


@dataclass(frozen=True)
class ParsedRequirement:
    """A requirement and the path to the file it was parsed from."""

    requirement: Requirement
    source_file: Path


class DiffType(Enum):
    """Enum representing types of requirement diffs: added, removed, or changed."""

    ADDED = auto()
    REMOVED = auto()
    CHANGED = auto()

    def __str__(self) -> str:
        """Return the lowercase name of the DiffType enum member."""
        return self.name.lower()


# =============================================================================
# CORE PARSING LOGIC
# =============================================================================

# Regex for blockquotes: matches contiguous blockquote lines
BLOCKQUOTE_PATTERN = re.compile(
    r"(^> .*(?:\n>.*)*)",  # Match a block starting with '> ' and all following '> ...' lines
    re.MULTILINE,
)


def _parse_requirements_from_markdown(md_text: str) -> list[Requirement]:
    """Parse requirements from Markdown text using block-quote syntax.

    Args:
        md_text (str): The Markdown text to parse.

    Returns:
        list[Requirement]: A list of parsed Requirement objects.

    Raises:
        ValueError: If duplicate requirement IDs are found.

    """
    # Remove HTML comments (REQ-PARSER-17)
    import re as _re

    md_text = _re.sub(r"<!--.*?-->", "", md_text, flags=_re.DOTALL)

    requirements: list[Requirement] = []
    for block in BLOCKQUOTE_PATTERN.findall(md_text):
        # Only consider lines starting with '>' (REQ-PARSER-12)
        lines = [line[2:].strip() for line in block.split("\n") if line.startswith(">")]
        # Remove empty lines (REQ-PARSER-7)
        lines = [line for line in lines if line.strip()]
        # Skip blockquotes with only an ID or only a description (REQ-PARSER-6)
        if len(lines) < 2:
            continue
        req_id = lines[0]
        # Heuristic: if the potential ID contains spaces, it's not a requirement.
        if " " in req_id:
            continue
        # Enforce REQ-CORE-6: ID must be ASCII only, then <STRING>-<NUMBER>
        if not all(ord(c) < 128 for c in req_id):
            raise ValueError(
                f"Requirement ID '{req_id}' contains non-ASCII characters, which are not allowed. (REQ-CORE-6)"
            )
        if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*-\d+$", req_id):
            raise ValueError(
                f"Requirement ID '{req_id}' does not match the required format '<STRING>-<NUMBER>' (REQ-CORE-6)"
            )
        description = lines[1]
        critical = False
        completed = False
        children: list[str] = []
        seen_children: Set[str] = set()
        for line in lines[2:]:
            norm = line.strip().lower()
            if norm == "critical":
                critical = True
            elif norm == "completed":
                completed = True
            elif norm.startswith("child-of"):
                after = line[len("child-of") :].lstrip()
                if after.startswith(":"):
                    after = after[1:].lstrip()
                child_id = after
                if child_id:
                    norm_child_id = child_id.strip().upper()
                    if norm_child_id in seen_children:
                        raise ValueError(
                            f"Duplicate child ID '{child_id}' in requirement '{req_id}' (case-insensitive, whitespace-insensitive)"
                        )
                    seen_children.add(norm_child_id)
                    children.append(child_id.strip())
            # Ignore unknown attributes instead of raising errors
            else:
                continue
        requirements.append(
            Requirement(req_id, description, critical, children, completed)
        )
    return requirements


def _validate_no_cycles(requirements: list[Requirement]) -> None:
    """Raise ValueError if a circular dependency is detected in the requirements graph."""
    adj: dict[str, list[str]] = {req.req_id: req.children for req in requirements}
    visiting: set[str] = set()  # For the current traversal path
    visited: set[str] = set()  # For all nodes ever visited

    def visit(req_id: str, path: list[str]) -> None:
        visiting.add(req_id)
        path.append(req_id)
        for child_id in adj.get(req_id, []):
            if child_id in visiting:
                path.append(child_id)
                raise ValueError(
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


def _validate_completed_children(requirements: list[Requirement]) -> None:
    """Raise ValueError if any completed requirement has incomplete children (REQ-CORE-7)."""
    req_dict = {r.req_id: r for r in requirements}
    errors: list[tuple[str, str]] = []
    for req in requirements:
        if req.completed:
            for child_id in req.children:
                child = req_dict.get(child_id)
                if child is not None and not child.completed:
                    errors.append((req.req_id, child_id))
    if errors:
        msg = "The following requirements are marked as completed but have incomplete children:\n"
        for parent_id, child_id in errors:
            msg += f"  - {parent_id} (incomplete child: {child_id})\n"
        raise ValueError(msg)


def _validate_duplicate_ids(parsed_requirements: list[ParsedRequirement]) -> None:
    """Raise ValueError if duplicate requirement IDs are found across files."""
    seen_ids: dict[str, Path] = {}
    for parsed_req in parsed_requirements:
        req_id = parsed_req.requirement.req_id
        source_file = parsed_req.source_file
        if req_id in seen_ids:
            first_file = seen_ids[req_id]
            raise ValueError(
                f"Duplicate requirement ID '{req_id}' found in '{source_file}'. "
                f"First defined in '{first_file}'."
            )
        seen_ids[req_id] = source_file


# =============================================================================
# PLUGIN-ORIENTED API
# =============================================================================


def parse_requirements_from_files(
    file_data: list[tuple[str, str]],
) -> list[ParsedRequirement]:
    """Parse requirements from a list of (file_path, content) tuples.

    Args:
        file_data: List of (file_path, content_string) tuples.

    Returns:
        List of ParsedRequirement objects with file associations.

    Raises:
        ValueError: If parsing or validation fails.

    """
    all_parsed_reqs: list[ParsedRequirement] = []

    for file_path, content in file_data:
        try:
            reqs = _parse_requirements_from_markdown(content)
            all_parsed_reqs.extend(
                [
                    ParsedRequirement(requirement=req, source_file=Path(str(file_path)))
                    for req in reqs
                ]
            )
        except ValueError as e:
            raise ValueError(f"Error in file '{file_path}': {e}") from e

    return all_parsed_reqs


def validate_requirements(parsed_requirements: list[ParsedRequirement]) -> None:
    """Run all validation checks on parsed requirements.

    Args:
        parsed_requirements: List of ParsedRequirement objects to validate.

    Raises:
        ValueError: If any validation fails.

    """
    if not parsed_requirements:
        return

    # Extract just the requirements for validation functions
    requirements = [pr.requirement for pr in parsed_requirements]

    # Run all validations
    _validate_duplicate_ids(parsed_requirements)
    _validate_no_cycles(requirements)
    _validate_completed_children(requirements)


def generate_requirement_page_content(parsed_req: ParsedRequirement) -> str:
    """Generate Markdown content for a single requirement page.

    Args:
        parsed_req: ParsedRequirement object with requirement and source file.

    Returns:
        Markdown content for the requirement page.

    """
    req = parsed_req.requirement
    source_file = parsed_req.source_file

    lines = []
    lines.append(f"# {req.req_id}")
    lines.append("")
    lines.append(f"{req.description}")
    lines.append("")

    # Add status indicators
    if req.critical:
        lines.append("⚠️ **Critical requirement**")
        lines.append("")
    if req.completed:
        lines.append("✅ **Completed**")
        lines.append("")

    # Add children if any
    if req.children:
        lines.append("## Children")
        lines.append("")
        for child_id in req.children:
            lines.append(f"- [{child_id}](./{child_id}.md)")
        lines.append("")

    # Add source file link
    lines.append(f"---")
    lines.append(f"*Source: [{source_file}](../{source_file}#{req.req_id})*")

    return "\n".join(lines)


def generate_requirement_index_content(
    parsed_requirements: list[ParsedRequirement],
) -> str:
    """Generate Markdown content for the requirements index page.

    Args:
        parsed_requirements: List of all ParsedRequirement objects.

    Returns:
        Markdown content for the index page.

    """
    lines = []
    lines.append("# Requirements Index")
    lines.append("")

    # Group by file
    file_groups: dict[Path, list[ParsedRequirement]] = {}
    for pr in parsed_requirements:
        file_groups.setdefault(pr.source_file, []).append(pr)

    for file_path in sorted(file_groups.keys()):
        lines.append(f"## {file_path}")
        lines.append("")

        for pr in sorted(file_groups[file_path], key=lambda pr: pr.requirement.req_id):
            req = pr.requirement
            status_emoji = "✅" if req.completed else "⏳"
            critical_indicator = "⚠️ " if req.critical else ""

            lines.append(
                f"- {status_emoji} {critical_indicator}[{req.req_id}](./{req.req_id}.md): {req.description}"
            )
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def _progress_bar(completed: int, total: int, width: int = 20) -> str:
    """Generate a Unicode progress bar string."""
    if total <= 0:
        return "`[" + (" " * width) + "]`"
    # Unicode 1/8 blocks: ▏▎▍▌▋▊▉█
    blocks = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    frac = min(max(completed / total, 0), 1)  # Clamp between 0 and 1
    if width == 1:
        # For width 1, show full block if at least half complete
        return f"`[{'█' if frac >= 0.5 else ' '}]`"
    total_blocks = frac * width
    full_blocks = int(total_blocks)
    partial_block_frac = total_blocks - full_blocks
    partial_block_idx = int(round(partial_block_frac * 8))
    bar = "█" * full_blocks
    if full_blocks < width:
        if partial_block_idx > 0 and partial_block_idx < 8:
            bar += blocks[partial_block_idx]
            bar += " " * (width - full_blocks - 1)
        else:
            bar += " " * (width - full_blocks)
    return f"`[{bar}]`"


def _diff_requirements(
    old: list[Requirement], new: list[Requirement]
) -> dict[DiffType, list[Requirement]]:
    """Compare two lists of requirements and return a diff dict."""
    old_dict: dict[str, Requirement] = {r.req_id: r for r in old}
    new_dict: dict[str, Requirement] = {r.req_id: r for r in new}
    added: list[Requirement] = [
        new_dict[rid] for rid in new_dict if rid not in old_dict
    ]
    removed: list[Requirement] = [
        old_dict[rid] for rid in old_dict if rid not in new_dict
    ]
    changed: list[Requirement] = [
        new_dict[rid]
        for rid in new_dict
        if rid in old_dict and new_dict[rid] != old_dict[rid]
    ]
    return {DiffType.ADDED: added, DiffType.REMOVED: removed, DiffType.CHANGED: changed}
