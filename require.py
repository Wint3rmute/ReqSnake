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

    def __post_init__(self) -> None:
        """Post-initialize the Requirement dataclass. No-op, as children is handled by default_factory."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the requirement for JSON serialization."""
        return {
            "id": self.req_id,
            "description": self.description,
            "critical": self.critical,
            "children": self.children,
            "completed": self.completed
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> 'Requirement':
        """Create a Requirement from a dictionary."""
        return Requirement(
            req_id=data["id"],
            description=data["description"],
            critical=data.get("critical", False),
            children=data.get("children", []),
            completed=data.get("completed", False)
        )

class InitResult(NamedTuple):
    """Result of api_init: scanned files and requirements."""

    scanned_files: list[Path]
    requirements: list[Requirement]

class CheckResult(NamedTuple):
    """Result of api_check: scanned files and diff dict."""

    scanned_files: list[Path]
    diff: dict[str, list[Requirement]]

class LockResult(NamedTuple):
    """Result of api_lock: scanned files and requirements."""

    scanned_files: list[Path]
    requirements: list[Requirement]

# Regex for blockquotes: matches contiguous blockquote lines
BLOCKQUOTE_PATTERN = re.compile(
    r"(^> .*(?:\n>.*)*)",  # Match a block starting with '> ' and all following '> ...' lines
    re.MULTILINE
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
    requirements: list[Requirement] = []
    seen_ids: Set[str] = set()
    for block in BLOCKQUOTE_PATTERN.findall(md_text):
        lines = [line[2:].strip() for line in block.split('\n') if line.startswith('>')]
        if len(lines) < 2:
            continue  # Not enough info for a requirement
        req_id = lines[0]
        if req_id in seen_ids:
            raise ValueError(f"Duplicate requirement ID found: {req_id}")
        seen_ids.add(req_id)
        description = lines[1]
        critical = False
        completed = False
        children: list[str] = []
        for line in lines[2:]:
            if line.lower() == 'critical':
                critical = True
            elif line.lower() == 'completed':
                completed = True
            elif line.lower().startswith('child:'):
                child_id = line[6:].strip()
                if child_id:
                    children.append(child_id)
        requirements.append(Requirement(req_id, description, critical, children, completed))
    return requirements

def find_markdown_files(root_dir: Path) -> list[Path]:
    """Return all Markdown (.md) files in the given directory recursively."""
    return [p for p in root_dir.rglob('*.md') if p.is_file()]

def load_lockfile(lockfile_path: Path) -> list[Requirement]:
    """Load requirements from a JSON lockfile."""
    with lockfile_path.open('r', encoding='utf-8') as f:
        data: list[dict[str, Any]] = json.load(f)
    return [Requirement.from_dict(item) for item in data]

def save_lockfile(lockfile_path: Path, requirements: list[Requirement]) -> None:
    """Save requirements to a JSON lockfile."""
    with lockfile_path.open('w', encoding='utf-8') as f:
        json.dump([req.to_dict() for req in requirements], f, indent=2)

def diff_requirements(old: list[Requirement], new: list[Requirement]) -> dict[str, list[Requirement]]:
    """Compare two lists of requirements and return a diff dict."""
    old_dict: dict[str, Requirement] = {r.req_id: r for r in old}
    new_dict: dict[str, Requirement] = {r.req_id: r for r in new}
    added: list[Requirement] = [new_dict[rid] for rid in new_dict if rid not in old_dict]
    removed: list[Requirement] = [old_dict[rid] for rid in old_dict if rid not in new_dict]
    changed: list[Requirement] = [new_dict[rid] for rid in new_dict if rid in old_dict and new_dict[rid] != old_dict[rid]]
    return {"added": added, "removed": removed, "changed": changed}

def print_scanned_files(md_files: list[Path]) -> None:
    """Print the Markdown files being scanned."""
    print("🔍 Scanning the following Markdown files:")
    for md_file in md_files:
        print(f"  {md_file}")

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
    save_lockfile(lockfile_path, requirements)
    return LockResult(md_files, requirements)

# --- CLI Entrypoint ---
def main() -> None:
    """Parse arguments and run the appropriate CLI command for require.py."""
    parser = argparse.ArgumentParser(description="require.py - Markdown requirements tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'init' command
    subparsers.add_parser("init", help="Initialize require.py in the current directory and generate requirements.lock.")

    # 'check' command
    subparsers.add_parser("check", help="Check if requirements.lock is up-to-date with Markdown requirements.")

    # 'lock' command
    subparsers.add_parser("lock", help="Update requirements.lock to match current Markdown requirements.")

    args = parser.parse_args()

    if args.command == "init":
        init_result = api_init()
        print_scanned_files(init_result.scanned_files)
        print(f"✅ Initialized requirements.lock with {len(init_result.requirements)} requirements.")

    elif args.command == "check":
        try:
            check_result = api_check()
        except FileNotFoundError:
            print("❌ requirements.lock not found. Run 'require.py init' first.")
            sys.exit(1)
        print_scanned_files(check_result.scanned_files)
        diff = check_result.diff
        if not diff["added"] and not diff["removed"] and not diff["changed"]:
            print("👍 requirements.lock is up-to-date.")
        else:
            if diff["added"]:
                print("➕ Added requirements:")
                for req in diff["added"]:
                    print(f"  + {req}")
            if diff["removed"]:
                print("➖ Removed requirements:")
                for req in diff["removed"]:
                    print(f"  - {req}")
            if diff["changed"]:
                print("✏️ Changed requirements:")
                for req in diff["changed"]:
                    print(f"  * {req}")
            sys.exit(2)

    elif args.command == "lock":
        lock_result = api_lock()
        print_scanned_files(lock_result.scanned_files)
        print(f"✅ requirements.lock updated with {len(lock_result.requirements)} requirements.")

if __name__ == "__main__":
    main() 