#! /usr/bin/env python3
"""require.py - Dead-simple Python script for tracking requirements in Markdown documents.

This module provides both a CLI and a Python API for managing requirements defined in Markdown files.
"""
import re
from typing import Optional, Any, Set, NamedTuple
from dataclasses import dataclass, field
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

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the requirement for JSON serialization."""
        return {
            "id": self.req_id,
            "description": self.description,
            "critical": self.critical,
            "children": self.children,
            "completed": self.completed,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Requirement":
        """Create a Requirement from a dictionary."""
        return Requirement(
            req_id=data["id"],
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
    """Result of api_init: scanned files and requirements."""

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


class LockResult(NamedTuple):
    """Result of api_lock: scanned files and requirements."""

    scanned_files: list[Path]
    requirements: list[Requirement]


# Regex for blockquotes: matches contiguous blockquote lines
BLOCKQUOTE_PATTERN = re.compile(
    r"(^> .*(?:\n>.*)*)",  # Match a block starting with '> ' and all following '> ...' lines
    re.MULTILINE,
)


def parse_requirements_from_markdown(md_text: str) -> list[Requirement]:
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
        if req_id in seen_ids:
            raise ValueError(f"Duplicate requirement ID found: {req_id}")
        seen_ids.add(req_id)
        description = lines[1]
        critical = False
        completed = False
        children: list[str] = []
        for line in lines[2:]:
            norm = line.strip().lower()
            if norm == "critical":
                critical = True
            elif norm == "completed":
                completed = True
            elif norm.startswith("child:"):
                child_id = line[6:].strip()
                if child_id and child_id not in children:
                    children.append(child_id)
            # Ignore unknown attributes (REQ-PARSER-10)
        requirements.append(
            Requirement(req_id, description, critical, children, completed)
        )
    return requirements


def find_markdown_files(root_dir: Path) -> list[Path]:
    """Return all Markdown (.md) files in the given directory recursively."""
    return [p for p in root_dir.rglob("*.md") if p.is_file()]


def load_lockfile(lockfile_path: Path) -> list[Requirement]:
    """Load requirements from a JSON lockfile."""
    with lockfile_path.open("r", encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.load(f)
    return [Requirement.from_dict(item) for item in data]


def save_lockfile(lockfile_path: Path, requirements: list[Requirement]) -> None:
    """Save requirements to a JSON lockfile atomically."""
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=lockfile_path.parent, encoding="utf-8"
    ) as tf:
        json.dump([req.to_dict() for req in requirements], tf, indent=2)
        tempname = tf.name
    Path(tempname).replace(lockfile_path)


def diff_requirements(
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


def print_scanned_files(md_files: list[Path]) -> None:
    """Print the Markdown files being scanned."""
    print("🔍 Scanning the following Markdown files:")
    for md_file in md_files:
        print(f"  {md_file}")


def print_diff_section(
    diff_type: str, requirements: list[Requirement], symbol: str
) -> None:
    """Print a section of the diff with a given symbol and requirements list."""
    if requirements:
        print(f"{symbol} {diff_type} requirements:")
        for req in requirements:
            for i, line in enumerate(req.to_pretty_string().split("\n")):
                prefix = f"  {symbol} " if i == 0 else "    "
                print(f"{prefix}{line}")


# --- Python API ---
def api_init(directory: Optional[str] = None) -> InitResult:
    """Scan Markdown files and create requirements.lock."""
    dir_path = Path(directory) if directory else Path.cwd()
    md_files = find_markdown_files(dir_path)
    requirements: list[Requirement] = []
    for md_file in md_files:
        with md_file.open("r", encoding="utf-8") as f:
            md_text = f.read()
        reqs = parse_requirements_from_markdown(md_text)
        requirements.extend(reqs)
    lockfile_path = dir_path / "requirements.lock"
    save_lockfile(lockfile_path, requirements)
    return InitResult(md_files, requirements)


def api_check(directory: Optional[str] = None) -> CheckResult:
    """Scan Markdown files and compare to requirements.lock."""
    dir_path = Path(directory) if directory else Path.cwd()
    lockfile_path = dir_path / "requirements.lock"
    if not lockfile_path.is_file():
        raise FileNotFoundError("requirements.lock not found. Run 'init' first.")
    md_files = find_markdown_files(dir_path)
    requirements: list[Requirement] = []
    for md_file in md_files:
        with md_file.open("r", encoding="utf-8") as f:
            md_text = f.read()
        reqs = parse_requirements_from_markdown(md_text)
        requirements.extend(reqs)
    lock_reqs = load_lockfile(lockfile_path)
    diff = diff_requirements(lock_reqs, requirements)
    return CheckResult(md_files, diff)


def api_lock(directory: Optional[str] = None) -> LockResult:
    """Scan Markdown files and update requirements.lock."""
    dir_path = Path(directory) if directory else Path.cwd()
    md_files = find_markdown_files(dir_path)
    requirements: list[Requirement] = []
    for md_file in md_files:
        with md_file.open("r", encoding="utf-8") as f:
            md_text = f.read()
        reqs = parse_requirements_from_markdown(md_text)
        requirements.extend(reqs)
    lockfile_path = dir_path / "requirements.lock"
    # Check if lockfile exists and is up-to-date
    lockfile_exists = lockfile_path.is_file()
    up_to_date = False
    if lockfile_exists:
        try:
            old_reqs = load_lockfile(lockfile_path)
            up_to_date = old_reqs == requirements
        except Exception:
            up_to_date = False
    print_scanned_files(md_files)
    if up_to_date:
        print("👍 requirements.lock is already up-to-date.")
    else:
        save_lockfile(lockfile_path, requirements)
        print(f"✅ requirements.lock updated with {len(requirements)} requirements.")
    return LockResult(md_files, requirements)


# --- CLI Entrypoint ---
def cli_init(args):
    """Handle the 'init' CLI command."""
    init_result = api_init()
    print_scanned_files(init_result.scanned_files)
    print(
        f"✅ Initialized requirements.lock with {len(init_result.requirements)} requirements."
    )


def cli_check(args):
    """Handle the 'check' CLI command."""
    try:
        check_result = api_check()
    except FileNotFoundError:
        print("❌ requirements.lock not found. Run 'require.py init' first.")
        sys.exit(1)
    print_scanned_files(check_result.scanned_files)
    diff = check_result.diff
    if (
        not diff[DiffType.ADDED]
        and not diff[DiffType.REMOVED]
        and not diff[DiffType.CHANGED]
    ):
        print("👍 requirements.lock is up-to-date.")
    else:
        print_diff_section("Added", diff[DiffType.ADDED], "+")
        print_diff_section("Removed", diff[DiffType.REMOVED], "-")
        print_diff_section("Changed", diff[DiffType.CHANGED], "*")
        sys.exit(2)


def cli_lock(args):
    """Handle the 'lock' CLI command."""
    dir_path = Path.cwd()
    lockfile_path = dir_path / "requirements.lock"
    # Gather new requirements
    md_files = find_markdown_files(dir_path)
    requirements: list[Requirement] = []
    for md_file in md_files:
        with md_file.open("r", encoding="utf-8") as f:
            md_text = f.read()
        reqs = parse_requirements_from_markdown(md_text)
        requirements.extend(reqs)
    # Check if lockfile exists and is up-to-date
    lockfile_exists = lockfile_path.is_file()
    up_to_date = False
    if lockfile_exists:
        try:
            old_reqs = load_lockfile(lockfile_path)
            up_to_date = old_reqs == requirements
        except (FileNotFoundError, json.JSONDecodeError):
            up_to_date = False
    print_scanned_files(md_files)
    if up_to_date:
        print("👍 requirements.lock is already up-to-date.")
    else:
        save_lockfile(lockfile_path, requirements)
        print(f"✅ requirements.lock updated with {len(requirements)} requirements.")


def main() -> None:
    """Parse arguments and run the appropriate CLI command for require.py."""
    parser = argparse.ArgumentParser(
        description="require.py - Markdown requirements tracker"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'init' command
    p_init = subparsers.add_parser(
        "init",
        help="Initialize require.py in the current directory and generate requirements.lock.",
    )
    p_init.set_defaults(func=cli_init)

    # 'check' command
    p_check = subparsers.add_parser(
        "check",
        help="Check if requirements.lock is up-to-date with Markdown requirements.",
    )
    p_check.set_defaults(func=cli_check)

    # 'lock' command
    p_lock = subparsers.add_parser(
        "lock", help="Update requirements.lock to match current Markdown requirements."
    )
    p_lock.set_defaults(func=cli_lock)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
