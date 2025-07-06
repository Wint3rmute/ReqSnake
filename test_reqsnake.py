"""Unit and integration tests for ReqSnake requirements management tool."""

import shutil
import tempfile
import unittest
from pathlib import Path

from mkdocs.exceptions import PluginError

from mkdocs_reqsnake.models import Requirement
from mkdocs_reqsnake.parser import (
    parse_requirements_from_files,
    parse_requirements_from_markdown,
)
from mkdocs_reqsnake.utils import load_ignore_patterns, should_ignore_file
from mkdocs_reqsnake.validator import validate_requirements


class TestRequirementParser(unittest.TestCase):
    """Unit tests for the requirement Markdown parser."""

    def test_single_requirement(self) -> None:
        """Test parsing a single requirement with critical and children."""
        md = (
            "> MECH-123\n> The wing must withstand 5g load.\n>\n> critical\n"
            "> child-of: MECH-54\n> child-of: MECH-57"
        )
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(
            reqs[0],
            Requirement(
                req_id="MECH-123",
                description="The wing must withstand 5g load.",
                critical=True,
                parents=["MECH-54", "MECH-57"],
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
                parents=["MECH-54"],
            ),
        )
        self.assertEqual(
            reqs[1],
            Requirement(
                req_id="AVIO-15",
                description="Avionics must support dual redundancy.",
                critical=False,
                parents=["AVIO-16"],
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
                parents=[],
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

    def test_duplicate_ids_same_file(self) -> None:
        """Test that duplicate requirement IDs in the same file raise a ValueError."""
        md = """
> MECH-123
> The wing must withstand 5g load.
>
> critical

> MECH-123
> Another requirement with the same ID.
"""
        file_data = [("test.md", md)]
        with self.assertRaises(PluginError) as context:
            parsed_reqs = parse_requirements_from_files(file_data)
            validate_requirements(parsed_reqs)
        self.assertIn(
            "Duplicate requirement ID 'MECH-123' found", str(context.exception)
        )

    def test_child_of_syntax(self) -> None:
        """Test that 'child-of' is supported as a child relationship key."""
        md = (
            "> REQ-1\n> Parent requirement.\n> child-of REQ-2\n"
            "> child-of: REQ-3\n> CHILD-OF req-5\n> child-of: REQ-6\n"
        )
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(
            set(reqs[0].parents),
            {"REQ-2", "REQ-3", "req-5", "REQ-6"},
        )

    def test_normal_blockquote(self) -> None:
        """Test markdown blockquotes not containing requirements are skipped."""
        md = """
# Some markdown content

A bit of text

> A blockquote
> with multiple
> lines

Moar text!
        """
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 0)

    def test_child_of_whitespace_and_case(self) -> None:
        """Test that 'child-of' is parsed case-insensitively and trims whitespace."""
        md = (
            "> REQ-1\n> Parent.\n>   CHILD-OF:   REQ-2   \n"
            "> child-of   REQ-3\n> child-OF:REQ-4\n"
        )
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(
            set(reqs[0].parents),
            {"REQ-2", "REQ-3", "REQ-4"},
        )

    def test_duplicate_child_ids_error(self) -> None:
        """REQ-PARSER-99: Parser raises errors on duplicated 'child-of' lines."""
        # Duplicate via 'child-of' (exact)
        md = "> REQ-1\n> Parent.\n> child-of: REQ-2\n> child-of: REQ-2\n"
        with self.assertRaises(PluginError) as ctx:
            parse_requirements_from_markdown(md)
        self.assertIn("Duplicate parent ID", str(ctx.exception))
        # Duplicate across 'child-of' forms (case-insensitive)
        md2 = "> REQ-1\n> Parent.\n> child-of REQ-2\n> child-of: req-2\n"
        with self.assertRaises(PluginError) as ctx:
            parse_requirements_from_markdown(md2)
        self.assertIn("Duplicate parent ID", str(ctx.exception))
        # Duplicate with whitespace differences
        md3 = "> REQ-1\n> Parent.\n> child-of:   REQ-2   \n> child-of: REQ-2\n"
        with self.assertRaises(PluginError) as ctx:
            parse_requirements_from_markdown(md3)
        self.assertIn("Duplicate parent ID", str(ctx.exception))

    def test_multiple_child_lines_and_duplicates(self) -> None:
        """REQ-PARSER-9/99: Multiple 'child-of' lines allowed, duplicates error."""
        md = "> REQ-1\n> Test.\n> child-of: REQ-2\n> child-of: REQ-2\n> child-of: REQ-3"
        with self.assertRaises(PluginError) as ctx:
            parse_requirements_from_markdown(md)
        self.assertIn("Duplicate parent ID 'REQ-2'", str(ctx.exception))

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
            "> REQ-abc\n> Invalid.\n",  # non-numeric suffix
            "> REQ-12.3\n> Invalid.\n",  # decimal not allowed
            "> REQ-12a\n> Invalid.\n",  # mixed alphanumeric suffix
            "> REQ-12A\n> Invalid.\n",  # number not integer
            "> _REQ-1\n> Invalid.\n",  # starts with underscore
            "> 1REQ-1\n> Invalid.\n",  # starts with number
        ]
        for md in invalid_cases:
            with self.assertRaises(PluginError, msg=md):
                parse_requirements_from_markdown(md)

    def test_ascii_only_ids(self) -> None:
        """REQ-CORE-6: IDs must contain only ASCII characters."""
        # Valid ASCII IDs
        valid_md = "> REQ-1\n> Valid.\n\n> SW-33\n> Valid.\n"
        reqs = parse_requirements_from_markdown(valid_md)
        self.assertEqual(len(reqs), 2)
        # Invalid non-ASCII IDs
        invalid_cases = [
            "> RÉQ-1\n> Invalid.\n",  # accented character
            "> REQ-1\n> Valid.\n\n> SW-33\n> Valid.\n\n> RÉQ-2\n> Invalid.\n",  # mixed
        ]
        for invalid_md in invalid_cases:
            with self.assertRaises(PluginError) as ctx:
                parse_requirements_from_markdown(invalid_md)
            self.assertIn("contains non-ASCII characters", str(ctx.exception))

    def test_unknown_attributes_raise_error(self) -> None:
        """REQ-PARSER-10: Unknown attributes should raise PluginError."""
        md = "> REQ-1\n> Test.\n> unknown-attr\n"
        with self.assertRaises(PluginError) as ctx:
            parse_requirements_from_markdown(md)
        self.assertIn("Unknown attribute 'unknown-attr'", str(ctx.exception))
        self.assertIn("REQ-1", str(ctx.exception))

    def test_circular_dependency_detection(self) -> None:
        """REQ-PARSER-15: Circular dependencies should be detected."""
        md = (
            "> REQ-1\n> Parent.\n> child-of: REQ-2\n\n"
            "> REQ-2\n> Child.\n> child-of: REQ-1\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with self.assertRaises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        self.assertIn("Circular dependency detected", str(ctx.exception))

    def test_missing_parent_validation(self) -> None:
        """REQ-CORE-8: Missing parent references should raise MissingParentError."""
        md = (
            "> REQ-1\n> Child requirement.\n> child-of: REQ-MISSING\n\n"
            "> REQ-2\n> Another requirement.\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with self.assertRaises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        self.assertIn(
            "references non-existing parent 'REQ-MISSING'", str(ctx.exception)
        )

    def test_multiple_missing_parents_validation(self) -> None:
        """REQ-CORE-8: Multiple missing parents should be caught."""
        md = (
            "> REQ-1\n> Child requirement.\n> child-of: REQ-MISSING1\n"
            "> child-of: REQ-MISSING2\n\n"
            "> REQ-2\n> Another requirement.\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with self.assertRaises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        # Should catch the first missing parent
        self.assertIn("references non-existing parent", str(ctx.exception))

    def test_valid_parent_references_pass(self) -> None:
        """REQ-CORE-8: Valid parent references should not raise errors."""
        md = (
            "> REQ-1\n> Parent requirement.\n\n"
            "> REQ-2\n> Child requirement.\n> child-of: REQ-1\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        # Should not raise an exception
        validate_requirements(parsed_reqs)

    def test_completed_parent_with_incomplete_child_fails(self) -> None:
        """REQ-CORE-7: Completed requirements with incomplete children raise error."""
        md = "> REQ-1\n> Parent.\n> completed\n\n> REQ-2\n> Child.\n> child-of: REQ-1\n"
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with self.assertRaises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        self.assertIn(
            "are marked as completed but have incomplete children", str(ctx.exception)
        )

    def test_completed_parent_with_completed_child_passes(self) -> None:
        """REQ-CORE-7: Completed requirements with completed children should pass."""
        md = (
            "> REQ-1\n> Parent.\n> completed\n> child-of: REQ-2\n\n"
            "> REQ-2\n> Child.\n> completed\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        # Should not raise an exception
        validate_requirements(parsed_reqs)


class TestRequirementPrettyString(unittest.TestCase):
    """Unit tests for the requirement pretty string formatting."""

    def test_pretty_string_variants(self) -> None:
        """Test that to_pretty_string() generates correct output for various states."""
        # Basic requirement
        req = Requirement("REQ-1", "Basic requirement")
        expected = "REQ-1: Basic requirement\n\n"
        self.assertEqual(req.to_pretty_string(), expected)

        # Critical requirement
        req = Requirement("REQ-2", "Critical requirement", critical=True)
        expected = "REQ-2: Critical requirement\n\n**⚠️ critical**\n\n"
        self.assertEqual(req.to_pretty_string(), expected)

        # Completed requirement
        req = Requirement("REQ-3", "Completed requirement", completed=True)
        expected = "REQ-3: Completed requirement\n\n✅ completed\n\n"
        self.assertEqual(req.to_pretty_string(), expected)

        # Requirement with children
        req = Requirement("REQ-4", "Parent requirement", parents=["REQ-5", "REQ-6"])
        expected = "REQ-4: Parent requirement\n\n### Parents\n\n- REQ-5\n- REQ-6\n"
        self.assertEqual(req.to_pretty_string(), expected)

        # Complete requirement (critical, completed, with children)
        req = Requirement(
            "REQ-7",
            "Complete requirement",
            critical=True,
            completed=True,
            parents=["REQ-8"],
        )
        expected = (
            "REQ-7: Complete requirement\n\n**⚠️ critical**\n\n"
            "✅ completed\n\n### Parents\n\n- REQ-8\n"
        )
        self.assertEqual(req.to_pretty_string(), expected)


class TestRequirementParserEdgeCases(unittest.TestCase):
    """Unit tests for edge cases in the requirement parser."""

    def test_ignore_blockquotes_with_only_id_or_description(self) -> None:
        """REQ-PARSER-6: Blockquotes with only ID or description ignored."""
        md = "> REQ-1\n\n> Just a description\n\n> REQ-2\n> Valid requirement\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].req_id, "REQ-2")

    def test_ignore_extra_blank_lines_and_whitespace(self) -> None:
        """Test that extra blank lines and whitespace are handled correctly."""
        md = "> REQ-1\n> \n> Description\n> \n> \n> critical\n> \n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].req_id, "REQ-1")
        self.assertEqual(reqs[0].description, "Description")
        self.assertTrue(reqs[0].critical)

    def test_attribute_keywords_case_and_spaces(self) -> None:
        """Test that attribute keywords are case-insensitive and handle whitespace."""
        md = "> REQ-1\n> Test.\n> CRITICAL\n> COMPLETED\n> CHILD-OF: REQ-2\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertTrue(reqs[0].critical)
        self.assertTrue(reqs[0].completed)
        self.assertEqual(reqs[0].parents, ["REQ-2"])

    def test_multiple_child_lines_and_duplicates(self) -> None:
        """Test multiple child-of lines and duplicate detection."""
        md = "> REQ-1\n> Test.\n> child-of: REQ-2\n> child-of: REQ-3\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(set(reqs[0].parents), {"REQ-2", "REQ-3"})

    def test_unknown_attributes_with_value_raise_error(self) -> None:
        """Test that unknown attributes with values also raise PluginError."""
        md = "> REQ-1\n> Test.\n> unknown-attr: some value\n"
        with self.assertRaises(PluginError) as ctx:
            parse_requirements_from_markdown(md)
        self.assertIn(
            "Unknown attribute 'unknown-attr: some value'", str(ctx.exception)
        )
        self.assertIn("REQ-1", str(ctx.exception))

    def test_case_sensitive_ids(self) -> None:
        """Test that requirement IDs are case-sensitive."""
        md = "> REQ-1\n> First.\n\n> req-1\n> Second.\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 2)
        self.assertEqual(reqs[0].req_id, "REQ-1")
        self.assertEqual(reqs[1].req_id, "req-1")

    def test_inconsistent_blockquote_lines(self) -> None:
        """Test lines without '>' break blocks, invalid attributes raise errors."""
        # Lines without '>' break blockquote blocks (REQ-PARSER-12)
        # This creates two separate blocks: one complete requirement and one invalid
        md = "> REQ-1\n> Description\n> critical\nNot a blockquote\n> completed\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)  # Only the complete requirement is parsed
        self.assertEqual(reqs[0].req_id, "REQ-1")
        self.assertEqual(reqs[0].description, "Description")
        self.assertTrue(reqs[0].critical)
        self.assertFalse(
            reqs[0].completed
        )  # 'completed' is in a separate block that gets ignored

        # But invalid attributes in blockquotes should raise errors (REQ-PARSER-10)
        md_with_invalid = (
            "> REQ-1\n> Description\n> critical\n> Not a valid attribute\n> completed\n"
        )
        with self.assertRaises(PluginError):
            parse_requirements_from_markdown(md_with_invalid)

    def test_ignore_markdown_formatting(self) -> None:
        """Test that markdown formatting in descriptions is preserved."""
        md = "> REQ-1\n> Description with **bold** and *italic* text.\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(
            reqs[0].description, "Description with **bold** and *italic* text."
        )

    def test_circular_child_relationship(self) -> None:
        """Test that circular child relationships are detected."""
        md = (
            "> REQ-1\n> Parent.\n> child-of: REQ-2\n\n"
            "> REQ-2\n> Child.\n> child-of: REQ-1\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with self.assertRaises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        self.assertIn("Circular dependency detected", str(ctx.exception))

    def test_unicode_support(self) -> None:
        """Test that unicode characters in descriptions are supported."""
        md = "> REQ-1\n> Description with unicode: café, naïve, 你好\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(
            reqs[0].description, "Description with unicode: café, naïve, 你好"
        )

    def test_ignore_blockquotes_in_comments(self) -> None:
        """REQ-PARSER-17: HTML comments should be ignored."""
        md = """
<!-- This is a comment with > REQ-1 > Description -->
> REQ-1
> Real requirement
> critical
"""
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].req_id, "REQ-1")
        self.assertTrue(reqs[0].critical)

    def test_mixed_line_endings_and_whitespace(self) -> None:
        """Test that mixed line endings and whitespace are handled correctly."""
        md = "> REQ-1\r\n> Description\r\n> critical\r\n"
        reqs = parse_requirements_from_markdown(md)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0].req_id, "REQ-1")
        self.assertEqual(reqs[0].description, "Description")
        self.assertTrue(reqs[0].critical)


