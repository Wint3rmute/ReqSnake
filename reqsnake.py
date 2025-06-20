#! /usr/bin/env python3
"""reqsnake.py - Dead-simple Python script for tracking requirements in Markdown documents.

This module provides both a CLI and a Python API for managing requirements defined in Markdown files.
"""
import re
from typing import Optional, Any, Set, NamedTuple, Tuple, Dict
from dataclasses import dataclass, field, asdict
from pathlib import Path
import argparse
import json
import sys
from enum import Enum, auto
import tempfile


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
        lines = [f"{self.req_id}: {self.description}"]
        if self.critical:
            lines.append("  - critical")
        if self.children:
            lines.append(f"  - children: {', '.join(self.children)}")
        if self.completed:
            lines.append("  - completed")
        return "\n".join(lines)


class InitResult(NamedTuple):
    """Result of the api_init function: scanned files and requirements."""

    scanned_files: list[Path]
    requirements: list[Requirement]


class LockResult(NamedTuple):
    """Result of api_lock: scanned files and requirements."""

    scanned_files: list[Path]
    requirements: list[Requirement]


class DiffType(Enum):
    """Enum representing types of requirement diffs: added, removed, or changed."""

    ADDED = auto()
    REMOVED = auto()
    CHANGED = auto()

    def __str__(self) -> str:
        """Return the lowercase name of the DiffType enum member."""
        return self.name.lower()


class CheckResult(NamedTuple):
    """Result of api_check: scanned files and diff dict."""

    scanned_files: list[Path]
    diff: dict[DiffType, list[Requirement]]


@dataclass(frozen=True)
class ParsedRequirement:
    """A requirement and the path to the file it was parsed from."""

    requirement: Requirement
    source_file: Path


class StatusResult(NamedTuple):
    """Result of api_status: requirements with file associations and status summary."""

    requirements: list[ParsedRequirement]
    total_count: int
    completed_count: int
    critical_count: int
    critical_completed_count: int


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
    seen_ids: Set[str] = set()
    for block in BLOCKQUOTE_PATTERN.findall(md_text):
        # Only consider lines starting with '>' (REQ-PARSER-12)
        lines = [line[2:].strip() for line in block.split("\n") if line.startswith(">")]
        # Remove empty lines (REQ-PARSER-7)
        lines = [line for line in lines if line.strip()]
        # Skip blockquotes with only an ID or only a description (REQ-PARSER-6)
        if len(lines) < 2:
            continue
        req_id = lines[0]
        # Enforce REQ-CORE-6: ID must be <STRING>-<NUMBER> and ASCII only
        if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*-\d+$", req_id):
            raise ValueError(
                f"Requirement ID '{req_id}' does not match the required format '<STRING>-<NUMBER>' (REQ-CORE-6)"
            )
        # Additional check: ensure all characters are ASCII
        if not all(ord(c) < 128 for c in req_id):
            raise ValueError(
                f"Requirement ID '{req_id}' contains non-ASCII characters, which are not allowed. (REQ-CORE-6)"
            )
        if req_id in seen_ids:
            raise ValueError(f"Duplicate requirement ID found: {req_id}")
        seen_ids.add(req_id)
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
            # Raise errors on unknown attributes (REQ-PARSER-10)
            else:
                raise ValueError(
                    f"Unknown atttribute '{norm}' of requirement '{req_id}'"
                )
        requirements.append(
            Requirement(req_id, description, critical, children, completed)
        )
    return requirements


def _read_requirementsignore(root_dir: Path) -> list[tuple[str, bool]]:
    """Read .requirementsignore file and return a list of (pattern, is_negation) tuples.

    Patterns follow .gitignore glob rules. Lines starting with '!' are negations.
    """
    ignore_file = root_dir / ".requirementsignore"
    patterns: list[tuple[str, bool]] = []
    if ignore_file.is_file():
        for line in ignore_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            is_negation = line.startswith("!")
            pattern = line[1:] if is_negation else line
            patterns.append((pattern, is_negation))
    return patterns


