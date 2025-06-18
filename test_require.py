import unittest
from require import Requirement, parse_requirements_from_markdown

class TestRequirementParser(unittest.TestCase):
    """Unit tests for the requirement Markdown parser."""
    def test_single_requirement(self):
        """Test parsing a single requirement with critical and children."""
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
        """Test parsing multiple requirements in one Markdown string."""
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
        """Test parsing a requirement with no critical or children fields."""
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
        """Test that non-blockquote content is ignored by the parser."""
        md = "# Not a requirement\nSome text.\n\n> MECH-123\n> The wing must withstand 5g load.\n> critical"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].req_id, "MECH-123")

    def test_duplicate_ids(self):
        """Test that duplicate requirement IDs raise a ValueError."""
        md = (
            "> MECH-123\n> The wing must withstand 5g load.\n>\n> critical\n\n"
            "> MECH-123\n> Another requirement with the same ID.\n"
        )
        with self.assertRaises(ValueError) as context:
            parse_requirements_from_markdown(md)
        self.assertIn("Duplicate requirement ID found: MECH-123", str(context.exception))

if __name__ == "__main__":
    unittest.main() 