"""Utility functions for ReqSnake."""

import fnmatch
from pathlib import Path
from typing import List


def load_ignore_patterns(config_dir: Path) -> List[str]:
    """Load ignore patterns from .requirementsignore file.

    Args:
        config_dir: Directory to look for .requirementsignore file.

    Returns:
        List of ignore patterns, empty if file doesn't exist.

    """
    ignore_file = config_dir / ".requirementsignore"
    if not ignore_file.exists():
        return []

    try:
        patterns = []
        with ignore_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    patterns.append(line)
        return patterns
    except (OSError, UnicodeDecodeError):
        # If we can't read the file, just return empty patterns
        return []


def should_ignore_file(file_path: str, ignore_patterns: List[str]) -> bool:
    """Check if a file should be ignored based on ignore patterns.

    Args:
        file_path: The file path to check.
        ignore_patterns: List of ignore patterns (gitignore-style).

    Returns:
        True if the file should be ignored, False otherwise.

    """
    if not ignore_patterns:
        return False

    # Normalize path separators to forward slashes for consistent pattern matching
    normalized_path = str(file_path).replace("\\", "/")

    for pattern in ignore_patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            dir_pattern = pattern.rstrip("/")
            # Check if the pattern matches any directory in the path
            path_parts = normalized_path.split("/")
            # Check each directory component (exclude the filename)
            for i in range(len(path_parts) - 1):
                dir_component = path_parts[i]
                if fnmatch.fnmatch(dir_component, dir_pattern):
                    return True
                # Also check the partial path up to this point
                partial_path = "/".join(path_parts[: i + 1])
                if fnmatch.fnmatch(partial_path, dir_pattern):
                    return True
        else:
            # File or glob pattern matching
            if fnmatch.fnmatch(normalized_path, pattern):
                return True
            # Also check just the filename
            filename = normalized_path.split("/")[-1]
            if fnmatch.fnmatch(filename, pattern):
                return True

    return False
