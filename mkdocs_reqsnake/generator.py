"""Content generation logic for ReqSnake."""

from .models import ParsedRequirement


def generate_requirement_page_content(
    parsed_req: ParsedRequirement, all_requirements: list[ParsedRequirement]
) -> str:
    """
    Generate Markdown content for a single requirement page.

    Args:
        parsed_req: ParsedRequirement object with requirement and source file.
        all_requirements: List of all ParsedRequirement objects to find children.

    Returns:
        Markdown content for the requirement page.

    """
    req = parsed_req.requirement
    source_file = parsed_req.source_file

    def _truncate_description(desc: str, max_words: int = 4) -> str:
        """Truncate description to first few words for diagram display.

        Args:
            desc: The description to truncate.
            max_words: Maximum number of words to keep.

        Returns:
            The truncated description.
        """
        words = desc.split()
        if len(words) <= max_words:
            return desc
        return " ".join(words[:max_words]) + "..."

    def _sanitize_for_mermaid(text: str) -> str:
        """Sanitize text for use in Mermaid mindmap nodes.

        Args:
            text: The text to sanitize.

        Returns:
            Sanitized text wrapped in backticks for safe Mermaid rendering.
        """
        # Always wrap in backticks for future-proof sanitization
        return f'"`{text}`"'

    def _get_requirement_by_id(req_id: str) -> str:
        """Get requirement description by ID.

        Args:
            req_id: The requirement ID to look for.

        Returns:
            The requirement description, or empty string if not found.
        """
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

    # Add Mermaid mindmap if there are children
    if children:
        lines.append("## Children Mindmap")
        lines.append("")
        lines.append("```mermaid")
        lines.append("mindmap")
        # Sanitize root node text
        root_text = _sanitize_for_mermaid(req.req_id)
        lines.append(f"  root(({root_text}))")

        # Add child nodes
        sorted_children = sorted(children)
        for child_id in sorted_children:
            child_desc = _get_requirement_by_id(child_id)
            if child_desc:
                # Truncate description for mindmap display
                truncated_desc = _truncate_description(child_desc, max_words=7)
                # Sanitize the text for Mermaid mindmap
                sanitized_text = _sanitize_for_mermaid(f"{child_id}: {truncated_desc}")
                lines.append(f"    {child_id}[{sanitized_text}]")
            else:
                lines.append(f"    {child_id}")

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
            # Extract category for hierarchical path
            parent_category = (
                parent_id.rsplit("-", 1)[0] if "-" in parent_id else "OTHER"
            )

            if parent_desc:
                lines.append(
                    f"- [{parent_id}](../{parent_category}/{parent_id}.md) - "
                    f"{parent_desc}"
                )
            else:
                lines.append(f"- [{parent_id}](../{parent_category}/{parent_id}.md)")
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
            # Extract category for hierarchical path
            child_category = child_id.rsplit("-", 1)[0] if "-" in child_id else "OTHER"

            if child_desc:
                lines.append(
                    f"- [{child_id}](../{child_category}/{child_id}.md) - {child_desc}"
                )
            else:
                lines.append(f"- [{child_id}](../{child_category}/{child_id}.md)")
        lines.append("")

    # Add source file link
    lines.append("---")
    lines.append(f"*Source: [{source_file}](../../{source_file})*")

    # Add parent flowchart at the bottom if there are parents
    if req.parents:
        lines.append("")
        lines.append("## Parent Hierarchy Flowchart")
        lines.append("")
        lines.append("```mermaid")
        lines.append("graph TD")

        # Get all ancestors in the hierarchy
        def _get_all_ancestors(
            req_id: str, visited: set[str] | None = None
        ) -> list[str]:
            """Get all ancestor requirement IDs up to root level.

            Args:
                req_id: The requirement ID to find ancestors for.
                visited: Set of already visited IDs to prevent cycles.

            Returns:
                List of ancestor IDs from immediate parents to root level.
            """
            if visited is None:
                visited = set()

            if req_id in visited:
                return []  # Prevent infinite loops

            visited.add(req_id)
            ancestors = []

            # Find the requirement object
            current_req = None
            for other_req in all_requirements:
                if other_req.requirement.req_id == req_id:
                    current_req = other_req.requirement
                    break

            if current_req and current_req.parents:
                for parent_id in current_req.parents:
                    ancestors.append(parent_id)
                    # Recursively get grandparents
                    ancestors.extend(_get_all_ancestors(parent_id, visited.copy()))

            return ancestors

        all_ancestors = _get_all_ancestors(req.req_id)

        # Remove duplicates while preserving order
        seen = set()
        unique_ancestors = []
        for ancestor in all_ancestors:
            if ancestor not in seen:
                seen.add(ancestor)
                unique_ancestors.append(ancestor)

        # Generate flowchart nodes for current requirement and all ancestors
        all_nodes = [req.req_id, *unique_ancestors]

        # Add node definitions with sanitized labels
        for node_id in all_nodes:
            node_desc = (
                _get_requirement_by_id(node_id)
                if node_id != req.req_id
                else req.description
            )
            if node_desc:
                truncated_desc = _truncate_description(node_desc, max_words=7)
                sanitized_label = _sanitize_for_mermaid(f"{node_id}: {truncated_desc}")
                if node_id == req.req_id:
                    # Highlight current requirement
                    lines.append(f"    {node_id}[{sanitized_label}]:::current")
                else:
                    lines.append(f"    {node_id}[{sanitized_label}]")
            else:
                lines.append(f"    {node_id}[{_sanitize_for_mermaid(node_id)}]")

        # Add edges from current requirement to its parents
        def _add_edges_recursive(
            child_id: str, visited: set[str] | None = None
        ) -> None:
            """Add edges from child to parents recursively.

            Args:
                child_id: The child requirement ID.
                visited: Set of visited IDs to prevent cycles.
            """
            if visited is None:
                visited = set()

            if child_id in visited:
                return

            visited.add(child_id)

            # Find the requirement object
            child_req = None
            for other_req in all_requirements:
                if other_req.requirement.req_id == child_id:
                    child_req = other_req.requirement
                    break

            if child_req and child_req.parents:
                for parent_id in child_req.parents:
                    lines.append(f"    {child_id} --> {parent_id}")
                    # Recursively add edges for parent
                    _add_edges_recursive(parent_id, visited.copy())

        _add_edges_recursive(req.req_id)

        # Add CSS styling for current requirement
        lines.append(
            "    classDef current fill:#ff9800,stroke:#e65100,stroke-width:3px,"
            "color:#fff"
        )

        lines.append("```")

    return "\n".join(lines)


def generate_requirement_index_content(
    parsed_requirements: list[ParsedRequirement],
) -> str:
    """
    Generate Markdown content for the requirements index page.

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
