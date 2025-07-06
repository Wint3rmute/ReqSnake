"""Unit tests for content generation."""

from mkdocs_reqsnake.generator import (
    generate_requirement_index_content,
    generate_requirement_page_content,
)
from tests.fixtures.sample_requirements import (
    SAMPLE_PARSED_REQUIREMENTS,
    create_sample_parsed_requirement,
)


class TestRequirementPageGeneration:
    """Unit tests for individual requirement page generation."""

    def test_basic_requirement_page(self):
        """Test generation of a basic requirement page."""
        parsed_req = create_sample_parsed_requirement(
            "REQ-1", "Test requirement", "test.md"
        )
        content = generate_requirement_page_content(parsed_req, [parsed_req])

        assert "# REQ-1" in content
        assert "Test requirement" in content
        assert "*Source: [test.md](../../test.md)*" in content

    def test_critical_requirement_page(self):
        """Test generation of a critical requirement page."""
        parsed_req = create_sample_parsed_requirement(
            "REQ-1", "Critical requirement", "test.md", critical=True
        )
        content = generate_requirement_page_content(parsed_req, [parsed_req])

        assert "⚠️ **Critical requirement**" in content

    def test_completed_requirement_page(self):
        """Test generation of a completed requirement page."""
        parsed_req = create_sample_parsed_requirement(
            "REQ-1", "Completed requirement", "test.md", completed=True
        )
        content = generate_requirement_page_content(parsed_req, [parsed_req])

        assert "✅ **Completed**" in content

    def test_requirement_with_parents(self):
        """Test generation of requirement page with parents."""
        parent = create_sample_parsed_requirement("REQ-0", "Parent requirement")
        child = create_sample_parsed_requirement(
            "REQ-1", "Child requirement", parents=["REQ-0"]
        )

        content = generate_requirement_page_content(child, [parent, child])

        assert "## Parents" in content
        assert "[REQ-0](../REQ/REQ-0.md)" in content
        assert "Parent requirement" in content

    def test_requirement_with_children(self):
        """Test generation of requirement page with children."""
        parent = create_sample_parsed_requirement("REQ-0", "Parent requirement")
        child = create_sample_parsed_requirement(
            "REQ-1", "Child requirement", parents=["REQ-0"]
        )

        content = generate_requirement_page_content(parent, [parent, child])

        assert "## Children" in content
        assert "[REQ-1](../REQ/REQ-1.md)" in content
        assert "Child requirement" in content

    def test_children_mindmap_generation(self):
        """Test generation of children mindmap."""
        parent = create_sample_parsed_requirement("REQ-0", "Parent requirement")
        child1 = create_sample_parsed_requirement(
            "REQ-1", "First child requirement", parents=["REQ-0"]
        )
        child2 = create_sample_parsed_requirement(
            "REQ-2", "Second child requirement", parents=["REQ-0"]
        )

        all_reqs = [parent, child1, child2]
        content = generate_requirement_page_content(parent, all_reqs)

        assert "## Children Mindmap" in content
        assert "```mermaid" in content
        assert "mindmap" in content
        assert 'root(("`REQ-0`"))' in content
        # The actual generator doesn't truncate to "..." but shows full description
        assert '"`REQ-1: First child requirement`"' in content
        assert '"`REQ-2: Second child requirement`"' in content

    def test_mindmap_sanitization_with_special_characters(self):
        """Test that mindmap generation sanitizes special characters correctly."""
        parent = create_sample_parsed_requirement(
            "REQ-PARSER-8",
            "The parser shall treat attribute keywords (e.g., 'critical', 'child-of', "
            "'completed') case-insensitively",
        )
        child = create_sample_parsed_requirement(
            "REQ-PARSER-9",
            "Parse requirements with [brackets] and {braces}",
            parents=["REQ-PARSER-8"],
        )

        all_reqs = [parent, child]
        content = generate_requirement_page_content(parent, all_reqs)

        assert "## Children Mindmap" in content
        assert "```mermaid" in content
        assert "mindmap" in content

        # Check that all text is properly sanitized with backticks
        assert 'root(("`REQ-PARSER-8`"))' in content  # All text is now sanitized
        assert (
            '"`REQ-PARSER-9: Parse requirements with [brackets] and {braces}`"'
            in content
        )

    def test_mindmap_sanitization_with_special_chars_in_root_id(self):
        """Test that mindmap generation sanitizes special characters in root node ID."""
        parent = create_sample_parsed_requirement(
            "REQ-PARSER(8)", "Root with special chars in ID"
        )
        child = create_sample_parsed_requirement(
            "REQ-PARSER-9", "Normal child", parents=["REQ-PARSER(8)"]
        )

        all_reqs = [parent, child]
        content = generate_requirement_page_content(parent, all_reqs)

        assert "## Children Mindmap" in content

        # Check that all text is properly sanitized with backticks
        assert 'root(("`REQ-PARSER(8)`"))' in content
        assert '"`REQ-PARSER-9: Normal child`"' in content

    def test_completion_statistics_parents(self):
        """Test completion statistics for parents."""
        completed_parent = create_sample_parsed_requirement(
            "REQ-0", "Completed parent", completed=True
        )
        incomplete_parent = create_sample_parsed_requirement(
            "REQ-1", "Incomplete parent", completed=False
        )
        child = create_sample_parsed_requirement(
            "REQ-2", "Child with mixed parents", parents=["REQ-0", "REQ-1"]
        )

        all_reqs = [completed_parent, incomplete_parent, child]
        content = generate_requirement_page_content(child, all_reqs)

        assert "## Parents (1/2 completed)" in content

    def test_completion_statistics_children(self):
        """Test completion statistics for children."""
        parent = create_sample_parsed_requirement("REQ-0", "Parent requirement")
        completed_child = create_sample_parsed_requirement(
            "REQ-1", "Completed child", parents=["REQ-0"], completed=True
        )
        incomplete_child = create_sample_parsed_requirement(
            "REQ-2", "Incomplete child", parents=["REQ-0"], completed=False
        )

        all_reqs = [parent, completed_child, incomplete_child]
        content = generate_requirement_page_content(parent, all_reqs)

        assert "## Children (1/2 completed)" in content

    def test_category_extraction_for_links(self):
        """Test that category is extracted correctly for navigation links."""
        parent = create_sample_parsed_requirement("REQ-CORE-1", "Core requirement")
        child = create_sample_parsed_requirement(
            "REQ-PARSER-1", "Parser requirement", parents=["REQ-CORE-1"]
        )

        content = generate_requirement_page_content(child, [parent, child])

        # Should link to correct category directory
        assert "[REQ-CORE-1](../REQ-CORE/REQ-CORE-1.md)" in content

    def test_orphaned_requirement(self):
        """Test generation for requirement with no parents or children."""
        req = create_sample_parsed_requirement("REQ-1", "Orphaned requirement")
        content = generate_requirement_page_content(req, [req])

        assert "# REQ-1" in content
        assert "Orphaned requirement" in content
        assert "## Parents" not in content
        assert "## Children" not in content
        assert "## Children Mindmap" not in content


