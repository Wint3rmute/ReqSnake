"""Content generation logic for ReqSnake."""

from pathlib import Path
from typing import Dict, List

from .models import ParsedRequirement


def generate_requirement_page_content(parsed_req: ParsedRequirement) -> str:
    """Generate Markdown content for a single requirement page.

    Args:
        parsed_req: ParsedRequirement object with requirement and source file.

    Returns:
        Markdown content for the requirement page.

    """
    req = parsed_req.requirement
    source_file = parsed_req.source_file

    lines = []
    lines.append(f"# {req.req_id}")
    lines.append("")
    lines.append(f"{req.description}")
    lines.append("")

    # Add status indicators
    if req.critical:
        lines.append("⚠️ **Critical requirement**")
        lines.append("")
    if req.completed:
        lines.append("✅ **Completed**")
        lines.append("")

    # Add children if any
    if req.children:
        lines.append("## Children")
        lines.append("")
        for child_id in req.children:
            lines.append(f"- [{child_id}](./{child_id}.md)")
        lines.append("")

    # Add source file link
    lines.append("---")
    lines.append(f"*Source: [{source_file}](../{source_file}#{req.req_id})*")

    return "\n".join(lines)


def generate_requirement_index_content(
    parsed_requirements: List[ParsedRequirement],
) -> str:
    """Generate Markdown content for the requirements index page.

    Args:
        parsed_requirements: List of all ParsedRequirement objects.

    Returns:
        Markdown content for the index page.

    """
    lines = []
    lines.append("# Requirements Index")
    lines.append("")

    # Group by file
    file_groups: Dict[Path, List[ParsedRequirement]] = {}
    for pr in parsed_requirements:
        if pr.source_file not in file_groups:
            file_groups[pr.source_file] = []
        file_groups[pr.source_file].append(pr)

    # Sort files and requirements for consistent output
    sorted_files = sorted(file_groups.keys())

    for file_path in sorted_files:
        lines.append(f"## {file_path}")
        lines.append("")

        # Sort requirements by ID for consistent output
        sorted_reqs = sorted(
            file_groups[file_path], key=lambda pr: pr.requirement.req_id
        )

        for pr in sorted_reqs:
            req = pr.requirement
            status_emoji = "✅" if req.completed else "⏳"
            critical_indicator = "⚠️ " if req.critical else ""

            lines.append(
                f"- {status_emoji} {critical_indicator}[{req.req_id}](./{req.req_id}.md): {req.description}"
            )
        lines.append("")

    return "\n".join(lines)
