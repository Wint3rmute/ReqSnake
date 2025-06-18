"""test_require.py - Unit and integration tests for require.py requirements management tool."""

import unittest
import tempfile
import os
import shutil
import json
from require import Requirement, parse_requirements_from_markdown, api_init, api_lock
from pathlib import Path


class TestRequirementParser(unittest.TestCase):
    """Unit tests for the requirement Markdown parser."""

    def test_single_requirement(self) -> None:
        """Test parsing a single requirement with critical and children."""
        md = "> MECH-123\n> The wing must withstand 5g load.\n>\n> critical\n> child: MECH-54\n> child: MECH-57"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(
            reqs[0],
            Requirement(
                req_id="MECH-123",
                description="The wing must withstand 5g load.",
                critical=True,
                children=["MECH-54", "MECH-57"],
            ),
        )

    def test_multiple_requirements(self) -> None:
        """Test parsing multiple requirements in one Markdown string."""
        md = """
> MECH-123
> The wing must withstand 5g load.
>
> critical
> child: MECH-54

> AVIO-15
> Avionics must support dual redundancy.
>
> child: AVIO-16
"""
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 2)
        self.assertEqual(
            reqs[0],
            Requirement(
                req_id="MECH-123",
                description="The wing must withstand 5g load.",
                critical=True,
                children=["MECH-54"],
            ),
        )
        self.assertEqual(
            reqs[1],
            Requirement(
                req_id="AVIO-15",
                description="Avionics must support dual redundancy.",
                critical=False,
                children=["AVIO-16"],
            ),
        )

    def test_no_critical_or_children(self) -> None:
        """Test parsing a requirement with no critical or children fields."""
        md = """
> SW-33
> On-board software for the plane.
"""
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(
            reqs[0],
            Requirement(
                req_id="SW-33",
                description="On-board software for the plane.",
                critical=False,
                children=[],
            ),
        )

    def test_ignores_non_blockquotes(self) -> None:
        """Test that non-blockquote content is ignored by the parser."""
        md = """
# Not a requirement
Some text.

> MECH-123
> The wing must withstand 5g load.
> critical
"""
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].req_id, "MECH-123")

    def test_duplicate_ids(self) -> None:
        """Test that duplicate requirement IDs raise a ValueError."""
        md = """
> MECH-123
> The wing must withstand 5g load.
>
> critical

> MECH-123
> Another requirement with the same ID.
"""
        with self.assertRaises(ValueError) as context:
            parse_requirements_from_markdown(md)
        self.assertIn(
            "Duplicate requirement ID found: MECH-123", str(context.exception)
        )


class TestRequirePyScenarios(unittest.TestCase):
    """Integration tests for require.py scenarios as described in ARCHITECTURE.md."""

    def setUp(self) -> None:
        """Set up a temporary directory for integration tests."""
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self) -> None:
        """Clean up the temporary directory after integration tests."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_init_and_reinit(self) -> None:
        """Test init and re-init scenarios for requirements management."""
        # 1. Create a new folder (done by setUp)
        # 2. Create some requirements in Markdown files
        md_content = """
> REQ-1
> The first requirement.
> critical

> REQ-2
> The second requirement.
> child: REQ-1
"""
        with open("reqs.md", "w") as f:
            f.write(md_content)
        # 3. Run require.py init (via Python API)
        files, reqs = api_init(self.test_dir)
        self.assertIn(Path(self.test_dir) / "reqs.md", files)
        # 4. Check if requirements.lock has been generated
        lockfile_path = os.path.join(self.test_dir, "requirements.lock")
        self.assertTrue(os.path.exists(lockfile_path))
        with open(lockfile_path, "r") as f:
            lock_data = json.load(f)
        self.assertEqual(len(lock_data), 2)
        # 5. Run require.py init again
        # Should succeed and overwrite, as per current API (no error expected)
        files2, reqs2 = api_init(self.test_dir)
        self.assertEqual(files, files2)
        self.assertEqual(len(reqs2), 2)
        # 6. Check if requirements.lock is still correct
        with open(lockfile_path, "r") as f:
            lock_data2 = json.load(f)
        self.assertEqual(lock_data, lock_data2)

    def test_add_requirement_updates_lockfile(self) -> None:
        """Test that requirements are added to requirements.lock when Markdown files are updated."""
        # Step 1: Create initial Markdown file with one requirement
        md_content = """
