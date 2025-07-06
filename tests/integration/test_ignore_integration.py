"""Integration tests for .requirementsignore functionality with the plugin."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mkdocs_reqsnake.plugin import ReqSnake


@patch("mkdocs_reqsnake.plugin.Section")
@patch("mkdocs_reqsnake.plugin.Page")
class TestIgnoreIntegration:
    """Integration tests for .requirementsignore functionality with the plugin."""

    @pytest.fixture
    def plugin(self):
        """Create a fresh plugin instance.

        Returns:
            ReqSnake plugin instance for testing.
        """
        plugin = ReqSnake()
        plugin.config = {"enabled": True}
        return plugin

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests.

        Yields:
            Path to the temporary directory.
        """
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        try:
            yield temp_path
        finally:
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create mock config pointing to temp directory.

        Args:
            temp_dir: Temporary directory fixture.

        Returns:
            Mock config object for testing.
        """
        mock_config = Mock()
        mock_config.config_file_path = str(temp_dir / "mkdocs.yml")
        mock_config.get = Mock(side_effect=lambda key, default=None: default)
        # Ensure Path(config.config_file_path).parent works properly
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

    @pytest.fixture
    def sample_files(self):
        """Create sample mock files for testing.

        Returns:
            Dictionary of mock file objects for testing.
        """
        # File with requirements that should be processed
        mock_file_normal = Mock()
        mock_file_normal.src_uri = "docs/requirements.md"
        mock_file_normal.content_string = """> REQ-1
> This is a normal requirement
> critical"""

        # File that should be ignored based on pattern
        mock_file_ignored = Mock()
        mock_file_ignored.src_uri = "docs/test_file.md"
        mock_file_ignored.content_string = """> REQ-2
> This requirement should be ignored
> critical"""

        # File in ignored directory
        mock_file_build = Mock()
        mock_file_build.src_uri = "build/generated.md"
        mock_file_build.content_string = """> REQ-3
> This requirement is in build directory
> critical"""

        # Another normal file
        mock_file_normal2 = Mock()
        mock_file_normal2.src_uri = "docs/specs.md"
        mock_file_normal2.content_string = """> REQ-4
> Another normal requirement"""

        return {
            "normal": mock_file_normal,
            "ignored": mock_file_ignored,
            "build": mock_file_build,
            "normal2": mock_file_normal2,
        }

    def test_ignore_functionality_no_ignore_file(
        self, mock_page, mock_section, plugin, mock_nav, mock_config, sample_files
    ):
        """Test that all files are processed when no .requirementsignore exists."""
        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = list(sample_files.values())
        mock_files.append = MagicMock()

        # Mock the constructors
        mock_page.return_value = Mock()
        mock_section.return_value = Mock()

        plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # All 4 requirements should be processed since no ignore file exists
        assert mock_files.append.call_count == 5  # 4 req pages + 1 index

    def test_ignore_functionality_with_patterns(
        self,
        mock_page,
        mock_section,
        plugin,
        mock_nav,
        mock_config,
        sample_files,
        temp_dir,
    ):
        """Test that files are ignored based on .requirementsignore patterns."""
        # Create .requirementsignore file
        ignore_content = """# Ignore test files
test_*.md
build/
"""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            sample_files["normal"],  # Should be processed
            sample_files["ignored"],  # Should be ignored (test_*.md)
            sample_files["build"],  # Should be ignored (build/)
            sample_files["normal2"],  # Should be processed
        ]
        mock_files.append = MagicMock()

        with patch("mkdocs_reqsnake.plugin.logger") as mock_logger:
            plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

            # Only 2 requirements should be processed (REQ-1 and REQ-4)
            assert mock_files.append.call_count == 3  # 2 req pages + 1 index

            # Check that ignored files were logged
            ignore_calls = [
                call
                for call in mock_logger.info.call_args_list
                if "Ignored" in str(call)
            ]
            assert len(ignore_calls) == 1
            assert "Ignored 2 files" in str(ignore_calls[0])

    def test_ignore_functionality_glob_patterns(
        self, mock_page, mock_section, plugin, mock_nav, mock_config, temp_dir
    ):
        """Test that glob patterns work correctly in .requirementsignore."""
        # Create .requirementsignore file with glob patterns
        ignore_content = """*.tmp
