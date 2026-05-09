"""
Lifecycle Framework Utilities - Transition validation and enforcement.

Implements the transition logic per Platform Core Status & Lifecycle Framework.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone

from .models import LifecycleStateDef, LifecycleTransitionRule, LifecycleTransitionAudit


class LifecycleError(Exception):
    """Base exception for lifecycle framework errors."""
    pass


class InvalidTransitionError(LifecycleError):
    """Raised when a transition is not allowed."""
    pass


class LockedStateError(LifecycleError):
    """Raised when trying to modify a locked state entity."""
    pass


class MissingStateDefinitionError(LifecycleError):
    """Raised when state definitions are not registered for an entity type."""
    pass


def get_default_state(entity_type):
    """
    Get the default initial state for an entity type.
    
    Args:
        entity_type: String identifier for entity type
    
    Returns:
        State name string
    
    Raises:
        MissingStateDefinitionError: If no states defined for entity type
    """
    try:
        state_def = LifecycleStateDef.objects.get(
            entity_type=entity_type,
            is_default=True,
            is_active=True
        )
        return state_def.state_name
    except LifecycleStateDef.DoesNotExist:
        raise MissingStateDefinitionError(
            f"No default state registered for entity type: {entity_type}"
        )


def is_state_locked(entity_type, state_name):
    """
    Check if a state is locked (prevents edits).
    
    Per specification: Locked and final states allow no edits.
    """
    try:
        state_def = LifecycleStateDef.objects.get(
            entity_type=entity_type,
            state_name=state_name,
            is_active=True
        )
        return state_def.state_type in ('locked', 'final')
    except LifecycleStateDef.DoesNotExist:
        return False


def is_state_final(entity_type, state_name):
    """Check if a state is final (no outgoing transitions)."""
    try:
        state_def = LifecycleStateDef.objects.get(
            entity_type=entity_type,
            state_name=state_name,
            is_active=True
        )
        return state_def.state_type == 'final'
    except LifecycleStateDef.DoesNotExist:
        return False


def get_allowed_transitions(entity_type, from_state):
    """
    Get list of allowed destination states from a given state.
    
    Args:
        entity_type: String identifier for entity type
        from_state: Current state name
    
    Returns:
        List of LifecycleTransitionRule objects
    """
    return LifecycleTransitionRule.objects.filter(
        entity_type=entity_type,
        from_state=from_state,
        is_active=True
    )


def can_transition(entity_type, from_state, to_state, user=None, required_permission=None):
    """
    Check if a transition is allowed.
    
    Per specification:
    - Transitions must be explicit (if not defined, denied)
    - Fail closed (default deny)
    - Final states have no outgoing transitions
    
    Args:
        entity_type: String identifier for entity type
        from_state: Current state
        to_state: Desired destination state
        user: User attempting transition (for permission checks)
        required_permission: Optional permission override for checking
    
    Returns:
        Boolean: True if transition is allowed
    """
    if from_state == to_state:
        return False  # Self-transitions not allowed
    
    if is_state_final(entity_type, from_state):
        return False  # Final states have no outgoing transitions
    
    # Check if transition rule exists
    try:
        rule = LifecycleTransitionRule.objects.get(
            entity_type=entity_type,
            from_state=from_state,
            to_state=to_state,
            is_active=True
        )
    except LifecycleTransitionRule.DoesNotExist:
        return False  # Transition not allowed
    
    # Check permission if required
    if rule.required_permission and user:
        if not user.has_perm(rule.required_permission):
            return False
    
    return True


def validate_transition(entity_type, from_state, to_state, reason=None, user=None):
    """
    Validate a transition and collect any errors.
    
    Args:
        entity_type: String identifier for entity type
        from_state: Current state
        to_state: Desired destination state
        reason: Optional reason text
        user: User attempting transition
    
    Returns:
        Tuple: (is_valid, error_message)
    """
    # Check if transition is allowed
    if not can_transition(entity_type, from_state, to_state, user):
        if is_state_final(entity_type, from_state):
            return False, f"Cannot transition from final state: {from_state}"
        return False, f"Transition not allowed: {from_state} → {to_state}"
    
    # Check if reason is required
    try:
        rule = LifecycleTransitionRule.objects.get(
            entity_type=entity_type,
            from_state=from_state,
            to_state=to_state,
            is_active=True
        )
        if rule.requires_reason and not reason:
            return False, "Reason is required for this transition"
    except LifecycleTransitionRule.DoesNotExist:
        return False, "Transition rule not found"
    
    return True, None


@transaction.atomic
def perform_transition(
    entity_type,
    entity_id,
    from_state,
    to_state,
    user,
    reason=None,
    is_override=False
):
    """
    Perform a lifecycle state transition with validation and auditing.
    
    Per specification:
    - Validates transition is allowed
    - Creates immutable audit entry
    - Atomic transaction
    
    Args:
        entity_type: String identifier for entity type
        entity_id: UUID of entity being transitioned
        from_state: Current state
        to_state: Desired destination state
        user: User performing transition
        reason: Optional reason text (required for some transitions)
        is_override: Whether this is an administrative override
    
    Returns:
        LifecycleTransitionAudit: The created audit entry
    
    Raises:
        InvalidTransitionError: If transition is not allowed
    """
    # Validate transition
    is_valid, error_msg = validate_transition(
        entity_type, from_state, to_state, reason, user
    )
    if not is_valid:
        raise InvalidTransitionError(error_msg)
    
    # Create audit entry
    audit_entry = LifecycleTransitionAudit.objects.create(
        user=user,
        entity_type=entity_type,
        entity_id=entity_id,
        from_state=from_state,
        to_state=to_state,
        reason=reason or '',
        is_override=is_override
    )
    
    return audit_entry


class LifecycleTransitionMixin:
    """
    Mixin for models to support lifecycle state transitions.
    
    Provides convenient methods for state management on LifecycleModel entities.
    
    Usage:
        class MyEntity(LifecycleModel, LifecycleTransitionMixin):
            entity_type = 'my_entity'
    """
    
    # Subclasses must define:
    # entity_type = 'your_entity_type'
    
    def perform_lifecycle_transition(self, to_state, user, reason=None, is_override=False):
        """
        Transition this entity to a new lifecycle state.
        
        Args:
            to_state: Destination state name
            user: User performing transition
            reason: Optional reason text
            is_override: Whether this is an override
        
        Raises:
            InvalidTransitionError: If transition not allowed
            LockedStateError: If in a locked state
        
        Returns:
            Updated self instance
        """
        # Check if currently locked
        if is_state_locked(self.entity_type, self.lifecycle_state):
            raise LockedStateError(
                f"Cannot modify entity in locked state: {self.lifecycle_state}"
            )
        
        # Perform transition
        audit_entry = perform_transition(
            entity_type=self.entity_type,
            entity_id=self.id,
            from_state=self.lifecycle_state,
            to_state=to_state,
            user=user,
            reason=reason,
            is_override=is_override
        )
        
        # Update this instance
        self.lifecycle_state = to_state
        self.lifecycle_changed_at = timezone.now()
        self.lifecycle_changed_by = user
        self.updated_by = user
        self.save()
        
        return self
    
    def get_allowed_transitions(self):
        """Get list of allowed destination states from current state."""
        return get_allowed_transitions(self.entity_type, self.lifecycle_state)
    
    def can_transition_to(self, to_state, user=None):
        """Check if transition to specific state is allowed."""
        return can_transition(
            self.entity_type,
            self.lifecycle_state,
            to_state,
            user=user
        )
    
    def is_locked(self):
        """Check if entity is in a locked state."""
        return is_state_locked(self.entity_type, self.lifecycle_state)
    
    def is_final(self):
        """Check if entity is in a final state."""
        return is_state_final(self.entity_type, self.lifecycle_state)
