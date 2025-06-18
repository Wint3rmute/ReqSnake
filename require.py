import re
from typing import List, Dict, Optional
import os
import argparse

class Requirement:
    """Represents a requirement parsed from a Markdown block-quote.

    Attributes:
        req_id (str): The unique identifier of the requirement.
        description (str): A short description of the requirement.
        critical (bool): Whether the requirement is marked as critical.
        children (List[str]): List of child requirement IDs.
    """
    def __init__(self, req_id: str, description: str, critical: bool = False, children: Optional[List[str]] = None):
        """Initializes a Requirement instance.

        Args:
            req_id (str): The unique identifier of the requirement.
            description (str): A short description of the requirement.
            critical (bool, optional): Whether the requirement is critical. Defaults to False.
            children (Optional[List[str]], optional): List of child requirement IDs. Defaults to None.
        """
        self.req_id = req_id
        self.description = description
        self.critical = critical
        self.children = children or []

    def __eq__(self, other):
        """Checks equality with another Requirement instance.

        Args:
            other (Requirement): Another Requirement instance to compare.

        Returns:
            bool: True if all attributes are equal, False otherwise.
        """
        return (
            self.req_id == other.req_id and
            self.description == other.description and
            self.critical == other.critical and
            self.children == other.children
        )

    def __repr__(self):
        """Returns a string representation of the Requirement instance.

        Returns:
            str: String representation of the requirement.
        """
        return f"Requirement({self.req_id!r}, {self.description!r}, critical={self.critical}, children={self.children})"


def parse_requirements_from_markdown(md_text: str) -> List[Requirement]:
    """Parses requirements from Markdown text using block-quote syntax.

    Each requirement is defined as a block-quote where:
        - The first line is the requirement ID.
        - The second line is the short description.
        - Subsequent lines can specify 'critical' and 'child: <ID>'.

    Args:
        md_text (str): The Markdown text to parse.

    Returns:
        List[Requirement]: A list of parsed Requirement objects.

    Raises:
        ValueError: If duplicate requirement IDs are found.
    """
    requirements = []
    seen_ids = set()
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
        children = []
        for line in lines[2:]:
            if line.lower() == 'critical':
                critical = True
            elif line.lower().startswith('child:'):
                child_id = line[6:].strip()
                if child_id:
                    children.append(child_id)
        requirements.append(Requirement(req_id, description, critical, children))
    return requirements


def main():
    """Entrypoint for the require.py CLI application."""
    parser = argparse.ArgumentParser(description="require.py - Markdown requirements tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'parse' command
    parse_parser = subparsers.add_parser("parse", help="Parse requirements from a Markdown file and print them.")
    parse_parser.add_argument("file", type=str, help="Path to the Markdown file to parse.")

    args = parser.parse_args()

    if args.command == "parse":
        if not os.path.isfile(args.file):
            print(f"Error: File not found: {args.file}")
            exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            md_text = f.read()
        try:
            requirements = parse_requirements_from_markdown(md_text)
        except ValueError as e:
            print(f"Error: {e}")
            exit(1)
        for req in requirements:
            print(req)

if __name__ == "__main__":
    main() 