**/build/**
docs/test_*
"""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        # Create additional mock files
        mock_file_tmp = Mock()
        mock_file_tmp.src_uri = "file.tmp"
        mock_file_tmp.content_string = "> REQ-3\n> Temp requirement"

        mock_file_nested_build = Mock()
        mock_file_nested_build.src_uri = "project/build/nested.md"
        mock_file_nested_build.content_string = "> REQ-4\n> Nested build requirement"

        mock_file_normal = Mock()
        mock_file_normal.src_uri = "docs/requirements.md"
        mock_file_normal.content_string = "> REQ-1\n> Normal requirement"

        mock_file_test = Mock()
        mock_file_test.src_uri = "docs/test_file.md"
        mock_file_test.content_string = "> REQ-2\n> Test requirement"

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            mock_file_normal,  # Should be processed
            mock_file_test,  # Should be ignored (docs/test_*)
            mock_file_tmp,  # Should be ignored (*.tmp)
            mock_file_nested_build,  # Should be ignored (**/build/**)
        ]
        mock_files.append = MagicMock()

        # Mock the constructors
        mock_page.return_value = Mock()
        mock_section.return_value = Mock()

        with patch("mkdocs_reqsnake.plugin.logger") as mock_logger:
            plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

            # Only 1 requirement should be processed
            assert mock_files.append.call_count == 2  # 1 req page + 1 index

            # Check that ignored files were logged
            ignore_calls = [
                call
                for call in mock_logger.info.call_args_list
                if "Ignored" in str(call)
            ]
            assert len(ignore_calls) == 1
            assert "Ignored 3 files" in str(ignore_calls[0])

    def test_ignore_functionality_with_comments_and_blanks(
        self,
        mock_page,
        mock_section,
        plugin,
        mock_nav,
        mock_config,
        sample_files,
        temp_dir,
    ):
        """Test comments and blank lines in .requirementsignore are handled."""
        ignore_content = """# This is a comment
# Another comment

test_*.md

# Ignore build directories
build/

# End comment"""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            sample_files["normal"],  # Should be processed
            sample_files["ignored"],  # Should be ignored
            sample_files["build"],  # Should be ignored
            sample_files["normal2"],  # Should be processed
        ]
        mock_files.append = MagicMock()

        # Mock the constructors
        mock_page.return_value = Mock()
        mock_section.return_value = Mock()

        plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Only 2 requirements should be processed
        assert mock_files.append.call_count == 3  # 2 req pages + 1 index

    def test_ignore_functionality_error_handling(
        self,
        mock_page,
        mock_section,
        plugin,
        mock_nav,
        mock_config,
        sample_files,
        temp_dir,
    ):
        """Test that plugin handles .requirementsignore read errors gracefully."""
        # Create a .requirementsignore file and then make it unreadable
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text("test_*.md")
        ignore_file.chmod(0o000)  # Make file unreadable

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            sample_files["normal"],
            sample_files["ignored"],
        ]
        mock_files.append = MagicMock()

        # Mock the constructors
        mock_page.return_value = Mock()
        mock_section.return_value = Mock()

        try:
            # Should not raise an exception and should process all files
            plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

            # All files should be processed when ignore file can't be read
            assert mock_files.append.call_count == 3  # 2 req pages + 1 index
        finally:
            # Restore permissions for cleanup
            ignore_file.chmod(0o644)

    def test_ignore_functionality_unicode_handling(
        self, mock_page, mock_section, plugin, mock_nav, mock_config, temp_dir
    ):
        """Test that unicode in ignore files is handled properly."""
        ignore_content = """# Test with unicode: café
test_*.md
файл*.md  # Cyrillic pattern
"""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text(ignore_content, encoding="utf-8")

        mock_file_test = Mock()
        mock_file_test.src_uri = "test_example.md"
        mock_file_test.content_string = "> REQ-1\n> Test requirement"

        mock_file_cyrillic = Mock()
        mock_file_cyrillic.src_uri = "файл_example.md"
        mock_file_cyrillic.content_string = "> REQ-2\n> Cyrillic requirement"

        mock_file_normal = Mock()
        mock_file_normal.src_uri = "normal.md"
        mock_file_normal.content_string = "> REQ-3\n> Normal requirement"

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            mock_file_test,  # Should be ignored (test_*.md)
            mock_file_cyrillic,  # Should be ignored (файл*.md)
            mock_file_normal,  # Should be processed
        ]
        mock_files.append = MagicMock()

        # Mock the constructors
        mock_page.return_value = Mock()
        mock_section.return_value = Mock()

        plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Only 1 requirement should be processed
        assert mock_files.append.call_count == 2  # 1 req page + 1 index

    def test_ignore_functionality_relative_paths(
        self, mock_page, mock_section, plugin, mock_nav, mock_config, temp_dir
    ):
        """Test ignore patterns with relative paths."""
        ignore_content = """docs/temp/
./build/
../external/
"""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        mock_files_data = [
            ("docs/temp/file.md", True),  # Should be ignored
            ("./build/output.md", True),  # Should be ignored
            ("../external/lib.md", True),  # Should be ignored
            ("docs/main.md", False),  # Should be processed
            ("src/code.md", False),  # Should be processed
        ]

        mock_files_list = []
        for file_path, _should_ignore in mock_files_data:
            mock_file = Mock()
            mock_file.src_uri = file_path
            mock_file.content_string = (
                f"> REQ-{len(mock_files_list)}\n> Requirement in {file_path}"
            )
            mock_files_list.append(mock_file)

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = mock_files_list
        mock_files.append = MagicMock()

        # Mock the constructors
        mock_page.return_value = Mock()
        mock_section.return_value = Mock()

        plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # Should process 2 files (the non-ignored ones)
        expected_processed = sum(
            1 for _, should_ignore in mock_files_data if not should_ignore
        )
        assert mock_files.append.call_count == expected_processed + 1  # + 1 for index

    def test_ignore_functionality_empty_patterns(
        self,
        mock_page,
        mock_section,
        plugin,
        mock_nav,
        mock_config,
        sample_files,
        temp_dir,
    ):
        """Test behavior with empty ignore patterns."""
        ignore_content = """
# Only comments and blank lines


# Another comment

"""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = list(sample_files.values())
        mock_files.append = MagicMock()

        # Mock the constructors
        mock_page.return_value = Mock()
        mock_section.return_value = Mock()

        plugin.on_nav(mock_nav, config=mock_config, files=mock_files)

        # All files should be processed when no actual patterns exist
        assert mock_files.append.call_count == 5  # 4 req pages + 1 index
