"""Tests for the ReqSnake MkDocs plugin functionality."""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from mkdocs.structure.files import InclusionLevel

from mkdocs_reqsnake.plugin import ReqSnake


class TestMkDocsPlugin(unittest.TestCase):
    """Test the ReqSnake MkDocs plugin functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.plugin = ReqSnake()
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)
        self.mock_file_no_reqs = Mock()
        self.mock_file_no_reqs.src_uri = "no_reqs.md"
        self.mock_file_no_reqs.content_string = ""  # No requirements
        self.mock_file_no_src_dir = Mock()
        self.mock_file_no_src_dir.src_uri = "no_src_dir.md"
        self.mock_file_no_src_dir.content_string = ""  # No requirements
        self.mock_file_with_reqs = Mock()
        self.mock_file_with_reqs.src_uri = "with_reqs.md"
        self.mock_file_with_reqs.content_string = "> REQ-1\n> Test requirement.\n"
        self.mock_config = Mock()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_plugin_initialization(self) -> None:
        """Test that the plugin initializes correctly."""
        plugin = ReqSnake()
        self.assertTrue(hasattr(plugin, "config_scheme"))
        self.assertTrue(hasattr(plugin, "on_files"))

    def test_plugin_config_scheme(self) -> None:
        """Test that the plugin has the correct configuration scheme."""
        plugin = ReqSnake()
        self.assertEqual(plugin.config_scheme[0][0], "enabled")

    def test_on_files_with_no_requirements(self) -> None:
        """Test on_files when no requirements are found in documentation."""
        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [self.mock_file_no_reqs]
        mock_files.append = MagicMock()
        self.plugin.on_files(mock_files, config=self.mock_config)
        # No requirements, so only the index page should be appended
        mock_files.append.assert_called_once()

    def test_on_files_with_requirements(self) -> None:
        """Test on_files when requirements are found in documentation."""
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
        mock_file.src_dir = "docs"
        mock_file.content_string = test_content

        # Create mock files collection
        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file]

        # Create mock config
        mock_config = Mock()

        # Call on_files
        result = self.plugin.on_files(mock_files, config=mock_config)

        # Should return the files object
        self.assertEqual(result, mock_files)

        # Should add generated files for each requirement
        # Check that append was called for each requirement + index
        self.assertEqual(mock_files.append.call_count, 3)  # 2 requirements + 1 index

        # Verify the calls were made with File.generated
        calls = mock_files.append.call_args_list
        generated_files = [call[0][0] for call in calls]

        # Check that we have files for each requirement
        req_ids = [f.src_uri for f in generated_files if "reqsnake" in f.src_uri]
        self.assertIn("reqsnake/REQ/REQ-1.md", req_ids)
        self.assertIn("reqsnake/REQ/REQ-2.md", req_ids)
        self.assertIn("reqsnake/index.md", req_ids)

    def test_on_files_ignores_files_without_src_dir(self) -> None:
        """Test that on_files ignores files without src_dir."""
        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            self.mock_file_no_src_dir,
            self.mock_file_with_reqs,
        ]
        mock_files.append = MagicMock()
        self.plugin.on_files(mock_files, config=self.mock_config)
        # Should generate one requirement file and one index file
        self.assertEqual(mock_files.append.call_count, 2)

    def test_on_files_with_complex_requirements(self) -> None:
        """Test on_files with complex requirements including children and completed status."""
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
        mock_file.src_dir = "docs"
        mock_file.content_string = test_content

        # Create mock files collection
        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file]

        # Create mock config
        mock_config = Mock()

        # Call on_files
        result = self.plugin.on_files(mock_files, config=mock_config)

        # Should return the files object
        self.assertEqual(result, mock_files)

        # Should add generated files for each requirement + index
        self.assertEqual(mock_files.append.call_count, 4)  # 3 requirements + 1 index

    def test_on_files_with_multiple_documentation_files(self) -> None:
        """Test on_files with requirements spread across multiple documentation files."""
        # Create multiple mock files with requirements
        mock_file1 = Mock()
        mock_file1.src_dir = "docs"
        mock_file1.content_string = "> REQ-1\n> First file requirement.\n"

        mock_file2 = Mock()
        mock_file2.src_dir = "docs"
        mock_file2.content_string = "> REQ-2\n> Second file requirement.\n"

        # Create mock files collection
        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file1, mock_file2]

        # Create mock config
        mock_config = Mock()

        # Call on_files
        result = self.plugin.on_files(mock_files, config=mock_config)

        # Should return the files object
        self.assertEqual(result, mock_files)

        # Should add generated files for each requirement + index
        self.assertEqual(mock_files.append.call_count, 3)  # 2 requirements + 1 index

    def test_generated_file_content(self) -> None:
        """Test that generated files are created with correct structure."""
        # Create test markdown content
        test_content = "> REQ-1\n> Test requirement.\n> critical"

        # Create mock file
        mock_file = Mock()
        mock_file.src_dir = "docs"
        mock_file.content_string = test_content

        # Create mock files collection
        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file]

        # Create mock config
        mock_config = Mock()

        # Call on_files
        self.plugin.on_files(mock_files, config=mock_config)

        # Get the generated file calls
        calls = mock_files.append.call_args_list
        generated_files = [call[0][0] for call in calls]

        # Find the requirement file
        req_file = None
        for file in generated_files:
            if hasattr(file, "src_uri") and file.src_uri == "reqsnake/REQ/REQ-1.md":
                req_file = file
                break

        self.assertIsNotNone(req_file)
        if req_file is not None:
            # Test that the file was created with the correct structure
            self.assertEqual(req_file.src_uri, "reqsnake/REQ/REQ-1.md")
            self.assertEqual(req_file.inclusion, InclusionLevel.INCLUDED)

    def test_index_file_content(self) -> None:
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
        mock_file.src_dir = "docs"
        mock_file.content_string = test_content

        # Create mock files collection
        mock_files = Mock()
        mock_files.documentation_pages.return_value = [mock_file]

        # Create mock config
        mock_config = Mock()

        # Call on_files
        self.plugin.on_files(mock_files, config=mock_config)

        # Get the generated file calls
        calls = mock_files.append.call_args_list
        generated_files = [call[0][0] for call in calls]

        # Find the index file
        index_file = None
        for file in generated_files:
            if hasattr(file, "src_uri") and file.src_uri == "reqsnake/index.md":
                index_file = file
                break

        self.assertIsNotNone(index_file)
        if index_file is not None:
            # Test that the index file was created with the correct structure
            self.assertEqual(index_file.src_uri, "reqsnake/index.md")
            self.assertEqual(index_file.inclusion, InclusionLevel.INCLUDED)

    def test_plugin_disabled(self) -> None:
        """Test that the plugin does nothing when disabled."""
        plugin = ReqSnake()
        plugin.config["enabled"] = False
        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [self.mock_file_with_reqs]
        mock_files.append = MagicMock()
        plugin.on_files(mock_files, config=self.mock_config)
        # Plugin is disabled, so no files should be appended
        mock_files.append.assert_not_called()


class TestIgnoreIntegration(unittest.TestCase):
    """Integration tests for .requirementsignore functionality with the plugin."""

    def setUp(self) -> None:
        """Set up test fixtures with temporary directory."""
        self.plugin = ReqSnake()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create mock config pointing to temp directory
        self.mock_config = Mock()
        self.mock_config.config_file_path = str(self.temp_path / "mkdocs.yml")

        # Create mock files
        self.create_mock_files()

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def create_mock_files(self) -> None:
        """Create mock files for testing."""
        # File with requirements that should be processed
        self.mock_file_normal = Mock()
        self.mock_file_normal.src_uri = "docs/requirements.md"
        self.mock_file_normal.content_string = """> REQ-1
