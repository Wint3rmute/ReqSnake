"""Unit tests for requirement validation."""

import pytest
from mkdocs.exceptions import PluginError

from mkdocs_reqsnake.parser import parse_requirements_from_files
from mkdocs_reqsnake.validator import validate_requirements
from tests.fixtures.sample_requirements import (
    create_sample_parsed_requirement,
)


class TestRequirementValidation:
    """Unit tests for requirement validation logic."""

    def test_missing_parent_validation(self):
        """REQ-CORE-8: Missing parent references should raise MissingParentError."""
        md = (
            "> REQ-1\n> Child requirement.\n> child-of: REQ-MISSING\n\n"
            "> REQ-2\n> Another requirement.\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with pytest.raises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        assert "references non-existing parent 'REQ-MISSING'" in str(ctx.value)

    def test_multiple_missing_parents_validation(self):
        """REQ-CORE-8: Multiple missing parents should be caught."""
        md = (
            "> REQ-1\n> Child requirement.\n> child-of: REQ-MISSING1\n"
            "> child-of: REQ-MISSING2\n\n"
            "> REQ-2\n> Another requirement.\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with pytest.raises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        # Should catch the first missing parent
        assert "references non-existing parent" in str(ctx.value)

    def test_valid_parent_references_pass(self):
        """REQ-CORE-8: Valid parent references should not raise errors."""
        md = (
            "> REQ-1\n> Parent requirement.\n\n"
            "> REQ-2\n> Child requirement.\n> child-of: REQ-1\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        # Should not raise an exception
        validate_requirements(parsed_reqs)

    def test_circular_dependency_detection(self):
        """REQ-PARSER-15: Circular dependencies should be detected."""
        md = (
            "> REQ-1\n> Parent.\n> child-of: REQ-2\n\n"
            "> REQ-2\n> Child.\n> child-of: REQ-1\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with pytest.raises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        assert "Circular dependency detected" in str(ctx.value)

    def test_completed_parent_with_incomplete_child_fails(self):
        """REQ-CORE-7: Completed requirements with incomplete children raise error."""
        md = "> REQ-1\n> Parent.\n> completed\n\n> REQ-2\n> Child.\n> child-of: REQ-1\n"
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with pytest.raises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        assert "are marked as completed but have incomplete children" in str(ctx.value)

    def test_completed_parent_with_completed_child_passes(self):
        """REQ-CORE-7: Completed requirements with completed children should pass."""
        md = (
            "> REQ-1\n> Parent.\n> completed\n> child-of: REQ-2\n\n"
            "> REQ-2\n> Child.\n> completed\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        # Should not raise an exception
        validate_requirements(parsed_reqs)

    def test_duplicate_ids_same_file(self):
        """Test that duplicate requirement IDs in the same file raise an error."""
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
            validate_requirements(parsed_reqs)
        assert "Duplicate requirement ID 'MECH-123' found" in str(context.value)

    def test_empty_requirements_list(self):
        """Test validation with empty requirements list."""
        # Should not raise any exceptions
        validate_requirements([])

    def test_single_requirement_validation(self):
        """Test validation with a single valid requirement."""
        parsed_req = create_sample_parsed_requirement("REQ-1", "Single requirement")
        validate_requirements([parsed_req])  # Should not raise

    def test_complex_valid_hierarchy(self):
        """Test validation with a complex but valid requirement hierarchy."""
        parsed_reqs = [
            create_sample_parsed_requirement("REQ-1", "Root requirement"),
            create_sample_parsed_requirement(
                "REQ-2", "Child of REQ-1", parents=["REQ-1"]
            ),
            create_sample_parsed_requirement(
                "REQ-3", "Child of REQ-2", parents=["REQ-2"]
            ),
            create_sample_parsed_requirement("REQ-4", "Independent requirement"),
        ]
        validate_requirements(parsed_reqs)  # Should not raise


class TestValidationIntegration:
    """Integration tests for validation with parsing."""

    def test_circular_child_relationship(self):
        """Test that circular child relationships are detected."""
        md = (
            "> REQ-1\n> Parent.\n> child-of: REQ-2\n\n"
            "> REQ-2\n> Child.\n> child-of: REQ-1\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with pytest.raises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        assert "Circular dependency detected" in str(ctx.value)

    def test_three_way_circular_dependency(self):
        """Test detection of three-way circular dependency."""
        md = (
            "> REQ-1\n> First.\n> child-of: REQ-2\n\n"
            "> REQ-2\n> Second.\n> child-of: REQ-3\n\n"
            "> REQ-3\n> Third.\n> child-of: REQ-1\n"
        )
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with pytest.raises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        assert "Circular dependency detected" in str(ctx.value)

    def test_self_referencing_requirement(self):
        """Test that a requirement cannot reference itself as parent."""
        md = "> REQ-1\n> Self-referencing requirement.\n> child-of: REQ-1\n"
        file_data = [("test.md", md)]
        parsed_reqs = parse_requirements_from_files(file_data)
        with pytest.raises(PluginError) as ctx:
            validate_requirements(parsed_reqs)
        assert "Circular dependency detected" in str(ctx.value)