class TestRequirementIndexGeneration:
    """Unit tests for requirements index page generation."""

    def test_basic_index_generation(self):
        """Test generation of basic requirements index."""
        content = generate_requirement_index_content(SAMPLE_PARSED_REQUIREMENTS)

        assert "# Requirements Index" in content
        assert "**Overall completion:" in content

    def test_index_completion_statistics(self):
        """Test overall completion statistics in index."""
        # Create mix of completed and incomplete requirements
        reqs = [
            create_sample_parsed_requirement("REQ-1", "First", completed=True),
            create_sample_parsed_requirement("REQ-2", "Second", completed=False),
            create_sample_parsed_requirement("REQ-3", "Third", completed=True),
        ]

        content = generate_requirement_index_content(reqs)
        assert "**Overall completion: 2/3 requirements**" in content

    def test_index_categorization(self):
        """Test that requirements are properly categorized in index."""
        reqs = [
            create_sample_parsed_requirement("REQ-CORE-1", "Core requirement"),
            create_sample_parsed_requirement("REQ-PARSER-1", "Parser requirement"),
            create_sample_parsed_requirement("REQ-OUTPUT-1", "Output requirement"),
        ]

        content = generate_requirement_index_content(reqs)

        assert "## REQ-CORE" in content
        assert "## REQ-PARSER" in content
        assert "## REQ-OUTPUT" in content

    def test_index_category_completion_stats(self):
        """Test category-level completion statistics."""
        reqs = [
            create_sample_parsed_requirement(
                "REQ-CORE-1", "First core", completed=True
            ),
            create_sample_parsed_requirement(
                "REQ-CORE-2", "Second core", completed=False
            ),
            create_sample_parsed_requirement(
                "REQ-PARSER-1", "Parser req", completed=True
            ),
        ]

        content = generate_requirement_index_content(reqs)

        assert "*Completion: 1/2 requirements*" in content  # REQ-CORE category
        assert "*Completion: 1/1 requirements*" in content  # REQ-PARSER category

    def test_index_requirement_links(self):
        """Test that index contains correct links to requirement pages."""
        req = create_sample_parsed_requirement("REQ-CORE-1", "Core requirement")
        content = generate_requirement_index_content([req])

        assert "[REQ-CORE-1](./REQ-CORE/REQ-CORE-1.md)" in content

    def test_index_status_emojis(self):
        """Test status emojis in index."""
        reqs = [
            create_sample_parsed_requirement("REQ-1", "Completed", completed=True),
            create_sample_parsed_requirement("REQ-2", "Incomplete", completed=False),
        ]

        content = generate_requirement_index_content(reqs)

        assert "✅" in content  # Completed
        assert "⏳" in content  # Incomplete

    def test_index_critical_indicators(self):
        """Test critical requirement indicators in index."""
        reqs = [
            create_sample_parsed_requirement("REQ-1", "Critical", critical=True),
            create_sample_parsed_requirement("REQ-2", "Normal", critical=False),
        ]

        content = generate_requirement_index_content(reqs)

        # Critical requirements should have warning emoji
        assert "⚠️" in content

    def test_empty_requirements_index(self):
        """Test index generation with no requirements."""
        content = generate_requirement_index_content([])

        assert "# Requirements Index" in content
        assert "**Overall completion: 0/0 requirements**" in content

    def test_index_sorting(self):
        """Test that requirements are sorted consistently in index."""
        reqs = [
            create_sample_parsed_requirement("REQ-CORE-3", "Third"),
            create_sample_parsed_requirement("REQ-CORE-1", "First"),
            create_sample_parsed_requirement("REQ-CORE-2", "Second"),
        ]

        content = generate_requirement_index_content(reqs)

        # Should be sorted by ID
        lines = content.split("\n")
        req_1_line = next(i for i, line in enumerate(lines) if "REQ-CORE-1" in line)
        req_2_line = next(i for i, line in enumerate(lines) if "REQ-CORE-2" in line)
        req_3_line = next(i for i, line in enumerate(lines) if "REQ-CORE-3" in line)

        assert req_1_line < req_2_line < req_3_line
