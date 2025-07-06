"""Custom exceptions for ReqSnake."""

from mkdocs.exceptions import PluginError


class ReqSnakeError(PluginError):
    """Base exception for all ReqSnake errors."""

    pass


class ParseError(ReqSnakeError):
    """Raised when parsing requirements fails."""

    pass


class ValidationError(ReqSnakeError):
    """Raised when requirement validation fails."""

    pass


class DuplicateRequirementError(ValidationError):
    """Raised when duplicate requirement IDs are found."""

    pass


class CircularDependencyError(ValidationError):
    """Raised when circular dependencies are detected."""

    pass


class CompletionValidationError(ValidationError):
    """Raised when completed requirements have incomplete children."""

    pass


class InvalidRequirementIdError(ParseError):
    """Raised when a requirement ID doesn't match the required format."""

    pass


class UnknownAttributeError(ParseError):
    """Raised when an unknown attribute is found in a requirement."""

    pass
