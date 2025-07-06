"""Utility functions for ReqSnake."""

import fnmatch
from pathlib import Path
from typing import Dict, List

from .models import DiffType, Requirement


def progress_bar(completed: int, total: int, width: int = 20) -> str:
    """Generate a Unicode progress bar string.

    Args:
        completed: Number of completed items.
        total: Total number of items.
        width: Width of the progress bar in characters.

    Returns:
        Unicode progress bar string.

    """
    if total <= 0:
        return "`[" + (" " * width) + "]`"

    # Unicode 1/8 blocks: ▏▎▍▌▋▊▉█
    blocks = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    frac = min(max(completed / total, 0), 1)  # Clamp between 0 and 1

    if width == 1:
        # For width 1, show full block if at least half complete
        return f"`[{'█' if frac >= 0.5 else ' '}]`"

    total_blocks = frac * width
    full_blocks = int(total_blocks)
    partial_block_frac = total_blocks - full_blocks
    partial_block_idx = int(round(partial_block_frac * 8))

    bar = "█" * full_blocks
    if full_blocks < width:
        if partial_block_idx > 0 and partial_block_idx < 8:
            bar += blocks[partial_block_idx]
            bar += " " * (width - full_blocks - 1)
        else:
            bar += " " * (width - full_blocks)

    return f"`[{bar}]`"


def diff_requirements(
    old: List[Requirement], new: List[Requirement]
) -> Dict[DiffType, List[Requirement]]:
    """Compare two lists of requirements and return a diff dict.

    Args:
        old: Previous list of requirements.
        new: Current list of requirements.

    Returns:
        Dictionary mapping DiffType to list of requirements.

    """
    old_dict: Dict[str, Requirement] = {r.req_id: r for r in old}
    new_dict: Dict[str, Requirement] = {r.req_id: r for r in new}

    added: List[Requirement] = [
        new_dict[rid] for rid in new_dict if rid not in old_dict
    ]
    removed: List[Requirement] = [
        old_dict[rid] for rid in old_dict if rid not in new_dict
    ]
    changed: List[Requirement] = [
        new_dict[rid]
        for rid in new_dict
        if rid in old_dict and new_dict[rid] != old_dict[rid]
    ]

    return {DiffType.ADDED: added, DiffType.REMOVED: removed, DiffType.CHANGED: changed}


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
