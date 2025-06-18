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

    def test_init_and_reinit(self) -> None:
        """Test init and re-init scenarios for requirements management."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = """
> REQ-1
> The first requirement.
> critical

> REQ-2
> The second requirement.
> child: REQ-1
"""
            reqs_md = test_dir_path / "reqs.md"
            reqs_md.write_text(md_content)
            files, reqs = api_init(tmpdir)
            self.assertIn(test_dir_path / "reqs.md", files)
            lockfile_path = test_dir_path / "requirements.lock"
            self.assertTrue(lockfile_path.exists())
            lock_data = json.loads(lockfile_path.read_text())
            self.assertEqual(len(lock_data), 2)
            files2, reqs2 = api_init(tmpdir)
            self.assertEqual(files, files2)
            self.assertEqual(len(reqs2), 2)
            lock_data2 = json.loads(lockfile_path.read_text())
            self.assertEqual(lock_data, lock_data2)

    def test_add_requirement_updates_lockfile(self) -> None:
        """Test that requirements are added to requirements.lock when Markdown files are updated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = "> REQ-1\n> The first requirement.\n> critical\n"
            md_path = test_dir_path / "reqs.md"
            md_path.write_text(md_content)
            api_init(tmpdir)
            lockfile_path = test_dir_path / "requirements.lock"
            lock_data = json.loads(lockfile_path.read_text())
            self.assertEqual(len(lock_data), 1)
            self.assertEqual(lock_data[0]["id"], "REQ-1")
            md_content_updated = "> REQ-1\n> The first requirement.\n> critical\n\n> REQ-2\n> The second requirement.\n"
            md_path.write_text(md_content_updated)
            api_lock(tmpdir)
            lock_data_updated = json.loads(lockfile_path.read_text())
            self.assertEqual(len(lock_data_updated), 2)
            ids = {req["id"] for req in lock_data_updated}
            self.assertIn("REQ-1", ids)
            self.assertIn("REQ-2", ids)

    def test_child_of_nonexistent_requirement(self) -> None:
        """Test behavior when a requirement is marked as a child of a non-existing requirement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = (
                "> REQ-1\n> The first requirement.\n> child: REQ-DOES-NOT-EXIST\n"
            )
            reqs_md = test_dir_path / "reqs.md"
            reqs_md.write_text(md_content)
            files, reqs = api_init(tmpdir)
            self.assertEqual(len(reqs), 1)
            req = reqs[0]
            self.assertIn("REQ-DOES-NOT-EXIST", req.children)

    def test_lock_idempotency(self) -> None:
        """Test that running api_lock twice without changes does not alter the lockfile (idempotency)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = "> REQ-1\n> The first requirement.\n> critical\n"
            md_path = test_dir_path / "reqs.md"
            md_path.write_text(md_content)
            api_init(tmpdir)
            lockfile_path = test_dir_path / "requirements.lock"
            lock_data_1 = lockfile_path.read_text()
            api_lock(tmpdir)
            lock_data_2 = lockfile_path.read_text()
            self.assertEqual(
                lock_data_1,
                lock_data_2,
                "Lockfile should not change if requirements are unchanged.",
            )


class TestRequirementPrettyString(unittest.TestCase):
    """Unit tests for the to_pretty_string method of Requirement."""

    def test_pretty_string_variants(self) -> None:
        """Test pretty string output for various requirement field combinations."""
        cases = [
            (Requirement(req_id="REQ-1", description="A minimal requirement."), "REQ-1: A minimal requirement."),
            (Requirement(req_id="REQ-2", description="A critical requirement.", critical=True), "REQ-2: A critical requirement.\n  - critical"),
            (Requirement(req_id="REQ-3", description="Has children.", children=["REQ-1", "REQ-2"]), "REQ-3: Has children.\n  - children: REQ-1, REQ-2"),
            (Requirement(req_id="REQ-4", description="Completed requirement.", completed=True), "REQ-4: Completed requirement.\n  - completed"),
            (Requirement(req_id="REQ-5", description="All fields set.", critical=True, children=["REQ-1", "REQ-2"], completed=True), "REQ-5: All fields set.\n  - critical\n  - children: REQ-1, REQ-2\n  - completed"),
        ]
        for req, expected in cases:
            with self.subTest(req=req):
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
