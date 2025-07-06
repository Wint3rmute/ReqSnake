"""Utility functions for ReqSnake."""

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
