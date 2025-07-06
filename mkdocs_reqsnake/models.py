"""Data models for ReqSnake."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Requirement:
    """
    Represent a requirement parsed from a Markdown block-quote.

    Attributes:
        req_id: The unique identifier of the requirement.
        description: A short description of the requirement.
        critical: Whether the requirement is marked as critical.
        parents: List of parent requirement IDs (from child-of lines).
        completed: Whether the requirement is completed.

    """

    req_id: str
    description: str
    critical: bool = False
    parents: list[str] = field(default_factory=list)
    completed: bool = False

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Requirement":
        """Create a Requirement from a dictionary.

        Args:
            data: Dictionary containing requirement data.

        Returns:
            A new Requirement instance.
        """
        return Requirement(
            req_id=data["req_id"],
            description=data["description"],
            critical=data.get("critical", False),
            parents=data.get(
                "parents", data.get("children", [])
            ),  # Support both old and new field names
            completed=data.get("completed", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert requirement to dictionary.

        Returns:
            Dictionary representation of the requirement.
        """
        return {
            "req_id": self.req_id,
            "description": self.description,
            "critical": self.critical,
            "parents": self.parents,
            "completed": self.completed,
        }

    @property
    def category(self) -> str:
        """Extract category from requirement ID (everything before the last dash).

        Returns:
            The requirement category (e.g., 'REQ-CORE' from 'REQ-CORE-1') or 'OTHER'.
        """
        return self.req_id.rsplit("-", 1)[0] if "-" in self.req_id else "OTHER"

    def to_pretty_string(self) -> str:
        """Return a human-readable, multi-line string representation."""
        lines = [f"{self.req_id}: {self.description}\n\n"]
        if self.critical:
            lines.append("**⚠️ critical**\n\n")
        if self.completed:
            lines.append("✅ completed\n\n")
        if self.parents:
            lines.append("### Parents\n\n")
            for parent in self.parents:
                lines.append(f"- {parent}\n")
        return "".join(lines)


@dataclass(frozen=True)
class ParsedRequirement:
    """A requirement and the path to the file it was parsed from."""

    requirement: Requirement
    source_file: Path
