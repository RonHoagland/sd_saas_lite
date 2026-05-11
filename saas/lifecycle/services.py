# lifecycle/services.py
# Business logic for state transitions in the Lifecycle Framework.
# Source: Lifecycle Framework Specification V1, Section 4.
#
# Core function: execute_transition()
# Helpers: get_available_transitions(), get_transition_history()

import uuid

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


# Stable sentinel UUID used as the audit `user_id` for system-initiated
# transitions (e.g. payment cascade auto-paying an invoice). Distinct from
# any real user UUID; safe to filter on in audit-log queries.
SYSTEM_USER_ID = uuid.UUID('00000000-0000-0000-0000-000000000000')
SYSTEM_USER_DISPLAY = 'System'


def execute_transition(entity, to_state, user, reason="", ip_address=None):
    """
    Execute a state transition on an entity.

    Steps:
    1. Read current state from entity.status
    2. Determine entity_type (from entity.lifecycle_entity_type or _meta.model_name)
    3. Get tenant_id from entity.tenant_id
    4. Look up LifecycleTransitionRule
    5. Validate role requirement (skipped in system mode)
    6. Validate reason requirement
    7. Update entity.status and save
    8. Create LifecycleTransitionAudit record
    9. Return audit record

    Args:
        entity: Model instance with status field and tenant_id
        to_state: Target state name (str)
        user: User instance performing transition, OR None for system mode.
              In system mode the role check is bypassed and the audit row
              is attributed to SYSTEM_USER_ID + 'System'. Reserved for
              cascades and background tasks (e.g. Payments.save() auto-
              transitioning an Invoice to Paid).
        reason: Optional transition reason/comment
        ip_address: Optional originating IP

    Returns:
        LifecycleTransitionAudit record

    Raises:
        TransitionDeniedError: If no rule exists for this transition
        PermissionDeniedError: If user lacks required role (only when user is not None)
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

    # 5. Validate role requirement (system mode bypasses).
    if rule.required_role and user is not None:
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

    # 7. Update and save entity. Entities may opt into a state-context sync
    # by defining `_apply_lifecycle_transition(from_state, to_state, reason, user)`
    # — used to keep denormalized fields (e.g., Customer.hold_reason) aligned
    # with the audit log. The hook is called *before* save() so all field
    # changes land in the same DB write as the status update.
    entity.status = to_state
    if hasattr(entity, '_apply_lifecycle_transition'):
        entity._apply_lifecycle_transition(
            from_state=current_state,
            to_state=to_state,
            reason=reason,
            user=user,
        )
    entity.save()

    # 8. Create audit record (system mode gets the sentinel user_id + 'System' display).
    if user is None:
        audit_user_id = SYSTEM_USER_ID
        audit_user_display = SYSTEM_USER_DISPLAY
    else:
        audit_user_id = user.id
        audit_user_display = getattr(user, 'email', str(user))

    audit = LifecycleTransitionAudit.objects.create(
        tenant_id=tenant_id,
        user_id=audit_user_id,
        user_display=audit_user_display,
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
    user_roles = set(_get_user_roles(user, tenant_id))
    if getattr(user, 'is_tenant_admin', False):
        user_roles.add('Tenant Administrator')

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

    The reserved role name ``Tenant Administrator`` matches users with
    ``is_tenant_admin=True`` (no ``EmployeeRole`` row required). Seeded
    lifecycle rules can use this for admin-only transitions.

    Args:
        user: User instance
        role_name: Name of role to check
        tenant_id: Tenant UUID

    Returns:
        bool: True if user has role, False otherwise
    """
    if role_name == 'Tenant Administrator':
        return bool(getattr(user, 'is_tenant_admin', False))
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
