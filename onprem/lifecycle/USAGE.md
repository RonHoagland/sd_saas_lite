# Lifecycle Framework - Usage Guide

## Overview

The Lifecycle Framework provides state management for any Django model. It enforces valid state transitions, tracks changes via an immutable audit log, and supports role-based access control.

## Quick Start

### 1. Define States

```python
from lifecycle.models import LifecycleStateDef

# In your code or data migrations:
LifecycleStateDef.objects.create(
    entity_type='task',
    state_name='DRAFT',
    state_label='Draft',
    state_type=LifecycleStateDef.StateTypeChoices.NORMAL,
    is_default=True,
    sort_order=1,
)

LifecycleStateDef.objects.create(
    entity_type='task',
    state_name='ACTIVE',
    state_label='Active',
    sort_order=2,
)

LifecycleStateDef.objects.create(
    entity_type='task',
    state_name='COMPLETED',
    state_label='Completed',
    state_type=LifecycleStateDef.StateTypeChoices.FINAL,
    sort_order=3,
)
```

### 2. Define Transitions

```python
from lifecycle.models import LifecycleTransitionRule

# Allow transition from DRAFT to ACTIVE
LifecycleTransitionRule.objects.create(
    entity_type='task',
    from_state='DRAFT',
    to_state='ACTIVE',
)

# Require approval role to transition to COMPLETED
LifecycleTransitionRule.objects.create(
    entity_type='task',
    from_state='ACTIVE',
    to_state='COMPLETED',
    required_role='Approver',
    requires_reason=True,  # Must provide a reason
)
```

### 3. Add LifecycleMixin to Your Model

```python
from django.db import models
from config.base_models import TenantModel
from lifecycle.mixins import LifecycleMixin

class Task(TenantModel, LifecycleMixin):
    lifecycle_entity_type = 'task'  # Must match entity_type in states
    
    title = models.CharField(max_length=300)
    status = models.CharField(
        max_length=50,
        default='DRAFT'  # Match default state from LifecycleStateDef
    )
    # ... other fields
```

### 4. Execute Transitions

```python
from lifecycle.services import execute_transition

task = Task.objects.get(pk=task_id)
user = request.user

# Simple transition
try:
    audit = task.execute_transition('ACTIVE', user)
    print(f"Transitioned to {audit.to_state}")
except TransitionDeniedError:
    print("This transition is not allowed")
except PermissionDeniedError:
    print("You don't have permission for this transition")
except ReasonRequiredError:
    print("You must provide a reason for this transition")
```

### 5. Check Available Transitions

```python
# Get transitions available to user
available = task.get_available_transitions(user)
for transition in available:
    print(f"{transition['to_state']} ({transition['state_label']})")
    if transition['requires_reason']:
        print("  → Requires reason")
```

### 6. View Transition History

```python
# Get audit trail
history = task.get_transition_history()
for audit in history:
    print(f"{audit.timestamp}: {audit.from_state} → {audit.to_state}")
    print(f"  By: {audit.user_display}")
    if audit.reason:
        print(f"  Reason: {audit.reason}")
```

## Advanced Usage

### Role-Based Transitions

```python
from users.models import Role, EmployeeRole

# Create a role
approver_role = Role.objects.create(
    tenant_id=tenant_id,
    name='Approver'
)

# Assign to user
EmployeeRole.objects.create(
    tenant_id=tenant_id,
    employee=user,
    role=approver_role
)

# Define rule requiring role
LifecycleTransitionRule.objects.create(
    entity_type='task',
    from_state='PENDING_APPROVAL',
    to_state='APPROVED',
    required_role='Approver',
)
```

### Admin Override (Final States)

```python
# Allow admin to revert from final state
LifecycleTransitionRule.objects.create(
    entity_type='task',
    from_state='COMPLETED',
    to_state='ACTIVE',
    is_admin_override=True,
    required_role='Admin',
)
```

### IP Address Tracking

```python
# Capture IP address in the audit trail
audit = execute_transition(
    entity=task,
    to_state='ACTIVE',
    user=user,
    ip_address=request.META.get('REMOTE_ADDR')
)
```

## Error Handling

```python
from lifecycle.exceptions import (
    TransitionDeniedError,
    PermissionDeniedError,
    ReasonRequiredError,
    FinalStateError,
)

try:
    audit = task.execute_transition('NEW_STATE', user, reason='...')
except TransitionDeniedError as e:
    # No rule exists for this transition
    return JsonResponse({'error': str(e)}, status=400)
except PermissionDeniedError as e:
    # User lacks required role
    return JsonResponse({'error': str(e)}, status=403)
except ReasonRequiredError as e:
    # Transition requires a reason
    return JsonResponse({'error': str(e)}, status=400)
except FinalStateError as e:
    # Can't leave final state without override
    return JsonResponse({'error': str(e)}, status=400)
```

## Django Admin

The framework includes three admin interfaces:

1. **LifecycleStateDefAdmin**: Manage state definitions
   - Filter by entity_type and state_type
   - Set default states
   - Order states with sort_order

2. **LifecycleTransitionRuleAdmin**: Manage transition rules
   - View "from → to" transitions
   - Configure role requirements
   - Set reason requirements

3. **LifecycleTransitionAuditAdmin**: View-only audit log
   - Read-only access to all transitions
   - Cannot be modified or deleted
   - Filtered by entity_type, timestamp, user

## Design Principles

### Immutable Audit Log

LifecycleTransitionAudit records are write-once and read-only. They preserve:
- tenant_id (even if tenant is deleted)
- user_id and user_display (snapshot of email at time)
- Exact state transition details
- Optional reason and IP address

### Deny-by-Default Transitions

No transitions are allowed unless explicitly defined in LifecycleTransitionRule. This ensures:
- Explicit control over state machines
- Prevents accidental invalid states
- Forces design review of transitions

### Role-Based Access Control

Transitions can require specific roles (e.g., "Approver"). If a rule requires a role:
- User must have that role in the same tenant
- Checked via EmployeeRole relationship
- Returns PermissionDeniedError if missing

### Final States

States marked as StateTypeChoices.FINAL cannot be exited unless:
- A rule explicitly allows it with is_admin_override=True
- Typically paired with a required_role to restrict usage

## Testing

Use SDTATestCase from tests.base:

```python
from tests.base import SDTATestCase
from lifecycle.models import LifecycleStateDef, LifecycleTransitionRule
from lifecycle.services import execute_transition

class MyLifecycleTest(SDTATestCase):
    def setUp(self):
        super().setUp()
        # Create states and rules
        LifecycleStateDef.objects.create(...)
        LifecycleTransitionRule.objects.create(...)
    
    def test_my_transition(self):
        user = self.make_user()  # From base class
        entity = self.make_my_entity()
        
        audit = execute_transition(entity, 'NEW_STATE', user)
        self.assertEqual(audit.to_state, 'NEW_STATE')
```

## See Also

- lifecycle/models.py - Model definitions and constraints
- lifecycle/services.py - Core business logic
- lifecycle/exceptions.py - Exception types
- lifecycle/tests.py - Comprehensive test suite
