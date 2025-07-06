"""Content generation logic for ReqSnake."""

from .models import ParsedRequirement


def generate_requirement_page_content(
    parsed_req: ParsedRequirement, all_requirements: list[ParsedRequirement]
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

    def _requirement_exists(req_id: str) -> bool:
        """Check if a requirement exists in the parsed requirements."""
        return any(
            other_req.requirement.req_id == req_id for other_req in all_requirements
        )

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

    # Add Mermaid mindmap if there are children
    if children:
        lines.append("## Children Mindmap")
        lines.append("")
        lines.append("```mermaid")
        lines.append("mindmap")
        lines.append(f"  root(({req.req_id}))")

        # Add child nodes
        sorted_children = sorted(children)
        for child_id in sorted_children:
            child_desc = _get_requirement_by_id(child_id)
            if child_desc:
                # Truncate description for mindmap display
                truncated_desc = _truncate_description(child_desc, max_words=5)
                lines.append(f"    {child_id}[{child_id}: {truncated_desc}]")
            else:
                lines.append(f"    {child_id}")

        lines.append("```")
        lines.append("")

    # Add parents if any
    if req.parents:
        # Calculate parent completion statistics (only for existing parents)
        existing_parents = [p for p in req.parents if _requirement_exists(p)]
        parent_total = len(existing_parents)
        parent_completed = 0
        for parent_id in existing_parents:
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
            if _requirement_exists(parent_id):
                # Find the parent requirement to get its description
                parent_desc = _get_requirement_by_id(parent_id)
                # Extract category for hierarchical path
                if "-" in parent_id:
                    parent_category = parent_id.rsplit("-", 1)[0]
                else:
                    parent_category = "OTHER"

                if parent_desc:
                    lines.append(
                        f"- [{parent_id}](../{parent_category}/{parent_id}.md) - "
                        f"{parent_desc}"
                    )
                else:
                    lines.append(
                        f"- [{parent_id}](../{parent_category}/{parent_id}.md)"
                    )
            else:
                lines.append(f"- {parent_id} (not found)")
        lines.append("")

    # Add children if any
    if children:
        # Calculate child completion statistics (only for existing children)
        existing_children = [c for c in children if _requirement_exists(c)]
        child_total = len(existing_children)
        child_completed = 0
        for child_id in existing_children:
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
            if _requirement_exists(child_id):
                # Find the child requirement to get its description
                child_desc = _get_requirement_by_id(child_id)
                # Extract category for hierarchical path
                if "-" in child_id:
                    child_category = child_id.rsplit("-", 1)[0]
                else:
                    child_category = "OTHER"

                if child_desc:
                    lines.append(
                        f"- [{child_id}](../{child_category}/{child_id}.md) - "
                        f"{child_desc}"
                    )
                else:
                    lines.append(f"- [{child_id}](../{child_category}/{child_id}.md)")
            else:
                lines.append(f"- {child_id} (not found)")
        lines.append("")

    # Add source file link
    lines.append("---")
    lines.append(f"*Source: [{source_file}](../../{source_file})*")

    return "\n".join(lines)


def generate_requirement_index_content(
    parsed_requirements: list[ParsedRequirement],
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
        f"**Overall completion: {completed_requirements}/"
        f"{total_requirements} requirements**"
    )
    lines.append("")

    # Group by requirement category (e.g., REQ-CORE, REQ-PARSER, REQ-TEST)
    category_groups: dict[str, list[ParsedRequirement]] = {}
    for pr in parsed_requirements:
        req_id = pr.requirement.req_id
        # Extract category from requirement ID (everything before the last dash)
        category = req_id.rsplit("-", 1)[0] if "-" in req_id else "OTHER"

        if category not in category_groups:
            category_groups[category] = []
        category_groups[category].append(pr)

    # Sort categories and requirements for consistent output
    sorted_categories = sorted(category_groups.keys())

    for category in sorted_categories:
        category_reqs = category_groups[category]
        category_total = len(category_reqs)
        category_completed = sum(1 for pr in category_reqs if pr.requirement.completed)

        lines.append(f"## {category}")
        lines.append(
            f"*Completion: {category_completed}/{category_total} requirements*"
        )
        lines.append("")

        # Sort requirements by ID for consistent output
        sorted_reqs = sorted(category_reqs, key=lambda pr: pr.requirement.req_id)

        for pr in sorted_reqs:
            req = pr.requirement
            status_emoji = "✅" if req.completed else "⏳"
            critical_indicator = "⚠️ " if req.critical else ""

            lines.append(
                f"- {status_emoji} {critical_indicator}[{req.req_id}]"
                f"(./{category}/{req.req_id}.md): {req.description}"
            )
        lines.append("")

    return "\n".join(lines)
