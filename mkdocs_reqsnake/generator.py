"""Content generation logic for ReqSnake."""

from pathlib import Path
from typing import Dict, List

from .models import ParsedRequirement


def generate_requirement_page_content(
    parsed_req: ParsedRequirement, all_requirements: List[ParsedRequirement]
) -> str:
    """Generate Markdown content for a single requirement page.

    Args:
        parsed_req: ParsedRequirement object with requirement and source file.
        all_requirements: List of all ParsedRequirement objects to find children.

    Returns:
        Markdown content for the requirement page.

    """
    req = parsed_req.requirement
    source_file = parsed_req.source_file

    def _truncate_description(desc: str, max_words: int = 4) -> str:
        """Truncate description to first few words for diagram display."""
        words = desc.split()
        if len(words) <= max_words:
            return desc
        return " ".join(words[:max_words]) + "..."

    def _get_requirement_by_id(req_id: str) -> str:
        """Get requirement description by ID."""
        for other_req in all_requirements:
            if other_req.requirement.req_id == req_id:
                return other_req.requirement.description
        return ""

    lines = []
    lines.append(f"# {req.req_id}")
    lines.append("")

    # Add status indicators
    if req.critical:
        lines.append("⚠️ **Critical requirement**")
        lines.append("")

    lines.append(f"{req.description}")
    lines.append("")

    if req.completed:
        lines.append("✅ **Completed**")
        lines.append("")

    # Find children (one level down)
    children = []
    for other_req in all_requirements:
        if req.req_id in other_req.requirement.parents:
            children.append(other_req.requirement.req_id)

    # Add Mermaid diagram if there are parents or children
    if req.parents or children:
        lines.append("## Relationship Diagram")
        lines.append("")
        lines.append("```mermaid")
        lines.append("graph LR")

        # Add parent nodes and connections
        for parent_id in req.parents:
            parent_desc = _get_requirement_by_id(parent_id)
            parent_label = (
                f"{parent_id}<br/>{_truncate_description(parent_desc)}"
                if parent_desc
                else parent_id
            )
            lines.append(f'    {parent_id}["{parent_label}"]')
            lines.append(f"    {parent_id} --> {req.req_id}")

        # Add current requirement node
        current_label = f"{req.req_id}<br/>{_truncate_description(req.description)}"
        lines.append(f'    {req.req_id}["{current_label}"]')

        # Add child nodes and connections
        sorted_children = sorted(children)
        for child_id in sorted_children:
            child_desc = _get_requirement_by_id(child_id)
            child_label = (
                f"{child_id}<br/>{_truncate_description(child_desc)}"
                if child_desc
                else child_id
            )
            lines.append(f'    {child_id}["{child_label}"]')
            lines.append(f"    {req.req_id} --> {child_id}")

        # Add click events for navigation
        for parent_id in req.parents:
            lines.append(f'    click {parent_id} "/reqsnake/{parent_id}"')
        lines.append(f'    click {req.req_id} "/reqsnake/{req.req_id}"')
        for child_id in sorted_children:
            lines.append(f'    click {child_id} "/reqsnake/{child_id}"')

        # Add styling for different node types
        if req.parents:
            lines.append(
                "    classDef parentStyle fill:transparent,stroke:#2196f3,stroke-width:3px,color:#2196f3"
            )
            for parent_id in req.parents:
                lines.append(f"    class {parent_id} parentStyle")

        lines.append(
            "    classDef currentStyle fill:transparent,stroke:#ff9800,stroke-width:4px,color:#ff9800"
        )
        lines.append(f"    class {req.req_id} currentStyle")

        if children:
            lines.append(
                "    classDef childStyle fill:transparent,stroke:#9c27b0,stroke-width:3px,color:#9c27b0"
            )
            for child_id in sorted_children:
                lines.append(f"    class {child_id} childStyle")

        lines.append("```")
        lines.append("")

    # Add parents if any
    if req.parents:
        # Calculate parent completion statistics
        parent_total = len(req.parents)
        parent_completed = 0
        for parent_id in req.parents:
            for other_req in all_requirements:
                if (
                    other_req.requirement.req_id == parent_id
                    and other_req.requirement.completed
                ):
                    parent_completed += 1
                    break

        lines.append(f"## Parents ({parent_completed}/{parent_total} completed)")
        lines.append("")
        for parent_id in req.parents:
            # Find the parent requirement to get its description
            parent_desc = _get_requirement_by_id(parent_id)
            if parent_desc:
                lines.append(f"- [{parent_id}](./{parent_id}.md) - {parent_desc}")
            else:
                lines.append(f"- [{parent_id}](./{parent_id}.md)")
        lines.append("")

    # Add children if any
    if children:
        # Calculate child completion statistics
        child_total = len(children)
        child_completed = 0
        for child_id in children:
            for other_req in all_requirements:
                if (
                    other_req.requirement.req_id == child_id
                    and other_req.requirement.completed
                ):
                    child_completed += 1
                    break

        lines.append(f"## Children ({child_completed}/{child_total} completed)")
        lines.append("")
        for child_id in sorted(children):
            # Find the child requirement to get its description
            child_desc = _get_requirement_by_id(child_id)
            if child_desc:
                lines.append(f"- [{child_id}](./{child_id}.md) - {child_desc}")
            else:
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

    # Calculate overall completion statistics
    total_requirements = len(parsed_requirements)
    completed_requirements = sum(
        1 for pr in parsed_requirements if pr.requirement.completed
    )
    lines.append(
        f"**Overall completion: {completed_requirements}/{total_requirements} requirements**"
    )
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
        file_reqs = file_groups[file_path]
        file_total = len(file_reqs)
        file_completed = sum(1 for pr in file_reqs if pr.requirement.completed)

        lines.append(f"## {file_path}")
        lines.append(f"*Completion: {file_completed}/{file_total} requirements*")
        lines.append("")

        # Sort requirements by ID for consistent output
        sorted_reqs = sorted(file_reqs, key=lambda pr: pr.requirement.req_id)

        for pr in sorted_reqs:
            req = pr.requirement
            status_emoji = "✅" if req.completed else "⏳"
            critical_indicator = "⚠️ " if req.critical else ""

            lines.append(
                f"- {status_emoji} {critical_indicator}[{req.req_id}](./{req.req_id}.md): {req.description}"
            )
        lines.append("")

    return "\n".join(lines)
