"""Integration tests for the ReqSnake MkDocs plugin."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from mkdocs.structure.files import InclusionLevel

from mkdocs_reqsnake.plugin import ReqSnake


class TestMkDocsPluginIntegration:
    """Integration tests for the ReqSnake MkDocs plugin functionality."""

    @pytest.fixture
    def plugin(self):
        """Create a fresh plugin instance."""
        return ReqSnake()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        try:
            yield temp_path
        finally:
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create mock MkDocs config."""
        mock_config = Mock()
        mock_config.config_file_path = str(temp_dir / "mkdocs.yml")
        return mock_config

    @pytest.fixture
    def mock_nav(self):
        """Create mock navigation object."""
        mock_nav = Mock()
        mock_nav.items = []
        return mock_nav

    def test_plugin_initialization(self):
        """Test that the plugin initializes correctly."""
        plugin = ReqSnake()
        assert hasattr(plugin, "config_scheme")
        assert hasattr(plugin, "on_nav")

    def test_plugin_config_scheme(self):
        """Test that the plugin has the correct configuration scheme."""
        plugin = ReqSnake()
        assert plugin.config_scheme[0][0] == "enabled"

    def test_on_nav_with_no_requirements(self, plugin, mock_nav, mock_config):
        """Test on_nav when no requirements are found in documentation."""
        mock_files = MagicMock()
        mock_file = Mock()
        mock_file.src_uri = "no_reqs.md"
        mock_file.content_string = "# Just documentation"
        mock_files.documentation_pages.return_value = [mock_file]
        mock_files.append = MagicMock()

        result = plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Should return the nav object
        assert result == mock_nav
        # Should not add navigation items when no requirements found
        assert len(mock_nav.items) == 0

    def test_on_nav_with_requirements(self, plugin, mock_nav, mock_config):
        """Test on_nav when requirements are found in documentation."""
        # Create test markdown content with requirements
        test_content = """
# Some documentation

> REQ-1
> First requirement.
> critical

> REQ-2
> Second requirement.
> child-of: REQ-1
"""

        # Create mock file
        mock_file = Mock()
        mock_file.src_uri = "test_requirements.md"
        mock_file.content_string = test_content

        # Create mock files collection
        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file]
        mock_files.append = Mock()

        # Call on_nav
        result = plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Should return the nav object
        assert result == mock_nav

        # Should add generated files for each requirement + index
        assert mock_files.append.call_count == 3  # 2 requirements + 1 index

        # Should add Requirements section to navigation
        assert len(mock_nav.items) == 1
        requirements_section = mock_nav.items[0]
        assert requirements_section.title == "Requirements"

    def test_on_nav_with_complex_requirements(self, plugin, mock_nav, mock_config):
        """Test on_nav with complex requirements including children and status."""
        # Create test markdown content with complex requirements
        test_content = """
# Documentation

> REQ-1
> Parent requirement.
> critical
> completed

> REQ-2
> Child requirement.
> child-of: REQ-1
> completed

> REQ-3
> Another requirement.
> critical
> completed
"""

        # Create mock file
        mock_file = Mock()
        mock_file.src_uri = "complex_reqs.md"
        mock_file.content_string = test_content

        # Create mock files collection
        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file]
        mock_files.append = Mock()

        # Call on_nav
        result = plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Should return the nav object
        assert result == mock_nav

        # Should add generated files for each requirement + index
        assert mock_files.append.call_count == 4  # 3 requirements + 1 index

        # Should create hierarchical navigation
        assert len(mock_nav.items) == 1
        requirements_section = mock_nav.items[0]
        assert requirements_section.title == "Requirements"

    def test_on_nav_with_multiple_documentation_files(
        self, plugin, mock_nav, mock_config
    ):
        """Test on_nav with requirements spread across multiple files."""
        # Create multiple mock files with requirements
        mock_file1 = Mock()
        mock_file1.src_uri = "first_file.md"
        mock_file1.content_string = "> REQ-1\n> First file requirement.\n"

        mock_file2 = Mock()
        mock_file2.src_uri = "second_file.md"
        mock_file2.content_string = "> REQ-2\n> Second file requirement.\n"

        # Create mock files collection
        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file1, mock_file2]
        mock_files.append = Mock()

        # Call on_nav
        result = plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Should return the nav object
        assert result == mock_nav

        # Should add generated files for each requirement + index
        assert mock_files.append.call_count == 3  # 2 requirements + 1 index

    def test_generated_file_structure(self, plugin, mock_nav, mock_config):
        """Test that generated files are created with correct structure."""
        # Create test markdown content
        test_content = "> REQ-1\n> Test requirement.\n> critical"

        # Create mock file
        mock_file = Mock()
        mock_file.src_uri = "generated_test.md"
        mock_file.content_string = test_content

        # Create mock files collection
        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file]
        mock_files.append = Mock()

        # Call on_nav
        plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Get the generated file calls
        calls = mock_files.append.call_args_list
        generated_files = [call[0][0] for call in calls]

        # Find the requirement file
        req_file = None
        for file in generated_files:
            if hasattr(file, "src_uri") and file.src_uri == "reqsnake/REQ/REQ-1.md":
                req_file = file
                break

        assert req_file is not None
        if req_file is not None:
            # Test that the file was created with the correct structure
            assert req_file.src_uri == "reqsnake/REQ/REQ-1.md"
            assert req_file.inclusion == InclusionLevel.INCLUDED

    def test_index_file_structure(self, plugin, mock_nav, mock_config):
        """Test that the index file is created with correct structure."""
        # Create test markdown content
        test_content = """
> REQ-1
> First requirement.

> REQ-2
> Second requirement.
"""

        # Create mock file
        mock_file = Mock()
        mock_file.src_uri = "index_test.md"
        mock_file.content_string = test_content

        # Create mock files collection
        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file]
        mock_files.append = Mock()

        # Call on_nav
        plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Get the generated file calls
        calls = mock_files.append.call_args_list
        generated_files = [call[0][0] for call in calls]

        # Find the index file
        index_file = None
        for file in generated_files:
            if hasattr(file, "src_uri") and file.src_uri == "reqsnake/index.md":
                index_file = file
                break

        assert index_file is not None
        if index_file is not None:
            # Test that the index file was created with the correct structure
            assert index_file.src_uri == "reqsnake/index.md"
            assert index_file.inclusion == InclusionLevel.INCLUDED

    def test_plugin_disabled(self, mock_nav, mock_config):
        """Test that the plugin does nothing when disabled."""
        plugin = ReqSnake()
        plugin.config = {"enabled": False}

        mock_files = MagicMock()
        mock_file = Mock()
        mock_file.src_uri = "with_reqs.md"
        mock_file.content_string = "> REQ-1\n> Test requirement.\n"
        mock_files.documentation_pages.return_value = [mock_file]
        mock_files.append = MagicMock()

        result = plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Plugin is disabled, so no files should be appended
        mock_files.append.assert_not_called()
        # Navigation should be unchanged
        assert result == mock_nav
        assert len(mock_nav.items) == 0

    def test_navigation_hierarchy_structure(self, plugin, mock_nav, mock_config):
        """Test that navigation hierarchy is created correctly."""
        test_content = """
> REQ-CORE-1
> Core requirement.

> REQ-PARSER-1
> Parser requirement.

> REQ-OUTPUT-1
> Output requirement.
"""

        mock_file = Mock()
        mock_file.src_uri = "hierarchy_test.md"
        mock_file.content_string = test_content

        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file]
        mock_files.append = Mock()

        plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Should create Requirements section with categories
        assert len(mock_nav.items) == 1
        requirements_section = mock_nav.items[0]
        assert requirements_section.title == "Requirements"

        # Should have Overview + 3 category sections
        assert len(requirements_section.children) == 4  # Overview + 3 categories

        # First child should be Overview
        overview = requirements_section.children[0]
        assert overview.title == "Overview"

        # Should have category sections
        category_titles = [child.title for child in requirements_section.children[1:]]
        assert "REQ-CORE" in category_titles
        assert "REQ-OUTPUT" in category_titles
        assert "REQ-PARSER" in category_titles

    def test_files_without_src_uri_ignored(self, plugin, mock_nav, mock_config):
        """Test that files without src_uri are ignored."""
        mock_file_no_src = Mock()
        mock_file_no_src.src_uri = None
        mock_file_no_src.content_string = "> REQ-1\n> Test requirement.\n"

        mock_file_valid = Mock()
        mock_file_valid.src_uri = "valid.md"
        mock_file_valid.content_string = "> REQ-2\n> Valid requirement.\n"

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            mock_file_no_src,
            mock_file_valid,
        ]
        mock_files.append = MagicMock()

        plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Should only process the valid file (1 requirement + 1 index)
        assert mock_files.append.call_count == 2