def _is_ignored_by_patterns(rel_path: str, patterns: list[tuple[str, bool]]) -> bool:
    """Return True if rel_path is ignored by the given .gitignore-style patterns."""
    from pathlib import PurePath

    path = PurePath(rel_path)
    ignored = False
    for pattern, is_negation in patterns:
        # .gitignore patterns are matched against the path as posix string
        if path.match(pattern):
            ignored = not is_negation
    return ignored


def _find_markdown_files(root_dir: Path) -> list[Path]:
    """Return all Markdown (.md) files in the given directory recursively, respecting .requirementsignore as .gitignore-style globs."""
    ignore_patterns = _read_requirementsignore(root_dir)
    files = []
    for p in root_dir.rglob("*.md"):
        if not p.is_file():
            continue
        rel_path = str(p.relative_to(root_dir))
        if _is_ignored_by_patterns(rel_path, ignore_patterns):
            continue
        files.append(p)
    return files


def _load_lockfile(lockfile_path: Path) -> list[Requirement]:
    """Load requirements from a JSON lockfile."""
    with lockfile_path.open("r", encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.load(f)
    return [Requirement.from_dict(item) for item in data]


def _save_lockfile(lockfile_path: Path, requirements: list[Requirement]) -> None:
    """Save requirements to a JSON lockfile atomically."""
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=lockfile_path.parent, encoding="utf-8"
    ) as tf:
        json.dump([asdict(req) for req in requirements], tf, indent=2)
        tempname = tf.name
    Path(tempname).replace(lockfile_path)


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


def _print_scanned_files(md_files: list[Path]) -> None:
    """Print the Markdown files being scanned."""
    print("🔍 Scanning the following Markdown files:")
    for md_file in md_files:
        print(f"  {md_file}")


def _print_diff_section(
    diff_type: str, requirements: list[Requirement], symbol: str
) -> None:
    """Print a section of the diff with a given symbol and requirements list."""
    if requirements:
        print(f"{symbol} {diff_type} requirements:")
        for req in requirements:
            for i, line in enumerate(req.to_pretty_string().split("\n")):
                prefix = f"  {symbol} " if i == 0 else "    "
                print(f"{prefix}{line}")


def _print_status_summary(status_result: StatusResult) -> None:
    """Print a summary of requirement completion status."""
    total = status_result.total_count
    completed = status_result.completed_count
    critical = status_result.critical_count
    critical_completed = status_result.critical_completed_count

    if total == 0:
        print("📊 No requirements found.")
        return

    completion_percentage = (completed / total) * 100 if total > 0 else 0
    critical_completion_percentage = (
        (critical_completed / critical) * 100 if critical > 0 else 0
    )

    print("📊 Requirements Status Summary:")
    print(f"  Total requirements: {total}")
    print(f"  Completed: {completed}/{total} ({completion_percentage:.1f}%)")
    print(f"  Critical requirements: {critical}")
    print(
        f"  Critical completed: {critical_completed}/{critical} ({critical_completion_percentage:.1f}%)"
    )
    print()


def _print_status_by_file(status_result: StatusResult) -> None:
    """Print requirements grouped by source file with completion status."""
    # Group requirements by file
    file_groups: dict[Path, list[ParsedRequirement]] = {}
    for pr in status_result.requirements:
        file_groups.setdefault(pr.source_file, []).append(pr)

    print("📁 Requirements by File:")
    for file_path in sorted(file_groups.keys()):
        reqs = file_groups[file_path]
        completed_count = sum(1 for pr in reqs if pr.requirement.completed)
        total_count = len(reqs)
        completion_percentage = (
            (completed_count / total_count) * 100 if total_count > 0 else 0
        )

        status_emoji = (
            "✅"
            if completed_count == total_count
            else "🔄" if completed_count > 0 else "⏳"
        )
        print(
            f"  {status_emoji} {file_path} ({completed_count}/{total_count} completed, {completion_percentage:.1f}%)"
        )

        for pr in reqs:
            req = pr.requirement
            req_status = "✅" if req.completed else "⏳"
            critical_indicator = "⚠️ " if req.critical else "  "
            print(
                f"    {req_status} {critical_indicator}{req.req_id}: {req.description}"
            )
    print()


