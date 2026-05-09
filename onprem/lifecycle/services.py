# lifecycle/services.py
# Business logic for state transitions in the Lifecycle Framework.
# Source: Lifecycle Framework Specification V1, Section 4.
#
# Core function: execute_transition()
# Helpers: get_available_transitions(), get_transition_history()

from lifecycle.models import (
    LifecycleStateDef,
    LifecycleTransitionRule,
    LifecycleTransitionAudit
)
from lifecycle.exceptions import (
    TransitionDeniedError,
    PermissionDeniedError,
    ReasonRequiredError,
    FinalStateError,
)


def execute_transition(entity, to_state, user, reason="", ip_address=None):
    """
    Execute a state transition on an entity.

    Steps:
    1. Read current state from entity.status
    2. Determine entity_type (from entity.lifecycle_entity_type or _meta.model_name)
    3. Get tenant_id from entity.tenant_id
    4. Look up LifecycleTransitionRule
    5. Validate role requirement
    6. Validate reason requirement
    7. Update entity.status and save
    8. Create LifecycleTransitionAudit record
    9. Return audit record

    Args:
        entity: Model instance with status field and tenant_id
        to_state: Target state name (str)
        user: User instance performing transition
        reason: Optional transition reason/comment
        ip_address: Optional originating IP

    Returns:
        LifecycleTransitionAudit record

    Raises:
        TransitionDeniedError: If no rule exists for this transition
        PermissionDeniedError: If user lacks required role
        ReasonRequiredError: If transition requires reason but none given
        FinalStateError: If transition originates from final state without override
    """

    # 1. Read current state
    current_state = getattr(entity, 'status', None)
    if current_state is None:
        raise ValueError("Entity does not have a 'status' field.")

    # 2. Determine entity_type
    entity_type = getattr(entity, 'lifecycle_entity_type', None) or entity._meta.model_name

    # 3. Get tenant_id
    tenant_id = entity.tenant_id

    # 4. Look up transition rule
    try:
        rule = LifecycleTransitionRule.all_objects.get(
            tenant_id=tenant_id,
            entity_type=entity_type,
            from_state=current_state,
            to_state=to_state
        )
    except LifecycleTransitionRule.DoesNotExist:
        raise TransitionDeniedError(
            f"No transition rule exists for {entity_type}: "
            f"{current_state} → {to_state} in this tenant."
        )

    # 5. Validate role requirement
    if rule.required_role:
        has_role = _user_has_role(user, rule.required_role, tenant_id)
        if not has_role:
            raise PermissionDeniedError(
                f"User must have role '{rule.required_role}' to perform this transition."
            )

    # 6. Validate reason requirement
    if rule.requires_reason and not reason:
        raise ReasonRequiredError(
            f"Transition {entity_type}: {current_state} → {to_state} requires a reason."
        )

    # Check if from_state is final and no admin override
    try:
        from_state_def = LifecycleStateDef.all_objects.get(
            tenant_id=tenant_id,
            entity_type=entity_type,
            state_name=current_state
        )
    except LifecycleStateDef.DoesNotExist:
        raise TransitionDeniedError(
            f"Current state '{current_state}' is not defined in LifecycleStateDef "
            f"for entity_type '{entity_type}' in this tenant."
        )
    if (from_state_def.state_type == LifecycleStateDef.StateTypeChoices.FINAL
            and not rule.is_admin_override):
        raise FinalStateError(
            f"Cannot transition from final state '{current_state}' "
            f"without admin override."
        )

    # 7. Update and save entity
    entity.status = to_state
    entity.save()

    # 8. Create audit record
    audit = LifecycleTransitionAudit.objects.create(
        tenant_id=tenant_id,
        user_id=user.id,
        user_display=getattr(user, 'email', str(user)),
        entity_type=entity_type,
        entity_id=entity.id,
        from_state=current_state,
        to_state=to_state,
        reason=reason,
        is_override=rule.is_admin_override,
        ip_address=ip_address,
    )

    # 9. Return audit record
    return audit


def get_available_transitions(entity, user):
    """
    Get list of available transitions from entity's current state.

    For each rule matching (tenant_id, entity_type, from_state=current):
    - Filter by user's roles (if required_role is set)
    - Return dict with to_state, state_label, requires_reason, is_admin_override

    Args:
        entity: Model instance with status field and tenant_id
        user: User instance

    Returns:
        List of dicts: [{'to_state': '...', 'state_label': '...', ...}]
    """
    current_state = getattr(entity, 'status', None)
    if current_state is None:
        return []

    entity_type = getattr(entity, 'lifecycle_entity_type', None) or entity._meta.model_name
    tenant_id = entity.tenant_id

    # Get all rules for current state
    rules = LifecycleTransitionRule.all_objects.filter(
        tenant_id=tenant_id,
        entity_type=entity_type,
        from_state=current_state
    )

    transitions = []
    user_roles = _get_user_roles(user, tenant_id)

    for rule in rules:
        # If rule requires a role, check if user has it
        if rule.required_role and rule.required_role not in user_roles:
            continue

        # Get target state definition for label
        try:
            to_state_def = LifecycleStateDef.all_objects.get(
                tenant_id=tenant_id,
                entity_type=entity_type,
                state_name=rule.to_state
            )
            state_label = to_state_def.state_label
        except LifecycleStateDef.DoesNotExist:
            state_label = rule.to_state

        transitions.append({
            'to_state': rule.to_state,
            'state_label': state_label,
            'requires_reason': rule.requires_reason,
            'is_admin_override': rule.is_admin_override,
        })

    return transitions


def get_transition_history(entity_type, entity_id, tenant_id):
    """
    Get audit trail for an entity instance.

    Args:
        entity_type: Type string (e.g., 'task')
        entity_id: UUID of entity
        tenant_id: UUID of tenant

    Returns:
        QuerySet of LifecycleTransitionAudit, ordered by timestamp (earliest first)
    """
    return LifecycleTransitionAudit.objects.filter(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by('timestamp')


# ─── Helper functions ──────────────────────────────────────────────────────

def _user_has_role(user, role_name, tenant_id):
    """
    Check if user has a specific role in the tenant.
    Lazy import to avoid circular dependencies.

    Args:
        user: User instance
        role_name: Name of role to check
        tenant_id: Tenant UUID

    Returns:
        bool: True if user has role, False otherwise
    """
    try:
        from users.models import EmployeeRole
        return EmployeeRole.all_objects.filter(
            tenant_id=tenant_id,
            employee=user,
            role__name=role_name
        ).exists()
    except (ImportError, Exception):
        return False


def _get_user_roles(user, tenant_id):
    """
    Get all roles for a user in the tenant.
    Returns a set of role names.

    Args:
        user: User instance
        tenant_id: Tenant UUID

    Returns:
        set: Role names user holds in tenant
    """
    try:
        from users.models import EmployeeRole
        roles = EmployeeRole.all_objects.filter(
            tenant_id=tenant_id,
            employee=user
        ).values_list('role__name', flat=True)
        return set(roles)
    except (ImportError, Exception):
        return set()