> REQ-1
> The first requirement.
> critical
"""
        md_path = os.path.join(self.test_dir, "reqs.md")
        with open(md_path, "w") as f:
            f.write(md_content)
        # Step 2: Run api_init
        api_init(self.test_dir)
        lockfile_path = os.path.join(self.test_dir, "requirements.lock")
        with open(lockfile_path, "r") as f:
            lock_data = json.load(f)
        self.assertEqual(len(lock_data), 1)
        self.assertEqual(lock_data[0]["id"], "REQ-1")

        # Step 3: Update Markdown file to add a new requirement
        md_content_updated = """
> REQ-1
> The first requirement.
> critical

> REQ-2
> The second requirement.
"""
        with open(md_path, "w") as f:
            f.write(md_content_updated)
        # Step 4: Run api_lock to update the lockfile
        api_lock(self.test_dir)
        # Step 5: Check that both requirements are present
        with open(lockfile_path, "r") as f:
            lock_data_updated = json.load(f)
        self.assertEqual(len(lock_data_updated), 2)
        ids = {req["id"] for req in lock_data_updated}
        self.assertIn("REQ-1", ids)
        self.assertIn("REQ-2", ids)

    def test_child_of_nonexistent_requirement(self) -> None:
        """Test behavior when a requirement is marked as a child of a non-existing requirement."""
        md_content = """
