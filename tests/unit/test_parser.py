"""Unit tests for the requirement parser."""

import pytest
from mkdocs.exceptions import PluginError

from mkdocs_reqsnake.models import Requirement
from mkdocs_reqsnake.parser import (
    parse_requirements_from_files,
    parse_requirements_from_markdown,
)


class TestRequirementParser:
    """Unit tests for the requirement Markdown parser."""

    def test_single_requirement(self):
        """Test parsing a single requirement with critical and children."""
        md = (
            "> MECH-123\n> The wing must withstand 5g load.\n>\n> critical\n"
            "> child-of: MECH-54\n> child-of: MECH-57"
        )
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert reqs[0] == Requirement(
            req_id="MECH-123",
            description="The wing must withstand 5g load.",
            critical=True,
            parents=["MECH-54", "MECH-57"],
        )

    def test_multiple_requirements(self):
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
        assert len(reqs) == 2
        assert reqs[0] == Requirement(
            req_id="MECH-123",
            description="The wing must withstand 5g load.",
            critical=True,
            parents=["MECH-54"],
        )
        assert reqs[1] == Requirement(
            req_id="AVIO-15",
            description="Avionics must support dual redundancy.",
            critical=False,
            parents=["AVIO-16"],
        )

    def test_no_critical_or_children(self):
        """Test parsing a requirement with no critical or children fields."""
        md = """
> SW-33
> On-board software for the plane.
"""
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert reqs[0] == Requirement(
            req_id="SW-33",
            description="On-board software for the plane.",
            critical=False,
            parents=[],
        )

    def test_ignores_non_blockquotes(self):
        """Test that non-blockquote content is ignored by the parser."""
        md = """
# Not a requirement
Some text.

> MECH-123
> The wing must withstand 5g load.
> critical
"""
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert reqs[0].req_id == "MECH-123"

    def test_child_of_syntax(self):
        """Test that 'child-of' is supported as a child relationship key."""
        md = (
            "> REQ-1\n> Parent requirement.\n> child-of REQ-2\n"
            "> child-of: REQ-3\n> CHILD-OF req-5\n> child-of: REQ-6\n"
        )
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert set(reqs[0].parents) == {"REQ-2", "REQ-3", "req-5", "REQ-6"}

    def test_normal_blockquote(self):
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
        assert len(reqs) == 0

    def test_child_of_whitespace_and_case(self):
        """Test that 'child-of' is parsed case-insensitively and trims whitespace."""
        md = (
            "> REQ-1\n> Parent.\n>   CHILD-OF:   REQ-2   \n"
            "> child-of   REQ-3\n> child-OF:REQ-4\n"
        )
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert set(reqs[0].parents) == {"REQ-2", "REQ-3", "REQ-4"}

    def test_duplicate_child_ids_error(self):
        """REQ-PARSER-99: Parser raises errors on duplicated 'child-of' lines."""
        # Duplicate via 'child-of' (exact)
        md = "> REQ-1\n> Parent.\n> child-of: REQ-2\n> child-of: REQ-2\n"
        with pytest.raises(PluginError) as ctx:
            parse_requirements_from_markdown(md)
        assert "Duplicate parent ID" in str(ctx.value)

        # Duplicate across 'child-of' forms (case-insensitive)
        md2 = "> REQ-1\n> Parent.\n> child-of REQ-2\n> child-of: req-2\n"
        with pytest.raises(PluginError) as ctx:
            parse_requirements_from_markdown(md2)
        assert "Duplicate parent ID" in str(ctx.value)

        # Duplicate with whitespace differences
        md3 = "> REQ-1\n> Parent.\n> child-of:   REQ-2   \n> child-of: REQ-2\n"
        with pytest.raises(PluginError) as ctx:
            parse_requirements_from_markdown(md3)
        assert "Duplicate parent ID" in str(ctx.value)

    def test_requirement_id_format_enforced(self):
        """REQ-CORE-6: IDs must be in the form <STRING>-<NUMBER>."""
        # Valid IDs
        valid_md = "> REQ-1\n> Valid.\n\n> SW-33\n> Valid.\n\n> A-0\n> Valid.\n"
        reqs = parse_requirements_from_markdown(valid_md)
        assert len(reqs) == 3

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
            with pytest.raises(PluginError):
                parse_requirements_from_markdown(md)

    def test_ascii_only_ids(self):
        """REQ-CORE-6: IDs must contain only ASCII characters."""
        # Valid ASCII IDs
        valid_md = "> REQ-1\n> Valid.\n\n> SW-33\n> Valid.\n"
        reqs = parse_requirements_from_markdown(valid_md)
        assert len(reqs) == 2

        # Invalid non-ASCII IDs
        invalid_cases = [
            "> RÉQ-1\n> Invalid.\n",  # accented character
            "> REQ-1\n> Valid.\n\n> SW-33\n> Valid.\n\n> RÉQ-2\n> Invalid.\n",  # mixed
        ]
        for invalid_md in invalid_cases:
            with pytest.raises(PluginError) as ctx:
                parse_requirements_from_markdown(invalid_md)
            assert "contains non-ASCII characters" in str(ctx.value)

    def test_unknown_attributes_raise_error(self):
        """REQ-PARSER-10: Unknown attributes should raise PluginError."""
        md = "> REQ-1\n> Test.\n> unknown-attr\n"
        with pytest.raises(PluginError) as ctx:
            parse_requirements_from_markdown(md)
        assert "Unknown attribute 'unknown-attr'" in str(ctx.value)
        assert "REQ-1" in str(ctx.value)

    def test_unknown_attributes_with_value_raise_error(self):
        """Test that unknown attributes with values also raise PluginError."""
        md = "> REQ-1\n> Test.\n> unknown-attr: some value\n"
        with pytest.raises(PluginError) as ctx:
            parse_requirements_from_markdown(md)
        assert "Unknown attribute 'unknown-attr: some value'" in str(ctx.value)
        assert "REQ-1" in str(ctx.value)


