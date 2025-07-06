"""Unit tests for utility functions."""

import tempfile
from pathlib import Path

import pytest

from mkdocs_reqsnake.utils import load_ignore_patterns, should_ignore_file


class TestIgnorePatterns:
    """Unit tests for .requirementsignore functionality."""

    def test_load_ignore_patterns_no_file(self, temp_dir):
        """Test load_ignore_patterns when .requirementsignore doesn't exist."""
        patterns = load_ignore_patterns(temp_dir)
        assert patterns == []

    def test_load_ignore_patterns_empty_file(self, temp_dir):
        """Test load_ignore_patterns with empty .requirementsignore file."""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text("")

        patterns = load_ignore_patterns(temp_dir)
        assert patterns == []

    def test_load_ignore_patterns_with_content(self, temp_dir):
        """Test load_ignore_patterns with various patterns."""
        ignore_content = """# Comment line
*.tmp
*~

build/
dist/
example.md
test_*.md
"""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        patterns = load_ignore_patterns(temp_dir)
        expected = ["*.tmp", "*~", "build/", "dist/", "example.md", "test_*.md"]
        assert patterns == expected

    def test_load_ignore_patterns_comments_and_blanks(self, temp_dir):
        """Test that comments and blank lines are ignored."""
        ignore_content = """# This is a comment
*.tmp
# Another comment

# Empty line above
build/
"""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        patterns = load_ignore_patterns(temp_dir)
        expected = ["*.tmp", "build/"]
        assert patterns == expected

    def test_load_ignore_patterns_unicode_error(self, temp_dir):
        """Test load_ignore_patterns handles unicode decode errors gracefully."""
        ignore_file = temp_dir / ".requirementsignore"
        # Write binary data that would cause decode error
        with ignore_file.open("wb") as f:
            f.write(b"\xff\xfe\x00\x00")

        patterns = load_ignore_patterns(temp_dir)
        assert patterns == []

    def test_load_ignore_patterns_permission_error(self, temp_dir):
        """Test load_ignore_patterns handles permission errors gracefully."""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text("test_*.md")
        ignore_file.chmod(0o000)  # Make file unreadable

        try:
            patterns = load_ignore_patterns(temp_dir)
            # Should return empty list on permission error
            assert patterns == []
        finally:
            # Restore permissions for cleanup
            ignore_file.chmod(0o644)


