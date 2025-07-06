"""Content generation logic for ReqSnake."""

from collections import defaultdict

from .models import ParsedRequirement, Requirement


class RequirementLookup:
    """Efficient lookup and relationship management for requirements."""

    def __init__(self, requirements: list[ParsedRequirement]):
        """Initialize lookup with list of requirements.

        Args:
            requirements: List of ParsedRequirement objects to index.
        """
        self._req_map: dict[str, ParsedRequirement] = {
            req.requirement.req_id: req for req in requirements
        }
        self._children_map: dict[str, list[str]] = defaultdict(list)
        self._build_children_map()

    def _build_children_map(self) -> None:
        """Build reverse lookup map for children."""
        for req in self._req_map.values():
            for parent_id in req.requirement.parents:
                self._children_map[parent_id].append(req.requirement.req_id)

    def get_requirement(self, req_id: str) -> ParsedRequirement | None:
        """O(1) requirement lookup.

        Args:
            req_id: The requirement ID to look up.

        Returns:
            ParsedRequirement object if found, None otherwise.
        """
        return self._req_map.get(req_id)

    def get_description(self, req_id: str) -> str:
        """Get requirement description by ID.

        Args:
            req_id: The requirement ID to look up.

        Returns:
            The requirement description, or empty string if not found.
        """
        req = self.get_requirement(req_id)
        return req.requirement.description if req else ""

    def get_children(self, req_id: str) -> list[str]:
        """Get all direct children of a requirement.

        Args:
            req_id: The requirement ID to find children for.

        Returns:
            Sorted list of child requirement IDs.
        """
        return sorted(self._children_map[req_id])

    def get_all_ancestors(
        self, req_id: str, visited: set[str] | None = None
    ) -> list[str]:
        """Get all ancestor IDs with cycle prevention.

        Args:
            req_id: The requirement ID to find ancestors for.
            visited: Set of already visited IDs to prevent cycles.

        Returns:
            List of ancestor IDs from immediate parents to root level.
        """
        if visited is None:
            visited = set()

        if req_id in visited:
            return []

        visited.add(req_id)
        ancestors = []

        req = self.get_requirement(req_id)
        if req and req.requirement.parents:
            for parent_id in req.requirement.parents:
                ancestors.append(parent_id)
                ancestors.extend(self.get_all_ancestors(parent_id, visited.copy()))

        return ancestors


class CompletionStats:
    """Calculate completion statistics for requirement groups."""

    def __init__(self, lookup: RequirementLookup):
        """Initialize with requirement lookup.

        Args:
            lookup: RequirementLookup instance for efficient data access.
        """
        self.lookup = lookup

    def calculate_completion(self, req_ids: list[str]) -> tuple[int, int]:
        """Calculate (completed_count, total_count) for a list of requirement IDs.

        Args:
            req_ids: List of requirement IDs to analyze.

        Returns:
            Tuple of (completed_count, total_count).
        """
        total = len(req_ids)
        completed = sum(
            1
            for req_id in req_ids
            if (req := self.lookup.get_requirement(req_id))
            and req.requirement.completed
        )
        return completed, total


