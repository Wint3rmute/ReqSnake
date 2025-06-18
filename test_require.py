"""test_require.py - Unit and integration tests for require.py requirements management tool."""

import unittest
import tempfile
import os
import shutil
import json
from require import (
    Requirement,
    parse_requirements_from_markdown,
    api_init,
    api_lock,
    api_status,
    StatusResult,
)
from pathlib import Path
import subprocess
import sys


class TestRequirementParser(unittest.TestCase):
    """Unit tests for the requirement Markdown parser."""

    def test_single_requirement(self) -> None:
        """Test parsing a single requirement with critical and children."""
        md = "> MECH-123\n> The wing must withstand 5g load.\n>\n> critical\n> child-of: MECH-54\n> child-of: MECH-57"
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
> child-of: MECH-54

> AVIO-15
> Avionics must support dual redundancy.
>
> child-of: AVIO-16
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

    def test_child_of_syntax(self) -> None:
        """Test that 'child-of' is supported as a child relationship key."""
        md = "> REQ-1\n> Parent requirement.\n> child-of REQ-2\n> child-of: REQ-3\n> CHILD-OF req-5\n> child-of: REQ-6\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(
            set(reqs[0].children),
            {"REQ-2", "REQ-3", "req-5", "REQ-6"},
        )

    def test_child_of_whitespace_and_case(self) -> None:
        """Test that 'child-of' is parsed case-insensitively and trims whitespace."""
        md = "> REQ-1\n> Parent.\n>   CHILD-OF:   REQ-2   \n> child-of   REQ-3\n> child-OF:REQ-4\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(
            set(reqs[0].children),
            {"REQ-2", "REQ-3", "REQ-4"},
        )

    def test_duplicate_child_ids_error(self) -> None:
        """REQ-PARSER-99: The parser shall raise errors on duplicated 'child-of' lines per requirement (case-insensitive, whitespace-insensitive)."""
        # Duplicate via 'child-of' (exact)
        md = "> REQ-1\n> Parent.\n> child-of: REQ-2\n> child-of: REQ-2\n"
        with self.assertRaises(ValueError) as ctx:
            parse_requirements_from_markdown(md)
        self.assertIn("Duplicate child ID", str(ctx.exception))
        # Duplicate across 'child-of' forms (case-insensitive)
        md2 = "> REQ-1\n> Parent.\n> child-of REQ-2\n> child-of: req-2\n"
        with self.assertRaises(ValueError) as ctx:
            parse_requirements_from_markdown(md2)
        self.assertIn("Duplicate child ID", str(ctx.exception))
        # Duplicate with whitespace differences
        md3 = "> REQ-1\n> Parent.\n> child-of:   REQ-2   \n> child-of: REQ-2\n"
        with self.assertRaises(ValueError) as ctx:
            parse_requirements_from_markdown(md3)
        self.assertIn("Duplicate child ID", str(ctx.exception))

    def test_multiple_child_lines_and_duplicates(self) -> None:
        """REQ-PARSER-9/99: Multiple 'child-of' lines are allowed, but duplicates must raise an error."""
        md = "> REQ-1\n> Test.\n> child-of: REQ-2\n> child-of: REQ-2\n> child-of: REQ-3"
        with self.assertRaises(ValueError) as ctx:
            parse_requirements_from_markdown(md)
        self.assertIn("Duplicate child ID 'REQ-2'", str(ctx.exception))

    def test_requirement_id_format_enforced(self) -> None:
        """REQ-CORE-6: IDs must be in the form <STRING>-<NUMBER>."""
        # Valid IDs
        valid_md = "> REQ-1\n> Valid.\n\n> SW-33\n> Valid.\n\n> A-0\n> Valid.\n"
        reqs = parse_requirements_from_markdown(valid_md)
        self.assertEqual(len(reqs), 3)
        # Invalid IDs
        invalid_cases = [
            "> REQ1\n> Invalid.\n",  # missing dash
            "> REQ-\n> Invalid.\n",  # missing number
            "> -123\n> Invalid.\n",  # missing string
            "> 123-REQ\n> Invalid.\n",  # number first
            "> REQ-12A\n> Invalid.\n",  # number not integer
            "> _REQ-1\n> Invalid.\n",  # starts with underscore
            "> 1REQ-1\n> Invalid.\n",  # starts with number
        ]
        for md in invalid_cases:
            with self.assertRaises(ValueError, msg=md):
                parse_requirements_from_markdown(md)


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
> child-of: REQ-1
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
            self.assertEqual(lock_data[0]["req_id"], "REQ-1")
            md_content_updated = "> REQ-1\n> The first requirement.\n> critical\n\n> REQ-2\n> The second requirement.\n"
            md_path.write_text(md_content_updated)
            api_lock(tmpdir)
            lock_data_updated = json.loads(lockfile_path.read_text())
            self.assertEqual(len(lock_data_updated), 2)
            ids = {req["req_id"] for req in lock_data_updated}
            self.assertIn("REQ-1", ids)
            self.assertIn("REQ-2", ids)

    def test_child_of_nonexistent_requirement(self) -> None:
        """Test behavior when a requirement is marked as a child of a non-existing requirement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = (
                "> REQ-1\n> The first requirement.\n> child-of: REQ-DOES-NOT-EXIST\n"
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

    def test_cli_check_outputs_file_path(self) -> None:
        """Test that the CLI check output includes the file path for changed requirements."""
        require_py = str(Path(__file__).parent / "require.py")
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_path = test_dir_path / "reqs.md"
            md_path.write_text("> REQ-1\n> The first requirement.\n")
            # Run init
            subprocess.run(
                [sys.executable, require_py, "init"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
            )
            # Change the requirement
            md_path.write_text("> REQ-1\n> The changed requirement.\n")
            # Run check and capture output
            result = subprocess.run(
                [sys.executable, require_py, "check"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            self.assertIn(str(md_path), result.stdout)
            self.assertIn("Changed requirements:", result.stdout)

    def test_requirementsignore_ignores_files(self) -> None:
        """REQ-CLI-11: Files matching .requirementsignore .gitignore-style globs are ignored during scanning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            # Create two markdown files
            file1 = test_dir_path / "reqs1.md"
            file2 = test_dir_path / "ignoreme.md"
            file1.write_text("> REQ-1\n> Requirement 1.\n")
            file2.write_text("> REQ-2\n> Requirement 2.\n")
            # Test literal ignore
            (test_dir_path / ".requirementsignore").write_text("ignoreme.md\n")
            files, reqs = api_init(tmpdir)
            scanned = {f.name for f in files}
            self.assertIn("reqs1.md", scanned)
            self.assertNotIn("ignoreme.md", scanned)
            self.assertEqual(len(reqs), 1)
            self.assertEqual(reqs[0].req_id, "REQ-1")
            # Test glob ignore
            (test_dir_path / ".requirementsignore").write_text("*ignore*.md\n")
            files, reqs = api_init(tmpdir)
            scanned = {f.name for f in files}
            self.assertIn("reqs1.md", scanned)
            self.assertNotIn("ignoreme.md", scanned)
            self.assertEqual(len(reqs), 1)
            self.assertEqual(reqs[0].req_id, "REQ-1")
            # Test negation (!)
            (test_dir_path / ".requirementsignore").write_text("*.md\n!reqs1.md\n")
            files, reqs = api_init(tmpdir)
            scanned = {f.name for f in files}
            self.assertIn("reqs1.md", scanned)
            self.assertNotIn("ignoreme.md", scanned)
            self.assertEqual(len(reqs), 1)
            self.assertEqual(reqs[0].req_id, "REQ-1")
            # Now remove .requirementsignore and both should be scanned
            (test_dir_path / ".requirementsignore").unlink()
            files, reqs = api_init(tmpdir)
            scanned = {f.name for f in files}
            self.assertIn("reqs1.md", scanned)
            self.assertIn("ignoreme.md", scanned)
            self.assertEqual(len(reqs), 2)


