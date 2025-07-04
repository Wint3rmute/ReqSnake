"""Data models for ReqSnake."""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class Requirement:
    """Represent a requirement parsed from a Markdown block-quote.

    Attributes:
        req_id: The unique identifier of the requirement.
        description: A short description of the requirement.
        critical: Whether the requirement is marked as critical.
        children: List of child requirement IDs.
        completed: Whether the requirement is completed.

    """

    req_id: str
    description: str
    critical: bool = False
    children: List[str] = field(default_factory=list)
    completed: bool = False

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Requirement":
        """Create a Requirement from a dictionary."""
        return Requirement(
            req_id=data["req_id"],
            description=data["description"],
            critical=data.get("critical", False),
            children=data.get("children", []),
            completed=data.get("completed", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert requirement to dictionary."""
        return {
            "req_id": self.req_id,
            "description": self.description,
            "critical": self.critical,
            "children": self.children,
            "completed": self.completed,
        }

    def to_pretty_string(self) -> str:
        """Return a human-readable, multi-line string representation of the requirement."""
        lines = [f"{self.req_id}: {self.description}\n\n"]
        if self.critical:
            lines.append("**⚠️ critical**\n\n")
        if self.completed:
            lines.append("✅ completed\n\n")
        if self.children:
            lines.append("### Children\n\n")
            for child in self.children:
                lines.append(f"- {child}\n")
        return "".join(lines)


@dataclass(frozen=True)
class ParsedRequirement:
    """A requirement and the path to the file it was parsed from."""

    requirement: Requirement
    source_file: Path


class DiffType(Enum):
    """Enum representing types of requirement diffs: added, removed, or changed."""

    ADDED = auto()
    REMOVED = auto()
    CHANGED = auto()

    def __str__(self) -> str:
        """Return the lowercase name of the DiffType enum member."""
        return self.name.lower()
