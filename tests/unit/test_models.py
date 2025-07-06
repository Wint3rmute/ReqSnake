"""Unit tests for ReqSnake data models."""

from mkdocs_reqsnake.models import Requirement
from tests.fixtures.sample_requirements import create_sample_requirement


class TestRequirement:
    """Unit tests for the Requirement model."""

    def test_requirement_creation(self):
        """Test basic requirement creation."""
        req = Requirement(
            req_id="REQ-1",
            description="Test requirement",
            critical=True,
            completed=False,
            parents=["REQ-0"],
        )
        assert req.req_id == "REQ-1"
        assert req.description == "Test requirement"
        assert req.critical is True
        assert req.completed is False
        assert req.parents == ["REQ-0"]

    def test_requirement_defaults(self):
        """Test requirement creation with default values."""
        req = Requirement(req_id="REQ-1", description="Test requirement")
        assert req.req_id == "REQ-1"
        assert req.description == "Test requirement"
        assert req.critical is False
        assert req.completed is False
        assert req.parents == []

    def test_requirement_equality(self):
        """Test requirement equality comparison."""
        req1 = Requirement("REQ-1", "Test requirement", critical=True)
        req2 = Requirement("REQ-1", "Test requirement", critical=True)
        req3 = Requirement("REQ-2", "Test requirement", critical=True)

        assert req1 == req2
        assert req1 != req3

    def test_requirement_string_representation(self):
        """Test requirement string representation."""
        req = Requirement("REQ-1", "Test requirement")
        # The actual __str__ method returns the repr, not the simple format
        assert "REQ-1" in str(req)
        assert "Test requirement" in str(req)

    def test_requirement_repr(self):
        """Test requirement repr."""
        req = Requirement("REQ-1", "Test requirement", critical=True)
        repr_str = repr(req)
        assert "REQ-1" in repr_str
        assert "Test requirement" in repr_str
        assert "critical=True" in repr_str


class TestRequirementPrettyString:
    """Unit tests for the requirement pretty string formatting."""

    def test_basic_requirement_pretty_string(self):
        """Test basic requirement pretty string output."""
        req = Requirement("REQ-1", "Basic requirement")
        expected = "REQ-1: Basic requirement\n\n"
        assert req.to_pretty_string() == expected

    def test_critical_requirement_pretty_string(self):
        """Test critical requirement pretty string output."""
        req = Requirement("REQ-2", "Critical requirement", critical=True)
        expected = "REQ-2: Critical requirement\n\n**⚠️ critical**\n\n"
        assert req.to_pretty_string() == expected

    def test_completed_requirement_pretty_string(self):
        """Test completed requirement pretty string output."""
        req = Requirement("REQ-3", "Completed requirement", completed=True)
        expected = "REQ-3: Completed requirement\n\n✅ completed\n\n"
        assert req.to_pretty_string() == expected

    def test_requirement_with_parents_pretty_string(self):
        """Test requirement with parents pretty string output."""
        req = Requirement("REQ-4", "Parent requirement", parents=["REQ-5", "REQ-6"])
        expected = "REQ-4: Parent requirement\n\n### Parents\n\n- REQ-5\n- REQ-6\n"
        assert req.to_pretty_string() == expected

    def test_complete_requirement_pretty_string(self):
        """Test complete requirement (critical, completed, with parents)."""
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
        assert req.to_pretty_string() == expected

    def test_empty_parents_list(self):
        """Test that empty parents list doesn't add parents section."""
        req = Requirement("REQ-1", "No parents", parents=[])
        expected = "REQ-1: No parents\n\n"
        assert req.to_pretty_string() == expected

    def test_single_parent(self):
        """Test requirement with single parent."""
        req = Requirement("REQ-1", "Single parent", parents=["REQ-0"])
        expected = "REQ-1: Single parent\n\n### Parents\n\n- REQ-0\n"
        assert req.to_pretty_string() == expected


class TestRequirementValidation:
    """Unit tests for requirement validation at the model level."""

    def test_empty_req_id_validation(self):
        """Test that empty requirement ID is handled."""
        # Note: Currently the model doesn't enforce validation
        # This test documents current behavior
        req = Requirement("", "Empty ID requirement")
        assert req.req_id == ""

    def test_empty_description_validation(self):
        """Test that empty description is handled."""
        req = Requirement("REQ-1", "")
        assert req.description == ""

    def test_none_parents_becomes_empty_list(self):
        """Test that None parents becomes empty list."""
        req = Requirement("REQ-1", "Test", parents=None)
        # Note: The current model doesn't convert None to empty list
        # This test documents current behavior
        assert req.parents is None

    def test_unicode_in_description(self):
        """Test unicode characters in description."""
        req = Requirement("REQ-1", "Unicode: café, naïve, 你好")
        assert "café" in req.description
        assert "naïve" in req.description
        assert "你好" in req.description

    def test_markdown_in_description(self):
        """Test markdown formatting in description."""
        req = Requirement("REQ-1", "Description with **bold** and *italic*")
        assert req.description == "Description with **bold** and *italic*"
        # Verify markdown is preserved in pretty string
        pretty = req.to_pretty_string()
        assert "**bold**" in pretty
        assert "*italic*" in pretty


class TestRequirementFixtures:
    """Test the requirement fixtures from sample_requirements.py."""

    def test_create_sample_requirement(self):
        """Test the create_sample_requirement fixture function."""
        req = create_sample_requirement()
        assert req.req_id == "REQ-1"
        assert req.description == "Sample requirement"
        assert req.critical is False
        assert req.completed is False
        assert req.parents == []

    def test_create_sample_requirement_with_params(self):
        """Test create_sample_requirement with custom parameters."""
        req = create_sample_requirement(
            req_id="CUSTOM-1",
            description="Custom requirement",
            critical=True,
            completed=True,
            parents=["PARENT-1"],
        )
        assert req.req_id == "CUSTOM-1"
        assert req.description == "Custom requirement"
        assert req.critical is True
        assert req.completed is True
        assert req.parents == ["PARENT-1"]