class TestRequirementPrettyString(unittest.TestCase):
    """Unit tests for the to_pretty_string method of Requirement."""

    def test_pretty_string_variants(self) -> None:
        """Test pretty string output for various requirement field combinations."""
        cases = [
            (
                Requirement(req_id="REQ-1", description="A minimal requirement."),
                "REQ-1: A minimal requirement.",
            ),
            (
                Requirement(
                    req_id="REQ-2", description="A critical requirement.", critical=True
                ),
                "REQ-2: A critical requirement.\n  - critical",
            ),
            (
                Requirement(
                    req_id="REQ-3",
                    description="Has children.",
                    children=["REQ-1", "REQ-2"],
                ),
                "REQ-3: Has children.\n  - children: REQ-1, REQ-2",
            ),
            (
                Requirement(
                    req_id="REQ-4", description="Completed requirement.", completed=True
                ),
                "REQ-4: Completed requirement.\n  - completed",
            ),
            (
                Requirement(
                    req_id="REQ-5",
                    description="All fields set.",
                    critical=True,
                    children=["REQ-1", "REQ-2"],
                    completed=True,
                ),
                "REQ-5: All fields set.\n  - critical\n  - children: REQ-1, REQ-2\n  - completed",
            ),
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
        """REQ-PARSER-8: Attribute keywords are case-insensitive and ignore spaces. 'child:' is now an error as unknown attribute."""
        md = "> REQ-1\n> Test.\n>   CrItIcAl  \n>   CHILD: REQ-2  \n>   COMPLETED  "
        with self.assertRaises(ValueError) as ctx:
            parse_requirements_from_markdown(md)
        self.assertIn("Unknown atttribute 'child: req-2'", str(ctx.exception))

    def test_multiple_child_lines_and_duplicates(self) -> None:
        """REQ-PARSER-9/99: Multiple 'child-of' lines are allowed, but duplicates must raise an error."""
        md = "> REQ-1\n> Test.\n> child-of: REQ-2\n> child-of: REQ-2\n> child-of: REQ-3"
        with self.assertRaises(ValueError) as ctx:
            parse_requirements_from_markdown(md)
        self.assertIn("Duplicate child ID 'REQ-2'", str(ctx.exception))

    def test_ignore_unknown_attributes(self) -> None:
        """REQ-PARSER-10: Unknown attributes in blockquotes now raise an error."""
        md = "> REQ-1\n> Test.\n> priority: high\n> foo: bar"
        with self.assertRaises(ValueError) as ctx:
            parse_requirements_from_markdown(md)
        self.assertIn("Unknown atttribute 'priority: high'", str(ctx.exception))

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
        """REQ-PARSER-14: Blockquotes that span multiple paragraphs (blank lines) now raise error for unknown attribute."""
        md = "> REQ-1\n> First line.\n>\n> Second paragraph."
        with self.assertRaises(ValueError) as ctx:
            parse_requirements_from_markdown(md)
        self.assertIn("Unknown atttribute 'second paragraph.'", str(ctx.exception))

    def test_circular_child_relationship(self) -> None:
        """REQ-PARSER-15: Raise error if a circular child relationship is detected."""
        md = (
            "> REQ-1\n> Test.\n> child-of: REQ-2\n\n> REQ-2\n> Test.\n> child-of: REQ-1"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            reqs_md = Path(tmpdir) / "reqs.md"
            reqs_md.write_text(md)
            with self.assertRaises(ValueError) as ctx:
                api_init(tmpdir)
            self.assertIn("Circular dependency detected", str(ctx.exception))

    def test_unicode_support(self) -> None:
        """REQ-PARSER-16: Only ASCII IDs are allowed; Unicode IDs should raise an error."""
        md = "> REQ-ÜNICODE-1\n> Some description.\n> child-of: ASCII-2"
        with self.assertRaises(ValueError):
            parse_requirements_from_markdown(md)

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


class TestStatusCommand(unittest.TestCase):
    """Unit and integration tests for the status command functionality."""

    def test_api_status_basic_functionality(self) -> None:
        """Test basic api_status functionality with simple requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = """
> REQ-1
> First requirement.
> completed

> REQ-2
> Second requirement.
> critical

> REQ-3
> Third requirement.
> critical
> completed
"""
            reqs_md = test_dir_path / "reqs.md"
            reqs_md.write_text(md_content)

            # Initialize first
            api_init(tmpdir)

            # Test status
            status_result = api_status(tmpdir)

            self.assertIsInstance(status_result, StatusResult)
            self.assertEqual(status_result.total_count, 3)
            self.assertEqual(status_result.completed_count, 2)
            self.assertEqual(status_result.critical_count, 2)
            self.assertEqual(status_result.critical_completed_count, 1)
            self.assertEqual(len(status_result.requirements), 3)

    def test_api_status_no_lockfile(self) -> None:
        """Test that api_status raises FileNotFoundError when lockfile doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError) as context:
                api_status(tmpdir)
            self.assertIn("requirements.lock not found", str(context.exception))

    def test_api_status_with_hierarchical_requirements(self) -> None:
        """Test api_status with parent-child relationships using valid ASCII IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = """
> REQ-1
> Parent requirement.
> critical

> REQ-2
> Child requirement 1.
> child-of: REQ-1
> completed

> REQ-3
> Child requirement 2.
> child-of: REQ-1
"""
            reqs_md = test_dir_path / "reqs.md"
            reqs_md.write_text(md_content)

            # Initialize first
            api_init(tmpdir)

            # Test status
            status_result = api_status(tmpdir)

            self.assertEqual(status_result.total_count, 3)
            self.assertEqual(status_result.completed_count, 1)
            self.assertEqual(status_result.critical_count, 1)
            self.assertEqual(status_result.critical_completed_count, 0)

            # Check that requirements have correct file associations
            req_ids = {pr.requirement.req_id for pr in status_result.requirements}
            self.assertEqual(req_ids, {"REQ-1", "REQ-2", "REQ-3"})

            # Check file associations
            for pr in status_result.requirements:
                self.assertEqual(pr.source_file, reqs_md)

    def test_api_status_multiple_files(self) -> None:
        """Test api_status with requirements spread across multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)

            # Create multiple files
            file1_content = "> REQ-1\n> First file requirement.\n> completed\n"
            file1 = test_dir_path / "file1.md"
            file1.write_text(file1_content)

            file2_content = "> REQ-2\n> Second file requirement.\n> critical\n"
            file2 = test_dir_path / "file2.md"
            file2.write_text(file2_content)

            # Initialize first
            api_init(tmpdir)

            # Test status
            status_result = api_status(tmpdir)

            self.assertEqual(status_result.total_count, 2)
            self.assertEqual(status_result.completed_count, 1)
            self.assertEqual(status_result.critical_count, 1)

            # Check file associations
            file1_reqs = [
                pr for pr in status_result.requirements if pr.source_file == file1
            ]
            file2_reqs = [
                pr for pr in status_result.requirements if pr.source_file == file2
            ]

            self.assertEqual(len(file1_reqs), 1)
            self.assertEqual(len(file2_reqs), 1)
            self.assertEqual(file1_reqs[0].requirement.req_id, "REQ-1")
            self.assertEqual(file2_reqs[0].requirement.req_id, "REQ-2")

    def test_cli_status_output(self) -> None:
        """Test that the CLI status command produces expected output."""
        require_py = str(Path(__file__).parent / "require.py")

        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = """
> REQ-1
> First requirement.
> completed

> REQ-2
> Second requirement.
> critical
"""
            md_path = test_dir_path / "reqs.md"
            md_path.write_text(md_content)

            # Run init
            subprocess.run(
                [sys.executable, require_py, "init"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
            )

            # Run status and capture output
            result = subprocess.run(
                [sys.executable, require_py, "status"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0)
            output = result.stdout

            # Check for expected content
            self.assertIn("📊 Requirements Status Summary:", output)
            self.assertIn("Total requirements: 2", output)
            self.assertIn("Completed: 1/2 (50.0%)", output)
            self.assertIn("Critical requirements: 1", output)
            self.assertIn("📁 Requirements by File:", output)
            self.assertIn("🌳 Hierarchical Status:", output)
            self.assertIn("REQ-1: First requirement.", output)
            self.assertIn("REQ-2: Second requirement.", output)

    def test_cli_status_no_lockfile(self) -> None:
        """Test that CLI status command handles missing lockfile gracefully."""
        require_py = str(Path(__file__).parent / "require.py")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Run status without init
            result = subprocess.run(
                [sys.executable, require_py, "status"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("requirements.lock not found", result.stdout)

    def test_status_with_empty_requirements(self) -> None:
        """Test status functionality with no requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = "# No requirements here\nJust some text.\n"
            reqs_md = test_dir_path / "reqs.md"
            reqs_md.write_text(md_content)

            # Initialize first
            api_init(tmpdir)

            # Test status
            status_result = api_status(tmpdir)

            self.assertEqual(status_result.total_count, 0)
            self.assertEqual(status_result.completed_count, 0)
            self.assertEqual(status_result.critical_count, 0)
            self.assertEqual(status_result.critical_completed_count, 0)
            self.assertEqual(len(status_result.requirements), 0)

    def test_cli_status_md_output(self) -> None:
        """Test that the CLI status-md command produces a Markdown file with correct content."""
        require_py = str(Path(__file__).parent / "require.py")
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = """
> REQ-1
> First requirement.
> completed

> REQ-2
> Second requirement.
> critical
"""
            md_path = test_dir_path / "reqs.md"
            md_path.write_text(md_content)

            # Run init to create requirements.lock
            subprocess.run(
                [sys.executable, require_py, "init"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
            )

            # Run status-md to generate Markdown status file
            output_file = test_dir_path / "requirements-status.md"
            result = subprocess.run(
                [sys.executable, require_py, "status-md", "-o", str(output_file)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue(output_file.exists())
            md = output_file.read_text(encoding="utf-8")
            # Check for expected Markdown content
            self.assertIn("# Requirements Status Report", md)
            self.assertIn("## Summary", md)
            self.assertIn("REQ-1", md)
            self.assertIn("REQ-2", md)
            self.assertIn("Completed:", md)
            self.assertIn("Hierarchical Status", md)

    def test_completed_parent_with_incomplete_child_fails(self) -> None:
        """REQ-CORE-7: Parent cannot be completed unless all children are completed."""
        md = "> REQ-1\n> Child.\n> child-of: REQ-2\n\n> REQ-2\n> Parent.\n> completed\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            reqs_md = Path(tmpdir) / "reqs.md"
            reqs_md.write_text(md)
            with self.assertRaises(ValueError) as ctx:
                api_init(tmpdir)
            self.assertIn("REQ-2", str(ctx.exception))
            self.assertIn("REQ-1", str(ctx.exception))

    def test_completed_parent_with_completed_child_passes(self) -> None:
        """REQ-CORE-7: Parent can be completed if all children are completed."""
        md = "> REQ-1\n> Parent.\n> completed\n> child-of: REQ-2\n\n> REQ-2\n> Child.\n> completed\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            reqs_md = Path(tmpdir) / "reqs.md"
            reqs_md.write_text(md)
            # Should not raise
            api_init(tmpdir)

    def test_visual_dot_generation(self) -> None:
        """REQ-VISUAL-1: The tool shall generate a Graphviz dot file from requirements.lock."""
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir_path = Path(tmpdir)
            md_content = "> REQ-1\n> Parent.\n\n> REQ-2\n> Child.\n> child-of: REQ-1\n"
            reqs_md = test_dir_path / "reqs.md"
            reqs_md.write_text(md_content)
            # Generate lockfile
            subprocess.run(
                [sys.executable, str(Path(__file__).parent / "require.py"), "init"],
                cwd=tmpdir,
                check=True,
            )
            # Generate dot file
            dot_file = test_dir_path / "requirements-visual.dot"
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).parent / "require.py"),
                    "visual-dot",
                    "-o",
                    str(dot_file),
                ],
                cwd=tmpdir,
                check=True,
            )
            dot = dot_file.read_text(encoding="utf-8")
            self.assertIn("digraph requirements", dot)
            self.assertIn('"REQ-1"', dot)
            self.assertIn('"REQ-2"', dot)
            self.assertIn('"REQ-1" -> "REQ-2"', dot)


if __name__ == "__main__":
    unittest.main()