> This is a normal requirement
> critical"""

        # File that should be ignored based on pattern
        self.mock_file_ignored = Mock()
        self.mock_file_ignored.src_uri = "docs/test_file.md"
        self.mock_file_ignored.content_string = """> REQ-2
> This requirement should be ignored
> critical"""

        # File in ignored directory
        self.mock_file_build = Mock()
        self.mock_file_build.src_uri = "build/generated.md"
        self.mock_file_build.content_string = """> REQ-3
> This requirement is in build directory
> critical"""

        # Another normal file
        self.mock_file_normal2 = Mock()
        self.mock_file_normal2.src_uri = "docs/specs.md"
        self.mock_file_normal2.content_string = """> REQ-4
> Another normal requirement"""

    def test_ignore_functionality_no_ignore_file(self) -> None:
        """Test that all files are processed when no .requirementsignore exists."""
        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            self.mock_file_normal,
            self.mock_file_ignored,
            self.mock_file_build,
            self.mock_file_normal2,
        ]
        mock_files.append = MagicMock()

        result = self.plugin.on_files(mock_files, config=self.mock_config)

        # All 4 requirements should be processed since no ignore file exists
        self.assertEqual(mock_files.append.call_count, 5)  # 4 req pages + 1 index

    def test_ignore_functionality_with_patterns(self) -> None:
        """Test that files are ignored based on .requirementsignore patterns."""
        # Create .requirementsignore file
        ignore_content = """# Ignore test files
