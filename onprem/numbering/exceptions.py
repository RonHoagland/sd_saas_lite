# numbering/exceptions.py
# Exception classes for the Numbering Service.
# Source: Numbering Service Specification V1


class NumberingError(Exception):
    """Base exception for all numbering service errors."""
    pass


class NoRuleDefinedError(NumberingError):
    """Raised when no numbering rule exists for the given entity type."""
    pass


class NumberingDisabledError(NumberingError):
    """Raised when a numbering rule is disabled."""
    pass


class DuplicateAssignmentError(NumberingError):
    """Raised when trying to assign a number to an entity that already has one."""
    pass


class SequenceError(NumberingError):
    """Raised when a sequence operation fails."""
    pass