def _print_hierarchical_status(status_result: StatusResult) -> None:
    """Print hierarchical status showing parent-child relationships."""
    # Create a mapping from requirement ID to requirement
    req_dict: dict[str, ParsedRequirement] = {
        pr.requirement.req_id: pr for pr in status_result.requirements
    }

    # Find root requirements (those that are not children of any other requirement)
    all_children: set[str] = set()
    for pr in status_result.requirements:
        all_children.update(pr.requirement.children)

    root_reqs = [
        pr
        for pr in status_result.requirements
        if pr.requirement.req_id not in all_children
    ]

    print("🌳 Hierarchical Status:")

    def print_requirement_tree(pr: ParsedRequirement, level: int = 0) -> None:
        """Recursively print a requirement and its children."""
        req = pr.requirement
        indent = "  " * level
        status_emoji = "✅" if req.completed else "⏳"
        critical_indicator = "⚠️ " if req.critical else "  "

        print(
            f"{indent}{status_emoji} {critical_indicator}{req.req_id}: {req.description}"
        )

        # Print children
        for child_id in req.children:
            if child_id in req_dict:
                print_requirement_tree(req_dict[child_id], level + 1)
            else:
                print(f"{indent}  ❓ {child_id}: (not found)")

    for root_pr in sorted(root_reqs, key=lambda pr: pr.requirement.req_id):
        print_requirement_tree(root_pr)


def _validate_completed_children(requirements: list[Requirement]) -> None:
    """Raise ValueError if any completed requirement has incomplete children (REQ-CORE-7)."""
    req_dict = {r.req_id: r for r in requirements}
    # Build parent-to-children mapping
    parent_to_children: dict[str, list[Requirement]] = {}
    for req in requirements:
        for parent_id in req.children:
            parent_to_children.setdefault(parent_id, []).append(req)
    errors: list[tuple[str, str]] = []
    for req in requirements:
        if req.completed:
            for child in parent_to_children.get(req.req_id, []):
                if not child.completed:
                    errors.append((req.req_id, child.req_id))
    if errors:
        msg = "The following requirements are marked as completed but have incomplete children:\n"
        for parent_id, child_id in errors:
            msg += f"  - {parent_id} (incomplete child: {child_id})\n"
        raise ValueError(msg)


def _validate_no_cycles(requirements: list[Requirement]) -> None:
    """Raise ValueError if any circular child relationship is detected (REQ-PARSER-15)."""
    req_dict = {r.req_id: r for r in requirements}
    visited_global = set()

    def visit(req_id: str, path: list[str]) -> None:
        if req_id in path:
            cycle = path[path.index(req_id) :] + [req_id]
            raise ValueError(f"Circular dependency detected: {' -> '.join(cycle)}")
        if req_id in visited_global:
            return
        path.append(req_id)
        for parent_id in req_dict[req_id].children:
            if parent_id in req_dict:
                visit(parent_id, path)
        path.pop()
        visited_global.add(req_id)

    for req in requirements:
        visit(req.req_id, [])


# --- Python API ---
def reqsnake_init(directory: Optional[str] = None) -> InitResult:
    """Scan Markdown files and create requirements.lock."""
    dir_path = Path(directory) if directory else Path.cwd()
    md_files = _find_markdown_files(dir_path)
    requirements: list[Requirement] = []
    for md_file in md_files:
        with md_file.open("r", encoding="utf-8") as f:
            md_text = f.read()
        reqs = _parse_requirements_from_markdown(md_text)
        requirements.extend(reqs)
    _validate_no_cycles(requirements)
    _validate_completed_children(requirements)
    lockfile_path = dir_path / "requirements.lock"
    _save_lockfile(lockfile_path, requirements)
    return InitResult(md_files, requirements)