class MermaidGenerator:
    """Base class for Mermaid diagram generation."""

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text for Mermaid rendering.

        Args:
            text: The text to sanitize.

        Returns:
            Sanitized text wrapped in backticks.
        """
        return f'"`{text}`"'

    @staticmethod
    def truncate_description(desc: str, max_words: int = 4) -> str:
        """Truncate description for diagram display.

        Args:
            desc: The description to truncate.
            max_words: Maximum number of words to keep.

        Returns:
            Truncated description with ellipsis if needed.
        """
        words = desc.split()
        if len(words) <= max_words:
            return desc
        return " ".join(words[:max_words]) + "..."


class MindmapGenerator(MermaidGenerator):
    """Generate Mermaid mindmap diagrams."""

    def generate(
        self, root_req: Requirement, children: list[str], lookup: RequirementLookup
    ) -> list[str]:
        """Generate mindmap section for children.

        Args:
            root_req: The root requirement object.
            children: List of child requirement IDs.
            lookup: RequirementLookup for data access.

        Returns:
            List of markdown lines for the mindmap section.
        """
        lines = ["## Children Mindmap", "", "```mermaid", "mindmap"]

        root_text = self.sanitize_text(root_req.req_id)
        lines.append(f"  root(({root_text}))")

        for child_id in children:
            child_desc = lookup.get_description(child_id)
            if child_desc:
                truncated = self.truncate_description(child_desc, max_words=7)
                sanitized = self.sanitize_text(f"{child_id}: {truncated}")
                lines.append(f"    {child_id}[{sanitized}]")
            else:
                lines.append(f"    {child_id}")

        lines.extend(["```", ""])
        return lines


class FlowchartGenerator(MermaidGenerator):
    """Generate Mermaid flowchart diagrams."""

    def generate(self, req: Requirement, lookup: RequirementLookup) -> list[str]:
        """Generate parent hierarchy flowchart section.

        Args:
            req: The current requirement object.
            lookup: RequirementLookup for data access.

        Returns:
            List of markdown lines for the flowchart section.
        """
        lines = ["", "## Parent Hierarchy Flowchart", "", "```mermaid", "graph TD"]

        # Get all ancestors and build nodes
        all_ancestors = lookup.get_all_ancestors(req.req_id)
        unique_ancestors = list(
            dict.fromkeys(all_ancestors)
        )  # Remove duplicates, preserve order
        all_nodes = [req.req_id, *unique_ancestors]

        # Add node definitions
        for node_id in all_nodes:
            node_desc = (
                lookup.get_description(node_id)
                if node_id != req.req_id
                else req.description
            )
            if node_desc:
                truncated = self.truncate_description(node_desc, max_words=7)
                sanitized = self.sanitize_text(f"{node_id}: {truncated}")
                style = ":::current" if node_id == req.req_id else ""
                lines.append(f"    {node_id}[{sanitized}]{style}")
            else:
                lines.append(f"    {node_id}[{self.sanitize_text(node_id)}]")

        # Add edges
        self._add_edges_recursive(req.req_id, lookup, lines, set())

        # Add styling
        lines.extend(
            [
                "    classDef current fill:#ff9800,stroke:#e65100,stroke-width:3px,"
                "color:#fff",
                "```",
            ]
        )

        return lines

    def _add_edges_recursive(
        self,
        child_id: str,
        lookup: RequirementLookup,
        lines: list[str],
        visited: set[str],
    ) -> None:
        """Add edges from child to parents recursively."""
        if child_id in visited:
            return

        visited.add(child_id)
        child_req = lookup.get_requirement(child_id)

        if child_req and child_req.requirement.parents:
            for parent_id in child_req.requirement.parents:
                lines.append(f"    {child_id} --> {parent_id}")
                self._add_edges_recursive(parent_id, lookup, lines, visited.copy())


class RequirementPageGenerator:
    """Generates markdown content for requirement pages."""

    def __init__(self, lookup: RequirementLookup):
        """Initialize page generator with lookup.

        Args:
            lookup: RequirementLookup instance for efficient data access.
        """
        self.lookup = lookup
        self.stats = CompletionStats(lookup)
        self.mindmap_gen = MindmapGenerator()
        self.flowchart_gen = FlowchartGenerator()
        self.lines: list[str] = []

    def generate(self, parsed_req: ParsedRequirement) -> str:
        """Generate complete requirement page content.

        Args:
            parsed_req: ParsedRequirement object with requirement and source file.

        Returns:
            Complete markdown content for the requirement page.
        """
        req = parsed_req.requirement

        self._add_header(req)
        self._add_status_indicators(req)
        self._add_description(req)

        children = self.lookup.get_children(req.req_id)
        if children:
            self._add_children_mindmap(req, children)

        if req.parents:
            self._add_parents_section(req)

        if children:
            self._add_children_section(children)

        self._add_source_link(str(parsed_req.source_file))

        if req.parents:
            self._add_parent_flowchart(req)

        return "\n".join(self.lines)

    def _add_header(self, req: Requirement) -> None:
        """Add requirement header."""
        self.lines.extend([f"# {req.req_id}", ""])

    def _add_status_indicators(self, req: Requirement) -> None:
        """Add critical status indicator if applicable."""
        if req.critical:
            self.lines.extend(["⚠️ **Critical requirement**", ""])

    def _add_description(self, req: Requirement) -> None:
        """Add requirement description and completion status."""
        self.lines.extend([req.description, ""])
        if req.completed:
            self.lines.extend(["✅ **Completed**", ""])

    def _add_children_mindmap(self, req: Requirement, children: list[str]) -> None:
        """Add children mindmap section."""
        mindmap_lines = self.mindmap_gen.generate(req, children, self.lookup)
        self.lines.extend(mindmap_lines)

    def _add_parents_section(self, req: Requirement) -> None:
        """Add parents section with completion statistics and links."""
        completed, total = self.stats.calculate_completion(req.parents)
        self.lines.extend([f"## Parents ({completed}/{total} completed)", ""])

        for parent_id in req.parents:
            parent_desc = self.lookup.get_description(parent_id)
            parent_category = (
                parent_id.rsplit("-", 1)[0] if "-" in parent_id else "OTHER"
            )

            if parent_desc:
                self.lines.append(
                    f"- [{parent_id}](../{parent_category}/{parent_id}.md) - "
                    f"{parent_desc}"
                )
            else:
                self.lines.append(
                    f"- [{parent_id}](../{parent_category}/{parent_id}.md)"
                )

        self.lines.append("")

    def _add_children_section(self, children: list[str]) -> None:
        """Add children section with completion statistics and links."""
        completed, total = self.stats.calculate_completion(children)
        self.lines.extend([f"## Children ({completed}/{total} completed)", ""])

        for child_id in children:
            child_desc = self.lookup.get_description(child_id)
            child_category = child_id.rsplit("-", 1)[0] if "-" in child_id else "OTHER"

            if child_desc:
                self.lines.append(
                    f"- [{child_id}](../{child_category}/{child_id}.md) - {child_desc}"
                )
            else:
                self.lines.append(f"- [{child_id}](../{child_category}/{child_id}.md)")

        self.lines.append("")

    def _add_source_link(self, source_file: str) -> None:
        """Add source file link."""
        self.lines.extend(["---", f"*Source: [{source_file}](../../{source_file})*"])

    def _add_parent_flowchart(self, req: Requirement) -> None:
        """Add parent hierarchy flowchart section."""
        flowchart_lines = self.flowchart_gen.generate(req, self.lookup)
        self.lines.extend(flowchart_lines)


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
    lookup = RequirementLookup(all_requirements)
    generator = RequirementPageGenerator(lookup)
    return generator.generate(parsed_req)


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
