import re
from typing import List, Dict, Optional
import os
import unittest

class Requirement:
    def __init__(self, req_id: str, description: str, critical: bool = False, children: Optional[List[str]] = None):
        self.req_id = req_id
        self.description = description
        self.critical = critical
        self.children = children or []

    def __eq__(self, other):
        return (
            self.req_id == other.req_id and
            self.description == other.description and
            self.critical == other.critical and
            self.children == other.children
        )

    def __repr__(self):
        return f"Requirement({self.req_id!r}, {self.description!r}, critical={self.critical}, children={self.children})"


def parse_requirements_from_markdown(md_text: str) -> List[Requirement]:
    requirements = []
    blockquote_pattern = re.compile(r"(^> .*(?:\n>.*)*)", re.MULTILINE)
    for block in blockquote_pattern.findall(md_text):
        lines = [line[2:].strip() for line in block.split('\n') if line.startswith('>')]
        if len(lines) < 2:
            continue  # Not enough info for a requirement
        req_id = lines[0]
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

# --- Unit Tests ---
class TestRequirementParser(unittest.TestCase):
    def test_single_requirement(self):
        md = "> MECH-123\n> The wing must withstand 5g load.\n>\n> critical\n> child: MECH-54\n> child: MECH-57"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0], Requirement(
            req_id="MECH-123",
            description="The wing must withstand 5g load.",
            critical=True,
            children=["MECH-54", "MECH-57"]
        ))

    def test_multiple_requirements(self):
        md = (
            "> MECH-123\n> The wing must withstand 5g load.\n>\n> critical\n> child: MECH-54\n\n"
            "> AVIO-15\n> Avionics must support dual redundancy.\n>\n> child: AVIO-16\n"
        )
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 2)
        self.assertEqual(reqs[0], Requirement(
            req_id="MECH-123",
            description="The wing must withstand 5g load.",
            critical=True,
            children=["MECH-54"]
        ))
        self.assertEqual(reqs[1], Requirement(
            req_id="AVIO-15",
            description="Avionics must support dual redundancy.",
            critical=False,
            children=["AVIO-16"]
        ))

    def test_no_critical_or_children(self):
        md = "> SW-33\n> On-board software for the plane."
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0], Requirement(
            req_id="SW-33",
            description="On-board software for the plane.",
            critical=False,
            children=[]
        ))

    def test_ignores_non_blockquotes(self):
        md = "# Not a requirement\nSome text.\n\n> MECH-123\n> The wing must withstand 5g load.\n> critical"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].req_id, "MECH-123")

if __name__ == "__main__":
    unittest.main() 