class TestIgnoreFunctionality(unittest.TestCase):
    """Unit tests for .requirementsignore functionality."""

    def setUp(self) -> None:
        """Set up temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_load_ignore_patterns_no_file(self) -> None:
        """Test load_ignore_patterns when .requirementsignore doesn't exist."""
        patterns = load_ignore_patterns(self.temp_path)
        self.assertEqual(patterns, [])

    def test_load_ignore_patterns_empty_file(self) -> None:
        """Test load_ignore_patterns with empty .requirementsignore file."""
        ignore_file = self.temp_path / ".requirementsignore"
        ignore_file.write_text("")

        patterns = load_ignore_patterns(self.temp_path)
        self.assertEqual(patterns, [])

    def test_load_ignore_patterns_with_content(self) -> None:
        """Test load_ignore_patterns with various patterns."""
        ignore_content = """# Comment line
*.tmp
*~

build/
dist/
example.md
test_*.md
"""
        ignore_file = self.temp_path / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        patterns = load_ignore_patterns(self.temp_path)
        expected = ["*.tmp", "*~", "build/", "dist/", "example.md", "test_*.md"]
        self.assertEqual(patterns, expected)

    def test_load_ignore_patterns_comments_and_blanks(self) -> None:
        """Test that comments and blank lines are ignored."""
        ignore_content = """# This is a comment
*.tmp
# Another comment

# Empty line above
build/
"""
        ignore_file = self.temp_path / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        patterns = load_ignore_patterns(self.temp_path)
        expected = ["*.tmp", "build/"]
        self.assertEqual(patterns, expected)

    def test_load_ignore_patterns_unicode_error(self) -> None:
        """Test load_ignore_patterns handles unicode decode errors gracefully."""
        ignore_file = self.temp_path / ".requirementsignore"
        # Write binary data that would cause decode error
        with ignore_file.open("wb") as f:
            f.write(b"\xff\xfe\x00\x00")

        patterns = load_ignore_patterns(self.temp_path)
        self.assertEqual(patterns, [])

    def test_should_ignore_file_no_patterns(self) -> None:
        """Test should_ignore_file with empty patterns list."""
        self.assertFalse(should_ignore_file("any/file.md", []))

    def test_should_ignore_file_exact_match(self) -> None:
        """Test should_ignore_file with exact filename matches."""
        patterns = ["example.md", "README.txt"]

        self.assertTrue(should_ignore_file("example.md", patterns))
        self.assertTrue(should_ignore_file("path/to/example.md", patterns))
        self.assertFalse(should_ignore_file("other.md", patterns))

    def test_should_ignore_file_glob_patterns(self) -> None:
        """Test should_ignore_file with glob patterns."""
        patterns = ["*.tmp", "test_*.md", ".*"]

        self.assertTrue(should_ignore_file("file.tmp", patterns))
        self.assertTrue(should_ignore_file("path/file.tmp", patterns))
        self.assertTrue(should_ignore_file("test_example.md", patterns))
        self.assertTrue(should_ignore_file("path/test_example.md", patterns))
        self.assertTrue(should_ignore_file(".hidden", patterns))
        self.assertFalse(should_ignore_file("normal.md", patterns))

    def test_should_ignore_file_directory_patterns(self) -> None:
        """Test should_ignore_file with directory patterns."""
        patterns = ["build/", "node_modules/", "dist/"]

        self.assertTrue(should_ignore_file("build/output.md", patterns))
        self.assertTrue(should_ignore_file("project/build/file.md", patterns))
        self.assertTrue(should_ignore_file("node_modules/package/readme.md", patterns))
        self.assertFalse(should_ignore_file("src/file.md", patterns))
        self.assertFalse(should_ignore_file("buildfile.md", patterns))

    def test_should_ignore_file_mixed_patterns(self) -> None:
        """Test should_ignore_file with mixed pattern types."""
        patterns = ["*.tmp", "build/", "example.md", "test_*"]

        # File patterns
        self.assertTrue(should_ignore_file("file.tmp", patterns))
        self.assertTrue(should_ignore_file("example.md", patterns))

        # Directory patterns
        self.assertTrue(should_ignore_file("build/file.md", patterns))

        # Glob patterns
        self.assertTrue(should_ignore_file("test_something", patterns))

        # Should not be ignored
        self.assertFalse(should_ignore_file("normal.md", patterns))
        self.assertFalse(should_ignore_file("src/normal.md", patterns))

    def test_should_ignore_file_path_normalization(self) -> None:
        """Test that paths with different separators are handled correctly."""
        patterns = ["build/", "*.tmp"]

        # Test with different path separators
        self.assertTrue(should_ignore_file("build\\file.md", patterns))
        self.assertTrue(should_ignore_file("build/file.md", patterns))
        self.assertTrue(should_ignore_file("path\\to\\file.tmp", patterns))
        self.assertTrue(should_ignore_file("path/to/file.tmp", patterns))


if __name__ == "__main__":
    unittest.main()
