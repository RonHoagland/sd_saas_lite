# lifecycle/exceptions.py
# Custom exceptions for the Lifecycle Framework.
# Source: Lifecycle Framework Specification V1, Section 5.


class LifecycleError(Exception):
    """Base exception for all lifecycle-related errors."""
    pass


class TransitionDeniedError(LifecycleError):
    """Raised when a transition is not allowed (no rule exists)."""
    pass


class PermissionDeniedError(LifecycleError):
    """Raised when user lacks required role for transition."""
    pass


class ReasonRequiredError(LifecycleError):
    """Raised when a transition requires a reason but none was provided."""
    pass


class FinalStateError(LifecycleError):
    """Raised when attempting to transition from a final state without admin override."""
    pass