class TestShouldIgnoreFile:
    """Unit tests for file ignore pattern matching."""

    def test_should_ignore_file_no_patterns(self):
        """Test should_ignore_file with empty patterns list."""
        assert should_ignore_file("any/file.md", []) is False

    def test_should_ignore_file_exact_match(self):
        """Test should_ignore_file with exact filename matches."""
        patterns = ["example.md", "README.txt"]

        assert should_ignore_file("example.md", patterns) is True
        assert should_ignore_file("path/to/example.md", patterns) is True
        assert should_ignore_file("other.md", patterns) is False

    def test_should_ignore_file_glob_patterns(self):
        """Test should_ignore_file with glob patterns."""
        patterns = ["*.tmp", "test_*.md", ".*"]

        assert should_ignore_file("file.tmp", patterns) is True
        assert should_ignore_file("path/file.tmp", patterns) is True
        assert should_ignore_file("test_example.md", patterns) is True
        assert should_ignore_file("path/test_example.md", patterns) is True
        assert should_ignore_file(".hidden", patterns) is True
        assert should_ignore_file("normal.md", patterns) is False

    def test_should_ignore_file_directory_patterns(self):
        """Test should_ignore_file with directory patterns."""
        patterns = ["build/", "node_modules/", "dist/"]

        assert should_ignore_file("build/output.md", patterns) is True
        assert should_ignore_file("project/build/file.md", patterns) is True
        assert should_ignore_file("node_modules/package/readme.md", patterns) is True
        assert should_ignore_file("src/file.md", patterns) is False
        assert should_ignore_file("buildfile.md", patterns) is False

    def test_should_ignore_file_mixed_patterns(self):
        """Test should_ignore_file with mixed pattern types."""
        patterns = ["*.tmp", "build/", "example.md", "test_*"]

        # File patterns
        assert should_ignore_file("file.tmp", patterns) is True
        assert should_ignore_file("example.md", patterns) is True

        # Directory patterns
        assert should_ignore_file("build/file.md", patterns) is True

        # Glob patterns
        assert should_ignore_file("test_something", patterns) is True

        # Should not be ignored
        assert should_ignore_file("normal.md", patterns) is False
        assert should_ignore_file("src/normal.md", patterns) is False

    def test_should_ignore_file_path_normalization(self):
        """Test that paths with different separators are handled correctly."""
        patterns = ["build/", "*.tmp"]

        # Test with different path separators
        assert should_ignore_file("build\\file.md", patterns) is True
        assert should_ignore_file("build/file.md", patterns) is True
        assert should_ignore_file("path\\to\\file.tmp", patterns) is True
        assert should_ignore_file("path/to/file.tmp", patterns) is True

    def test_should_ignore_file_case_sensitivity(self):
        """Test case sensitivity in pattern matching."""
        patterns = ["*.TMP", "Build/"]

        # Test case sensitivity (should be case-sensitive on most systems)
        assert should_ignore_file("file.tmp", patterns) is False  # Different case
        assert should_ignore_file("file.TMP", patterns) is True  # Exact case

    def test_should_ignore_file_complex_globs(self):
        """Test complex glob patterns."""
        patterns = ["**/build/**", "test_*.{md,txt}", "docs/**/temp/*"]

        assert should_ignore_file("project/build/output.md", patterns) is True
        assert (
            should_ignore_file("deep/project/build/nested/file.txt", patterns) is True
        )
        assert should_ignore_file("test_file.md", patterns) is True
        assert should_ignore_file("test_file.txt", patterns) is True
        assert should_ignore_file("docs/section/temp/file.md", patterns) is True

    def test_should_ignore_file_edge_cases(self):
        """Test edge cases in file pattern matching."""
        patterns = ["", "*/", "*"]  # Edge case patterns

        # Empty pattern should not match anything
        assert should_ignore_file("file.md", [""]) is False

        # "*/" should match directories
        assert should_ignore_file("dir/", ["*/"]) is True

        # "*" should match everything
        assert should_ignore_file("anything.md", ["*"]) is True

    def test_should_ignore_file_absolute_vs_relative_paths(self):
        """Test pattern matching with absolute vs relative paths."""
        patterns = ["build/", "*.tmp"]

        # Both absolute and relative paths should work
        assert should_ignore_file("/absolute/build/file.md", patterns) is True
        assert should_ignore_file("relative/build/file.md", patterns) is True
        assert should_ignore_file("/absolute/file.tmp", patterns) is True
        assert should_ignore_file("relative/file.tmp", patterns) is True


class TestUtilsIntegration:
    """Integration tests for utility functions."""

    def test_ignore_workflow_integration(self, temp_dir):
        """Test the full ignore workflow integration."""
        # Create ignore file with patterns
        ignore_content = """
# Test ignore patterns
*.tmp
build/
test_*
"""
        ignore_file = temp_dir / ".requirementsignore"
        ignore_file.write_text(ignore_content)

        # Load patterns
        patterns = load_ignore_patterns(temp_dir)

        # Test various files
        test_files = [
            ("normal.md", False),
            ("file.tmp", True),
            ("build/output.md", True),
            ("test_file.md", True),
            ("docs/readme.md", False),
        ]

        for file_path, should_be_ignored in test_files:
            result = should_ignore_file(file_path, patterns)
            assert result is should_be_ignored, (
                f"File {file_path} ignore result mismatch"
            )

    def test_ignore_file_types_comprehensive(self):
        """Test comprehensive file type patterns."""
        patterns = [
            "*.log",
            "*.tmp",
            "*.cache",  # Temporary files
            "build/",
            "dist/",
            ".git/",  # Build directories
            "test_*",
            "*_test.*",  # Test files
            ".*",  # Hidden files
        ]

        ignored_files = [
            "app.log",
            "temp.tmp",
            "data.cache",
            "build/output.js",
            "dist/bundle.css",
            ".git/config",
            "test_unit.py",
            "module_test.js",
            ".gitignore",
            ".hidden",
        ]

        not_ignored_files = [
            "README.md",
            "src/main.py",
            "docs/guide.md",
            "requirements.txt",
            "package.json",
        ]

        for file_path in ignored_files:
            assert should_ignore_file(file_path, patterns) is True, (
                f"{file_path} should be ignored"
            )

        for file_path in not_ignored_files:
            assert should_ignore_file(file_path, patterns) is False, (
                f"{file_path} should not be ignored"
            )
