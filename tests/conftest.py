"""Shared test fixtures for ReqSnake test suite."""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config() -> Mock:
    """Create a mock MkDocs config object."""
    mock_config = Mock()
    mock_config.config_file_path = None
    return mock_config


@pytest.fixture
def mock_file_with_requirements() -> Mock:
    """Create a mock file containing requirements."""
    mock_file = Mock()
    mock_file.src_uri = "with_reqs.md"
    mock_file.content_string = "> REQ-1\n> Test requirement.\n> critical\n"
    return mock_file


@pytest.fixture
def mock_file_no_requirements() -> Mock:
    """Create a mock file with no requirements."""
    mock_file = Mock()
    mock_file.src_uri = "no_reqs.md"
    mock_file.content_string = "# Just documentation\n\nNo requirements here."
    return mock_file


@pytest.fixture
def sample_requirement_markdown() -> str:
    """Sample markdown content with requirements."""
    return """
# Sample Documentation

> REQ-1
> First requirement.
> critical

> REQ-2
> Second requirement.
> child-of: REQ-1
> completed

> REQ-3
> Third requirement.
"""


@pytest.fixture
def complex_requirement_markdown() -> str:
    """Complex markdown content for testing edge cases."""
    return """
# Complex Requirements

> MECH-123
> The wing must withstand 5g load.
>
> critical
> child-of: MECH-54
> child-of: MECH-57
> completed

> AVIO-15
> Avionics must support dual redundancy.
>
> child-of: AVIO-16

> SW-33
> On-board software for the plane.
"""


@pytest.fixture
def invalid_requirement_markdown() -> str:
    """Invalid markdown content for testing error cases."""
    return """
> REQ-1
> Valid requirement.

> INVALID-ID
> Invalid requirement ID.

> REQ-2
> Another valid requirement.
> unknown-attribute
"""