def reqsnake_check(
    directory: Optional[str] = None,
) -> Tuple[CheckResult, Dict[str, Path]]:
    """Scan Markdown files and compare to requirements.lock, returning file info for each requirement."""
    dir_path = Path(directory) if directory else Path.cwd()
    lockfile_path = dir_path / "requirements.lock"
    if not lockfile_path.is_file():
        raise FileNotFoundError("requirements.lock not found. Run 'init' first.")
    md_files = _find_markdown_files(dir_path)
    parsed_reqs: list[ParsedRequirement] = []
    for md_file in md_files:
        parsed_reqs.extend(_parse_requirements_from_file(md_file))
    requirements = [pr.requirement for pr in parsed_reqs]
    _validate_completed_children(requirements)
    _validate_no_cycles(requirements)
    lock_reqs = _load_lockfile(lockfile_path)
    diff = _diff_requirements(lock_reqs, requirements)
    req_id_to_file: Dict[str, Path] = {
        pr.requirement.req_id: pr.source_file for pr in parsed_reqs
    }
    return CheckResult(md_files, diff), req_id_to_file


def reqsnake_lock(directory: Optional[str] = None) -> LockResult:
    """Scan Markdown files and update requirements.lock."""
    dir_path = Path(directory) if directory else Path.cwd()
    md_files = _find_markdown_files(dir_path)
    requirements: list[Requirement] = []
    for md_file in md_files:
        with md_file.open("r", encoding="utf-8") as f:
            md_text = f.read()
        reqs = _parse_requirements_from_markdown(md_text)
        requirements.extend(reqs)
    _validate_completed_children(requirements)
    _validate_no_cycles(requirements)
    lockfile_path = dir_path / "requirements.lock"
    # Check if lockfile exists and is up-to-date
    lockfile_exists = lockfile_path.is_file()
    up_to_date = False
    if lockfile_exists:
        try:
            old_reqs = _load_lockfile(lockfile_path)
            up_to_date = old_reqs == requirements
        except Exception:
            up_to_date = False
    _print_scanned_files(md_files)
    if up_to_date:
        print("👍 requirements.lock is already up-to-date.")
    else:
        _save_lockfile(lockfile_path, requirements)
        print(f"✅ requirements.lock updated with {len(requirements)} requirements.")
    return LockResult(md_files, requirements)


def reqsnake_status(directory: Optional[str] = None) -> StatusResult:
    """Scan Markdown files and return status information about requirements.

    Args:
        directory: Optional directory path. Defaults to current working directory.

    Returns:
        StatusResult: Requirements with file associations and status summary.

    Raises:
        FileNotFoundError: If requirements.lock not found.

    """
    dir_path = Path(directory) if directory else Path.cwd()
    lockfile_path = dir_path / "requirements.lock"
    if not lockfile_path.is_file():
        raise FileNotFoundError("requirements.lock not found. Run 'init' first.")

    # Load requirements from lockfile
    lock_reqs = _load_lockfile(lockfile_path)
    _validate_completed_children(lock_reqs)

    # Get file associations for requirements
    md_files = _find_markdown_files(dir_path)
    parsed_reqs: list[ParsedRequirement] = []
    for md_file in md_files:
        parsed_reqs.extend(_parse_requirements_from_file(md_file))

    # Create a mapping from requirement ID to ParsedRequirement
    req_id_to_parsed: dict[str, ParsedRequirement] = {}
    for pr in parsed_reqs:
        req_id_to_parsed[pr.requirement.req_id] = pr

    # Create ParsedRequirement list for lockfile requirements
    status_reqs: list[ParsedRequirement] = []
    for req in lock_reqs:
        # Find the source file for this requirement
        source_file = req_id_to_parsed.get(
            req.req_id, ParsedRequirement(req, Path("unknown.md"))
        ).source_file
        status_reqs.append(ParsedRequirement(req, source_file))

    # Calculate statistics
    total_count = len(status_reqs)
    completed_count = sum(1 for pr in status_reqs if pr.requirement.completed)
    critical_count = sum(1 for pr in status_reqs if pr.requirement.critical)
    critical_completed_count = sum(
        1 for pr in status_reqs if pr.requirement.critical and pr.requirement.completed
    )

    return StatusResult(
        requirements=status_reqs,
        total_count=total_count,
        completed_count=completed_count,
        critical_count=critical_count,
        critical_completed_count=critical_completed_count,
    )


