"""Simplified integration tests for the ReqSnake MkDocs plugin."""

from unittest.mock import Mock, patch

import pytest

from mkdocs_reqsnake.plugin import ReqSnake


class TestMkDocsPluginSimple:
    """Simplified integration tests for the ReqSnake MkDocs plugin functionality."""

    @pytest.fixture
    def plugin(self):
        """Create a fresh plugin instance.

        Returns:
            ReqSnake plugin instance for testing.
        """
        return ReqSnake()

    @pytest.fixture
    def mock_config(self):
        """Create mock MkDocs config.

        Returns:
            Mock MkDocs config object for testing.
        """
        mock_config = Mock()
        mock_config.config_file_path = "/tmp/mkdocs.yml"
        mock_config.get = Mock(side_effect=lambda key, default=None: default)
        return mock_config

    @pytest.fixture
    def mock_nav(self):
        """Create mock navigation object.

        Returns:
            Mock navigation object for testing.
        """
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

    def test_plugin_disabled(self, mock_nav, mock_config):
        """Test that the plugin does nothing when disabled."""
        plugin = ReqSnake()
        plugin.config = {"enabled": False}

        mock_files = Mock()
        mock_file = Mock()
        mock_file.src_uri = "with_reqs.md"
        mock_file.content_string = "> REQ-1\n> Test requirement.\n"
        mock_files.documentation_pages.return_value = [mock_file]
        mock_files.append = Mock()

        result = plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Plugin is disabled, so no files should be appended
        mock_files.append.assert_not_called()
        # Navigation should be unchanged
        assert result == mock_nav
        assert len(mock_nav.items) == 0

    @patch("mkdocs_reqsnake.plugin.Section")
    @patch("mkdocs_reqsnake.plugin.Page")
    def test_on_nav_processes_requirements(
        self, mock_page, mock_section, plugin, mock_nav, mock_config
    ):
        """Test on_nav processes requirements and creates navigation."""
        # Create test markdown content with requirements
        test_content = """
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

        # Mock the Page and Section constructors
        mock_page.return_value = Mock()
        mock_section.return_value = Mock()

        # Call on_nav
        result = plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Should return the nav object
        assert result == mock_nav

        # Should add generated files for each requirement + index
        assert mock_files.append.call_count == 3  # 2 requirements + 1 index

        # Should create Page and Section objects for navigation
        assert mock_page.called
        assert mock_section.called

    @patch("mkdocs_reqsnake.plugin.Section")
    @patch("mkdocs_reqsnake.plugin.Page")
    def test_on_nav_no_requirements(
        self, mock_page, mock_section, plugin, mock_nav, mock_config
    ):
        """Test on_nav when no requirements are found."""
        mock_files = Mock()
        mock_file = Mock()
        mock_file.src_uri = "no_reqs.md"
        mock_file.content_string = "# Just documentation"
        mock_files.documentation_pages.return_value = [mock_file]
        mock_files.append = Mock()

        result = plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Should return the nav object
        assert result == mock_nav
        # When no requirements are found, the plugin should still create index file
        assert mock_files.append.call_count == 1  # index file only

    @patch("mkdocs_reqsnake.plugin.Section")
    @patch("mkdocs_reqsnake.plugin.Page")
    def test_files_without_src_uri_ignored(
        self, mock_page, mock_section, plugin, mock_nav, mock_config
    ):
        """Test that files without src_uri are ignored."""
        mock_file_no_src = Mock()
        mock_file_no_src.src_uri = None
        mock_file_no_src.content_string = "> REQ-1\n> Test requirement.\n"

        mock_file_valid = Mock()
        mock_file_valid.src_uri = "valid.md"
        mock_file_valid.content_string = "> REQ-2\n> Valid requirement.\n"

        mock_files = Mock()
        mock_files.documentation_pages.return_value = [
            mock_file_no_src,
            mock_file_valid,
        ]
        mock_files.append = Mock()

        # Mock the constructors
        mock_page.return_value = Mock()
        mock_section.return_value = Mock()

        plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Should only process the valid file (1 requirement + 1 index)
        assert mock_files.append.call_count == 2