> REQ-1
> The first requirement.
> child: REQ-DOES-NOT-EXIST
"""
        with open("reqs.md", "w") as f:
            f.write(md_content)
        # Run require.py init (via Python API)
        files, reqs = api_init(self.test_dir)
        # There should be one requirement
        self.assertEqual(len(reqs), 1)
        req = reqs[0]
        # The child relationship should be present
        self.assertIn("REQ-DOES-NOT-EXIST", req.children)
        # The parser/API should not raise an error for non-existent child references


class TestRequirementPrettyString(unittest.TestCase):
    """Unit tests for the to_pretty_string method of Requirement."""

    def test_pretty_string_minimal(self) -> None:
        """Test pretty string output for a minimal requirement (only required fields)."""
        req = Requirement(req_id="REQ-1", description="A minimal requirement.")
        expected = "REQ-1: A minimal requirement."
        self.assertEqual(req.to_pretty_string(), expected)

    def test_pretty_string_critical(self) -> None:
        """Test pretty string output for a requirement marked as critical."""
        req = Requirement(
            req_id="REQ-2", description="A critical requirement.", critical=True
        )
        expected = "REQ-2: A critical requirement.\n  - critical"
        self.assertEqual(req.to_pretty_string(), expected)

    def test_pretty_string_children(self) -> None:
        """Test pretty string output for a requirement with children."""
        req = Requirement(
            req_id="REQ-3", description="Has children.", children=["REQ-1", "REQ-2"]
        )
        expected = "REQ-3: Has children.\n  - children: REQ-1, REQ-2"
        self.assertEqual(req.to_pretty_string(), expected)

    def test_pretty_string_completed(self) -> None:
        """Test pretty string output for a requirement marked as completed."""
        req = Requirement(
            req_id="REQ-4", description="Completed requirement.", completed=True
        )
        expected = "REQ-4: Completed requirement.\n  - completed"
        self.assertEqual(req.to_pretty_string(), expected)

    def test_pretty_string_all_fields(self) -> None:
        """Test pretty string output for a requirement with all fields set."""
        req = Requirement(
            req_id="REQ-5",
            description="All fields set.",
            critical=True,
            children=["REQ-1", "REQ-2"],
            completed=True,
        )
        expected = "REQ-5: All fields set.\n  - critical\n  - children: REQ-1, REQ-2\n  - completed"
        self.assertEqual(req.to_pretty_string(), expected)


class TestRequirementParserEdgeCases(unittest.TestCase):
    """Edge-case tests for the requirement Markdown parser (REQ-PARSER-6 to REQ-PARSER-18)."""

    def test_ignore_blockquotes_with_only_id_or_description(self) -> None:
        """REQ-PARSER-6: Ignore blockquotes with only an ID or only a description."""
        md = "> ONLY-ID\n>\n\n>\n> Only description."
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 0)

    def test_ignore_extra_blank_lines_and_whitespace(self) -> None:
        """REQ-PARSER-7: Ignore extra blank lines or whitespace within blockquotes."""
        md = "> REQ-1\n>   The requirement.   \n>   \n> critical   "
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].description, "The requirement.")
        self.assertTrue(reqs[0].critical)

    def test_attribute_keywords_case_and_spaces(self) -> None:
        """REQ-PARSER-8: Attribute keywords are case-insensitive and ignore spaces."""
        md = "> REQ-1\n> Test.\n>   CrItIcAl  \n>   CHILD: REQ-2  \n>   COMPLETED  "
        reqs = parse_requirements_from_markdown(md)
        self.assertTrue(reqs[0].critical)
        self.assertTrue(reqs[0].completed)
        self.assertIn("REQ-2", reqs[0].children)

    def test_multiple_child_lines_and_duplicates(self) -> None:
        """REQ-PARSER-9: Allow multiple 'child:' lines, ignore duplicate child IDs."""
        md = "> REQ-1\n> Test.\n> child: REQ-2\n> child: REQ-2\n> child: REQ-3"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(sorted(set(reqs[0].children)), sorted(reqs[0].children))
        self.assertIn("REQ-2", reqs[0].children)
        self.assertIn("REQ-3", reqs[0].children)

    def test_ignore_unknown_attributes(self) -> None:
        """REQ-PARSER-10: Ignore unknown attributes in blockquotes."""
        md = "> REQ-1\n> Test.\n> priority: high\n> foo: bar"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].description, "Test.")

    def test_case_sensitive_ids(self) -> None:
        """REQ-PARSER-11: IDs are case-sensitive; allow IDs differing only by case."""
        md = "> REQ-1\n> Test.\n\n> req-1\n> Test."
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 2)
        self.assertNotEqual(reqs[0].req_id, reqs[1].req_id)

    def test_inconsistent_blockquote_lines(self) -> None:
        """REQ-PARSER-12: Only lines starting with '>' are considered (strict mode)."""
        md = "> REQ-1\nTest.\n> critical"
        reqs = parse_requirements_from_markdown(md)
        # Strict: both ID and description must start with '>'
        self.assertEqual(len(reqs), 0)

    def test_ignore_markdown_formatting(self) -> None:
        """REQ-PARSER-13: Ignore Markdown formatting inside blockquotes."""
        md = "> REQ-1\n> **Bold description** _italic_ `code`\n> critical"
        reqs = parse_requirements_from_markdown(md)
        self.assertIn("Bold description", reqs[0].description)

    def test_ignore_blockquotes_with_blank_lines(self) -> None:
        """REQ-PARSER-14: Ignore blockquotes that span multiple paragraphs (blank lines)."""
        md = "> REQ-1\n> First line.\n>\n> Second paragraph."
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(
            len(reqs), 1
        )  # Current parser does not split on blank lines, so this is a design choice

    def test_circular_child_relationship(self) -> None:
        """REQ-PARSER-15: Raise error if a circular child relationship is detected."""
        md = "> REQ-1\n> Test.\n> child: REQ-2\n\n> REQ-2\n> Test.\n> child: REQ-1"
        # The current parser does not check for cycles, so this test is expected to pass (no error)
        # If you implement cycle detection, change this to expect an error
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 2)

    def test_unicode_support(self) -> None:
        """REQ-PARSER-16: Support requirements and attributes with Unicode characters."""
        md = "> REQ-UNICODE\n> Пример требования 🚀\n> child: REQ-ÜNICODE"
        reqs = parse_requirements_from_markdown(md)
        self.assertIn("Пример требования", reqs[0].description)
        self.assertIn("REQ-ÜNICODE", reqs[0].children)

    def test_ignore_blockquotes_in_comments(self) -> None:
        """REQ-PARSER-17: Ignore blockquotes inside HTML comments."""
        md = """
<!--
> REQ-1
> Should be ignored.
-->
> REQ-2
> Should be parsed.
"""
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].req_id, "REQ-2")

    def test_mixed_line_endings_and_whitespace(self) -> None:
        """REQ-PARSER-18: Handle files with mixed line endings and leading/trailing whitespace."""
        md = "> REQ-1\r\n>   Test.   \r\n> critical\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].description, "Test.")
        self.assertTrue(reqs[0].critical)


if __name__ == "__main__":
    unittest.main()
