import re
from typing import List, Dict, Optional, Any, Set, Tuple
import os
import argparse
import json

class Requirement:
    """Represents a requirement parsed from a Markdown block-quote.

    Attributes:
        req_id (str): The unique identifier of the requirement.
        description (str): A short description of the requirement.
        critical (bool): Whether the requirement is marked as critical.
        children (List[str]): List of child requirement IDs.
        completed (bool): Whether the requirement is completed.
    """
    def __init__(self, req_id: str, description: str, critical: bool = False, children: Optional[List[str]] = None, completed: bool = False) -> None:
        """Initializes a Requirement instance.

        Args:
            req_id (str): The unique identifier of the requirement.
            description (str): A short description of the requirement.
            critical (bool, optional): Whether the requirement is critical. Defaults to False.
            children (Optional[List[str]], optional): List of child requirement IDs. Defaults to None.
            completed (bool, optional): Whether the requirement is completed. Defaults to False.
        """
        self.req_id = req_id
        self.description = description
        self.critical = critical
        self.children = children or []
        self.completed = completed

    def __eq__(self, other: object) -> bool:
        """Checks equality with another Requirement instance.

        Args:
            other (Requirement): Another Requirement instance to compare.

        Returns:
            bool: True if all attributes are equal, False otherwise.
        """
        if not isinstance(other, Requirement):
            return NotImplemented
        return (
            self.req_id == other.req_id and
            self.description == other.description and
            self.critical == other.critical and
            self.children == other.children and
            self.completed == other.completed
        )

    def __repr__(self) -> str:
        """Returns a string representation of the Requirement instance.

        Returns:
            str: String representation of the requirement.
        """
        return f"Requirement({self.req_id!r}, {self.description!r}, critical={self.critical}, children={self.children}, completed={self.completed})"

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Requirement to a dictionary for JSON serialization."""
        return {
            "id": self.req_id,
            "description": self.description,
            "critical": self.critical,
            "children": self.children,
            "completed": self.completed
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Requirement':
        """Creates a Requirement from a dictionary."""
        return Requirement(
            req_id=data["id"],
            description=data["description"],
            critical=data.get("critical", False),
            children=data.get("children", []),
            completed=data.get("completed", False)
        )

def parse_requirements_from_markdown(md_text: str) -> List[Requirement]:
    """Parses requirements from Markdown text using block-quote syntax.

    Each requirement is defined as a block-quote where:
        - The first line is the requirement ID.
        - The second line is the short description.
        - Subsequent lines can specify 'critical', 'child: <ID>', and 'completed'.

    Args:
        md_text (str): The Markdown text to parse.

    Returns:
        List[Requirement]: A list of parsed Requirement objects.

    Raises:
        ValueError: If duplicate requirement IDs are found.
    """
    requirements: List[Requirement] = []
    seen_ids: Set[str] = set()
    blockquote_pattern = re.compile(r"(^> .*(?:\n>.*)*)", re.MULTILINE)
    for block in blockquote_pattern.findall(md_text):
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
        children: List[str] = []
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

def find_markdown_files(root_dir: str) -> List[str]:
    """Recursively finds all Markdown (.md) files in the given directory."""
    md_files: List[str] = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.md'):
                md_files.append(os.path.join(dirpath, filename))
    return md_files

def load_lockfile(lockfile_path: str) -> List[Requirement]:
    """Loads requirements from a JSON lockfile."""
    with open(lockfile_path, 'r', encoding='utf-8') as f:
        data: List[Dict[str, Any]] = json.load(f)
    return [Requirement.from_dict(item) for item in data]

def save_lockfile(lockfile_path: str, requirements: List[Requirement]) -> None:
    """Saves requirements to a JSON lockfile."""
    with open(lockfile_path, 'w', encoding='utf-8') as f:
        json.dump([req.to_dict() for req in requirements], f, indent=2)

def diff_requirements(old: List[Requirement], new: List[Requirement]) -> Dict[str, List[Requirement]]:
    """Compares two lists of requirements and returns a diff dict."""
    old_dict: Dict[str, Requirement] = {r.req_id: r for r in old}
    new_dict: Dict[str, Requirement] = {r.req_id: r for r in new}
    added: List[Requirement] = [new_dict[rid] for rid in new_dict if rid not in old_dict]
    removed: List[Requirement] = [old_dict[rid] for rid in old_dict if rid not in new_dict]
    changed: List[Requirement] = [new_dict[rid] for rid in new_dict if rid in old_dict and new_dict[rid] != old_dict[rid]]
    return {"added": added, "removed": removed, "changed": changed}

# --- Python API ---
def api_init(directory: Optional[str] = None) -> Tuple[List[str], List[Requirement]]:
    """Scan Markdown files and create requirements.lock. Returns (scanned_files, requirements)."""
    if directory is None:
        directory = os.getcwd()
    md_files = find_markdown_files(directory)
    requirements: List[Requirement] = []
    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            md_text = f.read()
        reqs = parse_requirements_from_markdown(md_text)
        requirements.extend(reqs)
    lockfile_path = os.path.join(directory, "requirements.lock")
    save_lockfile(lockfile_path, requirements)
    return md_files, requirements

def api_check(directory: Optional[str] = None) -> Tuple[List[str], Dict[str, List[Requirement]]]:
    """Scan Markdown files and compare to requirements.lock. Returns (scanned_files, diff_dict)."""
    if directory is None:
        directory = os.getcwd()
    lockfile_path = os.path.join(directory, "requirements.lock")
    if not os.path.isfile(lockfile_path):
        raise FileNotFoundError("requirements.lock not found. Run 'init' first.")
    md_files = find_markdown_files(directory)
    requirements: List[Requirement] = []
    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            md_text = f.read()
        reqs = parse_requirements_from_markdown(md_text)
        requirements.extend(reqs)
    lock_reqs = load_lockfile(lockfile_path)
    diff = diff_requirements(lock_reqs, requirements)
    return md_files, diff

def api_lock(directory: Optional[str] = None) -> Tuple[List[str], List[Requirement]]:
    """Scan Markdown files and update requirements.lock. Returns (scanned_files, requirements)."""
    if directory is None:
        directory = os.getcwd()
    md_files = find_markdown_files(directory)
    requirements: List[Requirement] = []
    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            md_text = f.read()
        reqs = parse_requirements_from_markdown(md_text)
        requirements.extend(reqs)
    lockfile_path = os.path.join(directory, "requirements.lock")
    save_lockfile(lockfile_path, requirements)
    return md_files, requirements

# --- CLI Entrypoint ---
def main() -> None:
    """Entrypoint for the require.py CLI application."""
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
        md_files, requirements = api_init()
        print("Scanning the following Markdown files:")
        for md_file in md_files:
            print(f"  {md_file}")
        print(f"Initialized requirements.lock with {len(requirements)} requirements.")

    elif args.command == "check":
        try:
            md_files, diff = api_check()
        except FileNotFoundError:
            print("requirements.lock not found. Run 'require.py init' first.")
            exit(1)
        print("Scanning the following Markdown files:")
        for md_file in md_files:
            print(f"  {md_file}")
        if not diff["added"] and not diff["removed"] and not diff["changed"]:
            print("requirements.lock is up-to-date.")
        else:
            if diff["added"]:
                print("Added requirements:")
                for req in diff["added"]:
                    print(f"  + {req}")
            if diff["removed"]:
                print("Removed requirements:")
                for req in diff["removed"]:
                    print(f"  - {req}")
            if diff["changed"]:
                print("Changed requirements:")
                for req in diff["changed"]:
                    print(f"  * {req}")
            exit(2)

    elif args.command == "lock":
        md_files, requirements = api_lock()
        print("Scanning the following Markdown files:")
        for md_file in md_files:
            print(f"  {md_file}")
        print(f"requirements.lock updated with {len(requirements)} requirements.")

if __name__ == "__main__":
    main() 