def _parse_requirements_from_file(md_file: Path) -> list[ParsedRequirement]:
    """Parse requirements from a Markdown file, returning ParsedRequirement with file path."""
    with md_file.open("r", encoding="utf-8") as f:
        md_text = f.read()
    reqs = _parse_requirements_from_markdown(md_text)
    return [ParsedRequirement(r, md_file) for r in reqs]


def _generate_status_markdown(status_result: StatusResult) -> str:
    """Generate a Markdown report of requirements status from a StatusResult."""
    lines = []
    # Summary
    total = status_result.total_count
    completed = status_result.completed_count
    critical = status_result.critical_count
    critical_completed = status_result.critical_completed_count
    completion_percentage = (completed / total) * 100 if total > 0 else 0
    critical_completion_percentage = (
        (critical_completed / critical) * 100 if critical > 0 else 0
    )
    lines.append("# Requirements Status Report\n")
    lines.append("## Summary\n")
    lines.append(f"- **Total requirements:** {total}")
    lines.append(f"- **Completed:** {completed}/{total} ({completion_percentage:.1f}%)")
    lines.append(f"- **Critical requirements:** {critical}")
    lines.append(
        f"- **Critical completed:** {critical_completed}/{critical} ({critical_completion_percentage:.1f}%)\n"
    )

    # By file
    lines.append("## Requirements by File\n")
    file_groups: dict[Path, list[ParsedRequirement]] = {}
    for pr in status_result.requirements:
        file_groups.setdefault(pr.source_file, []).append(pr)
    for file_path in sorted(file_groups.keys()):
        reqs = file_groups[file_path]
        completed_count = sum(1 for pr in reqs if pr.requirement.completed)
        total_count = len(reqs)
        completion_percentage = (
            (completed_count / total_count) * 100 if total_count > 0 else 0
        )
        lines.append(f"### {file_path}")
        lines.append(
            f"- **Completed:** {completed_count}/{total_count} ({completion_percentage:.1f}%)\n"
        )
        for pr in reqs:
            req = pr.requirement
            status_emoji = "✅" if req.completed else "⏳"
            critical_indicator = "⚠️ " if req.critical else ""
            children_str = (
                f" _(children: {', '.join(req.children)})_" if req.children else ""
            )
            lines.append(
                f"- {status_emoji} {critical_indicator}**{req.req_id}**: {req.description}{children_str}"
            )
        lines.append("")

    # Hierarchical
    lines.append("## Hierarchical Status\n")
    req_dict: dict[str, ParsedRequirement] = {
        pr.requirement.req_id: pr for pr in status_result.requirements
    }
    all_children: set[str] = set()
    for pr in status_result.requirements:
        all_children.update(pr.requirement.children)
    root_reqs = [
        pr
        for pr in status_result.requirements
        if pr.requirement.req_id not in all_children
    ]

    def print_tree(pr: ParsedRequirement, level: int = 0) -> None:
        req = pr.requirement
        indent = "  " * level
        status_emoji = "✅" if req.completed else "⏳"
        critical_indicator = "⚠️ " if req.critical else ""
        children_str = (
            f" _(children: {', '.join(req.children)})_" if req.children else ""
        )
        lines.append(
            f"{indent}- {status_emoji} {critical_indicator}**{req.req_id}**: {req.description}{children_str}"
        )
        for child_id in req.children:
            if child_id in req_dict:
                print_tree(req_dict[child_id], level + 1)
            else:
                lines.append(f"{indent}  - ❓ **{child_id}**: (not found)")

    for root_pr in sorted(root_reqs, key=lambda pr: pr.requirement.req_id):
        print_tree(root_pr)
    lines.append("")
    return "\n".join(lines)


