"""Sample requirement data for testing."""

from mkdocs_reqsnake.models import ParsedRequirement, Requirement


def create_sample_requirement(
    req_id: str = "REQ-1",
    description: str = "Sample requirement",
    critical: bool = False,
    completed: bool = False,
    parents: list[str] | None = None,
) -> Requirement:
    """Create a sample requirement for testing."""
    return Requirement(
        req_id=req_id,
        description=description,
        critical=critical,
        completed=completed,
        parents=parents or [],
    )


def create_sample_parsed_requirement(
    req_id: str = "REQ-1",
    description: str = "Sample requirement",
    source_file: str = "test.md",
    critical: bool = False,
    completed: bool = False,
    parents: list[str] | None = None,
) -> ParsedRequirement:
    """Create a sample parsed requirement for testing."""
    requirement = create_sample_requirement(
        req_id=req_id,
        description=description,
        critical=critical,
        completed=completed,
        parents=parents,
    )
    return ParsedRequirement(requirement=requirement, source_file=source_file)


# Common test data sets
SAMPLE_REQUIREMENTS = [
    create_sample_requirement("REQ-1", "First requirement", critical=True),
    create_sample_requirement("REQ-2", "Second requirement", parents=["REQ-1"]),
    create_sample_requirement("REQ-3", "Third requirement", completed=True),
]

SAMPLE_PARSED_REQUIREMENTS = [
    create_sample_parsed_requirement("REQ-1", "First requirement", critical=True),
    create_sample_parsed_requirement("REQ-2", "Second requirement", parents=["REQ-1"]),
    create_sample_parsed_requirement("REQ-3", "Third requirement", completed=True),
]

HIERARCHICAL_REQUIREMENTS = [
    create_sample_requirement("REQ-CORE-1", "Core requirement 1"),
    create_sample_requirement(
        "REQ-CORE-2", "Core requirement 2", parents=["REQ-CORE-1"]
    ),
    create_sample_requirement("REQ-PARSER-1", "Parser requirement 1"),
    create_sample_requirement("REQ-PARSER-2", "Parser requirement 2"),
]