class TestRequirementParserEdgeCases:
    """Unit tests for edge cases in the requirement parser."""

    def test_ignore_blockquotes_with_only_id_or_description(self):
        """REQ-PARSER-6: Blockquotes with only ID or description ignored."""
        md = "> REQ-1\n\n> Just a description\n\n> REQ-2\n> Valid requirement\n"
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert reqs[0].req_id == "REQ-2"

    def test_ignore_extra_blank_lines_and_whitespace(self):
        """Test that extra blank lines and whitespace are handled correctly."""
        md = "> REQ-1\n> \n> Description\n> \n> \n> critical\n> \n"
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert reqs[0].req_id == "REQ-1"
        assert reqs[0].description == "Description"
        assert reqs[0].critical is True

    def test_attribute_keywords_case_and_spaces(self):
        """Test that attribute keywords are case-insensitive and handle whitespace."""
        md = "> REQ-1\n> Test.\n> CRITICAL\n> COMPLETED\n> CHILD-OF: REQ-2\n"
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert reqs[0].critical is True
        assert reqs[0].completed is True
        assert reqs[0].parents == ["REQ-2"]

    def test_case_sensitive_ids(self):
        """Test that requirement IDs are case-sensitive."""
        md = "> REQ-1\n> First.\n\n> req-1\n> Second.\n"
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 2
        assert reqs[0].req_id == "REQ-1"
        assert reqs[1].req_id == "req-1"

    def test_inconsistent_blockquote_lines(self):
        """Test lines without '>' break blocks, invalid attributes raise errors."""
        # Lines without '>' break blockquote blocks (REQ-PARSER-12)
        # This creates two separate blocks: one complete requirement and one invalid
        md = "> REQ-1\n> Description\n> critical\nNot a blockquote\n> completed\n"
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1  # Only the complete requirement is parsed
        assert reqs[0].req_id == "REQ-1"
        assert reqs[0].description == "Description"
        assert reqs[0].critical is True
        assert (
            reqs[0].completed is False
        )  # 'completed' is in a separate block that gets ignored

        # But invalid attributes in blockquotes should raise errors (REQ-PARSER-10)
        md_with_invalid = (
            "> REQ-1\n> Description\n> critical\n> Not a valid attribute\n> completed\n"
        )
        with pytest.raises(PluginError):
            parse_requirements_from_markdown(md_with_invalid)

    def test_ignore_markdown_formatting(self):
        """Test that markdown formatting in descriptions is preserved."""
        md = "> REQ-1\n> Description with **bold** and *italic* text.\n"
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert reqs[0].description == "Description with **bold** and *italic* text."

    def test_unicode_support(self):
        """Test that unicode characters in descriptions are supported."""
        md = "> REQ-1\n> Description with unicode: café, naïve, 你好\n"
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert reqs[0].description == "Description with unicode: café, naïve, 你好"

    def test_ignore_blockquotes_in_comments(self):
        """REQ-PARSER-17: HTML comments should be ignored."""
        md = """
<!-- This is a comment with > REQ-1 > Description -->
> REQ-1
> Real requirement
> critical
"""
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert reqs[0].req_id == "REQ-1"
        assert reqs[0].critical is True

    def test_mixed_line_endings_and_whitespace(self):
        """Test that mixed line endings and whitespace are handled correctly."""
        md = "> REQ-1\r\n> Description\r\n> critical\r\n"
        reqs = parse_requirements_from_markdown(md)
        assert len(reqs) == 1
        assert reqs[0].req_id == "REQ-1"
        assert reqs[0].description == "Description"
        assert reqs[0].critical is True


class TestRequirementFileParser:
    """Unit tests for parsing requirements from multiple files."""

    def test_duplicate_ids_across_files(self):
        """Test that duplicate requirement IDs across files raise an error."""
        md = """
> MECH-123
> The wing must withstand 5g load.
>
> critical

> MECH-123
> Another requirement with the same ID.
"""
        file_data = [("test.md", md)]
        with pytest.raises(PluginError) as context:
            parsed_reqs = parse_requirements_from_files(file_data)
        # Note: This will be caught during validation, not parsing
        # But we should still test the integration