def _generate_graphviz(lockfile_path: Path, output_path: Path) -> None:
    """Generate a Graphviz dot file representing the requirements hierarchy."""
    requirements = _load_lockfile(lockfile_path)
    req_dict = {r.req_id: r for r in requirements}
    lines = ["digraph requirements {"]
    # Add nodes
    for req in requirements:
        label = req.req_id.replace('"', "")
        description_sanitized = req.description.replace('"', "")[:20] + "..."
        node_label = f"{label}"
        attrs = []
        if req.critical:
            attrs.append("style=filled fillcolor=red")
        if req.completed:
            attrs.append("style=filled fillcolor=lightgreen")
        attr_str = (",".join(attrs)) if attrs else ""
        lines.append(
            f'    "{req.req_id}" [label="{node_label} \n {description_sanitized} "{(", "+attr_str) if attr_str else ""}];'
        )
    # Add edges
    for req in requirements:
        for parent_id in req.children:
            if parent_id in req_dict:
                lines.append(f'    "{parent_id}" -> "{req.req_id}";')
    lines.append("}")
    output_path.write_text("\n".join(lines), encoding="utf-8")


# --- CLI Entrypoint ---
def cli_init(args: argparse.Namespace) -> None:
    """Handle the 'init' CLI command."""
    init_result = reqsnake_init()
    _print_scanned_files(init_result.scanned_files)
    print(
        f"✅ Initialized requirements.lock with {len(init_result.requirements)} requirements."
    )


def cli_check(args: argparse.Namespace) -> None:
    """Handle the 'check' CLI command."""
    try:
        check_result, req_id_to_file = reqsnake_check()
    except FileNotFoundError:
        print("❌ requirements.lock not found. Run 'reqsnake.py init' first.")
        sys.exit(1)
    _print_scanned_files(check_result.scanned_files)
    diff = check_result.diff

    def print_diff_with_file(
        diff_type: str, requirements: list[Requirement], symbol: str
    ) -> None:
        if requirements:
            print(f"{symbol} {diff_type} requirements:")
            for req in requirements:
                file_path = req_id_to_file.get(req.req_id, "<unknown file>")
                for i, line in enumerate(req.to_pretty_string().split("\n")):
                    prefix = f"  {symbol} " if i == 0 else "    "
                    if i == 0:
                        print(f"{prefix}{line}  [file: {file_path}]")
                    else:
                        print(f"{prefix}{line}")

    if (
        not diff[DiffType.ADDED]
        and not diff[DiffType.REMOVED]
        and not diff[DiffType.CHANGED]
    ):
        print("👍 requirements.lock is up-to-date.")
    else:
        print_diff_with_file("Added", diff[DiffType.ADDED], "+")
        print_diff_with_file("Removed", diff[DiffType.REMOVED], "-")
        print_diff_with_file("Changed", diff[DiffType.CHANGED], "*")
        sys.exit(2)


def cli_lock(args: argparse.Namespace) -> None:
    """Handle the 'lock' CLI command."""
    dir_path = Path.cwd()
    lockfile_path = dir_path / "requirements.lock"
    # Gather new requirements
    md_files = _find_markdown_files(dir_path)
    requirements: list[Requirement] = []
    for md_file in md_files:
        with md_file.open("r", encoding="utf-8") as f:
            md_text = f.read()
        reqs = _parse_requirements_from_markdown(md_text)
        requirements.extend(reqs)
    _validate_completed_children(requirements)
    _validate_no_cycles(requirements)
    # Check if lockfile exists and is up-to-date
    lockfile_exists = lockfile_path.is_file()
    up_to_date = False
    if lockfile_exists:
        try:
            old_reqs = _load_lockfile(lockfile_path)
            up_to_date = old_reqs == requirements
        except (FileNotFoundError, json.JSONDecodeError):
            up_to_date = False
    _print_scanned_files(md_files)
    if up_to_date:
        print("👍 requirements.lock is already up-to-date.")
    else:
        _save_lockfile(lockfile_path, requirements)
        print(f"✅ requirements.lock updated with {len(requirements)} requirements.")