test_*.md
build/
"""
        ignore_file = self.temp_path / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            self.mock_file_normal,  # Should be processed
            self.mock_file_ignored,  # Should be ignored (test_*.md)
            self.mock_file_build,  # Should be ignored (build/)
            self.mock_file_normal2,  # Should be processed
        ]
        mock_files.append = MagicMock()

        with patch("mkdocs_reqsnake.plugin.logger") as mock_logger:
            result = self.plugin.on_files(mock_files, config=self.mock_config)

            # Only 2 requirements should be processed (REQ-1 and REQ-4)
            self.assertEqual(mock_files.append.call_count, 3)  # 2 req pages + 1 index

            # Check that ignored files were logged
            ignore_calls = [
                call
                for call in mock_logger.info.call_args_list
                if "Ignored" in str(call)
            ]
            self.assertEqual(len(ignore_calls), 1)
            self.assertIn("Ignored 2 files", str(ignore_calls[0]))

    def test_ignore_functionality_glob_patterns(self) -> None:
        """Test that glob patterns work correctly in .requirementsignore."""
        # Create .requirementsignore file with glob patterns
        ignore_content = """*.tmp
**/build/**
docs/test_*
"""
        ignore_file = self.temp_path / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        # Create additional mock files
        mock_file_tmp = Mock()
        mock_file_tmp.src_uri = "file.tmp"
        mock_file_tmp.content_string = "> REQ-TMP\n> Temp requirement"

        mock_file_nested_build = Mock()
        mock_file_nested_build.src_uri = "project/build/nested.md"
        mock_file_nested_build.content_string = (
            "> REQ-NESTED\n> Nested build requirement"
        )

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            self.mock_file_normal,  # Should be processed
            self.mock_file_ignored,  # Should be ignored (docs/test_*)
            mock_file_tmp,  # Should be ignored (*.tmp)
            mock_file_nested_build,  # Should be ignored (**/build/**)
            self.mock_file_normal2,  # Should be processed
        ]
        mock_files.append = MagicMock()

        with patch("mkdocs_reqsnake.plugin.logger") as mock_logger:
            result = self.plugin.on_files(mock_files, config=self.mock_config)

            # Only 2 requirements should be processed
            self.assertEqual(mock_files.append.call_count, 3)  # 2 req pages + 1 index

            # Check that ignored files were logged
            ignore_calls = [
                call
                for call in mock_logger.info.call_args_list
                if "Ignored" in str(call)
            ]
            self.assertEqual(len(ignore_calls), 1)
            self.assertIn("Ignored 3 files", str(ignore_calls[0]))

    def test_ignore_functionality_with_comments_and_blanks(self) -> None:
        """Test that comments and blank lines in .requirementsignore are handled correctly."""
        ignore_content = """# This is a comment
# Another comment

test_*.md

# Ignore build directories
build/

# End comment"""
        ignore_file = self.temp_path / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            self.mock_file_normal,  # Should be processed
            self.mock_file_ignored,  # Should be ignored
            self.mock_file_build,  # Should be ignored
            self.mock_file_normal2,  # Should be processed
        ]
        mock_files.append = MagicMock()

        result = self.plugin.on_files(mock_files, config=self.mock_config)

        # Only 2 requirements should be processed
        self.assertEqual(mock_files.append.call_count, 3)  # 2 req pages + 1 index

    def test_ignore_functionality_error_handling(self) -> None:
        """Test that plugin handles .requirementsignore read errors gracefully."""
        # Create a .requirementsignore file and then make it unreadable
        ignore_file = self.temp_path / ".requirementsignore"
        ignore_file.write_text("test_*.md")
        ignore_file.chmod(0o000)  # Make file unreadable

        mock_files = MagicMock()
        mock_files.documentation_pages.return_value = [
            self.mock_file_normal,
            self.mock_file_ignored,
        ]
        mock_files.append = MagicMock()

        try:
            # Should not raise an exception and should process all files
            result = self.plugin.on_files(mock_files, config=self.mock_config)

            # All files should be processed when ignore file can't be read
            self.assertEqual(mock_files.append.call_count, 3)  # 2 req pages + 1 index
        finally:
            # Restore permissions for cleanup
            ignore_file.chmod(0o644)


if __name__ == "__main__":
    unittest.main()