def cli_status(args: argparse.Namespace) -> None:
    """Handle the 'status' CLI command."""
    try:
        status_result = reqsnake_status()
    except FileNotFoundError:
        print("❌ requirements.lock not found. Run 'reqsnake.py init' first.")
        sys.exit(1)

    _print_status_summary(status_result)
    _print_status_by_file(status_result)
    _print_hierarchical_status(status_result)


def cli_status_md(args: argparse.Namespace) -> None:
    """Handle the 'status-md' CLI command."""
    try:
        status_result = reqsnake_status()
    except FileNotFoundError:
        print("❌ requirements.lock not found. Run 'reqsnake.py init' first.")
        sys.exit(1)
    output_path = (
        Path(args.output)
        if hasattr(args, "output") and args.output
        else Path("requirements-status.md")
    )
    md = _generate_status_markdown(status_result)
    output_path.write_text(md, encoding="utf-8")
    print(f"✅ Requirements status written to {output_path}")


def cli_visual_dot(args: argparse.Namespace) -> None:
    """Handle the 'visual-dot' CLI command."""
    dir_path = Path.cwd()
    lockfile_path = dir_path / "requirements.lock"
    if not lockfile_path.is_file():
        print("❌ requirements.lock not found. Run 'reqsnake.py init' first.")
        sys.exit(1)
    output_path = (
        Path(args.output)
        if hasattr(args, "output") and args.output
        else Path("requirements.gv")
    )
    _generate_graphviz(lockfile_path, output_path)
    print(f"✅ Requirements Graphviz dot file written to {output_path}")


def main() -> None:
    """Parse arguments and run the appropriate CLI command for reqsnake.py. Supports shorthands for commands."""
    parser = argparse.ArgumentParser(
        description="reqsnake.py - Markdown requirements tracker"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'init' command
    p_init = subparsers.add_parser(
        "init",
        help="Initialize reqsnake.py in the current directory and generate requirements.lock.",
        aliases=["i"],
    )
    p_init.set_defaults(func=cli_init)

    # 'check' command
    p_check = subparsers.add_parser(
        "check",
        help="Check if requirements.lock is up-to-date with Markdown requirements.",
        aliases=["c"],
    )
    p_check.set_defaults(func=cli_check)

    # 'lock' command
    p_lock = subparsers.add_parser(
        "lock",
        help="Update requirements.lock to match current Markdown requirements.",
        aliases=["l"],
    )
    p_lock.set_defaults(func=cli_lock)

    # 'status' command
    p_status = subparsers.add_parser(
        "status",
        help="Get status information about requirements.",
        aliases=["s"],
    )
    p_status.set_defaults(func=cli_status)

    # 'status-md' command
    p_status_md = subparsers.add_parser(
        "status-md",
        help="Generate a Markdown file with the status of all requirements (from requirements.lock).",
        aliases=["sm"],
    )
    p_status_md.add_argument(
        "-o",
        "--output",
        default="requirements-status.md",
        help="Output Markdown file (default: requirements-status.md)",
    )
    p_status_md.set_defaults(func=cli_status_md)

    # 'visual-dot' command
    p_visual_dot = subparsers.add_parser(
        "visual-dot",
        help="Generate a Graphviz dot file representing the requirements hierarchy (from requirements.lock).",
        aliases=["v"],
    )
    p_visual_dot.add_argument(
        "-o",
        "--output",
        default="requirements.gv",
        help="Output dot file (default: requirements.gv)",
    )
    p_visual_dot.set_defaults(func=cli_visual_dot)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
