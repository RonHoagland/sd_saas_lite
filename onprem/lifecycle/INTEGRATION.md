# Lifecycle Framework - Integration Checklist

## Pre-Integration Verification

- [x] All 8 Python files created and syntactically valid
- [x] All models follow TenantModel patterns (except audit)
- [x] UUID PKs, tenant_id fields, audit fields inherited
- [x] Proper DB constraints and indexes
- [x] Admin classes registered with TenantModelAdmin
- [x] Comprehensive test suite with 18+ tests
- [x] Exception classes defined
- [x] Service functions implemented
- [x] Mixin class for easy integration
- [x] No circular import issues (lazy loading used)

## Integration Steps

### 1. Add to INSTALLED_APPS

In your Django settings.py:

```python
INSTALLED_APPS = [
    # ... other apps
    'lifecycle',
    # ... other apps
]
```

### 2. Run Migrations

```bash
python manage.py makemigrations lifecycle
python manage.py migrate
```

This will create three tables:
- lifecycle_lifecyclestatedef
- lifecycle_lifecycletransitionrule
- lifecycle_lifecycletransitionaudit

### 3. Create Initial States and Transitions (Optional)

Create a data migration or management command to seed initial states:

```python
# lifecycle/management/commands/init_lifecycle_states.py
from django.core.management.base import BaseCommand
from lifecycle.models import LifecycleStateDef, LifecycleTransitionRule

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create states for your entity types
        # See USAGE.md for examples
        pass
```

### 4. Update Your Models

Add LifecycleMixin to models that use state management:

```python
from lifecycle.mixins import LifecycleMixin

class Task(TenantModel, LifecycleMixin):
    lifecycle_entity_type = 'task'
    status = models.CharField(max_length=50, default='DRAFT')
    # ... other fields
```

### 5. Update Your Views/APIs

Replace direct status updates:

```python
# Before:
entity.status = 'APPROVED'
entity.save()

# After:
from lifecycle.services import execute_transition
audit = execute_transition(entity, 'APPROVED', user, reason='...')
```

### 6. Register Admin Interfaces

The admin interfaces are auto-registered via @admin.register decorators.
They will appear in Django admin under the "Lifecycle" section:

- State Definitions
- Transition Rules
- Transition Audit (read-only)

### 7. Run Tests

```bash
python manage.py test lifecycle.tests
```

Expected output:
- 18+ test methods
- All tests passing
- 100% coverage of critical paths

## Files Created

```
lifecycle/
├── __init__.py              (0 lines)
├── apps.py                  (7 lines)
├── exceptions.py            (28 lines)
├── models.py                (238 lines)
├── services.py              (250 lines)
├── mixins.py                (65 lines)
├── admin.py                 (96 lines)
├── tests.py                 (550 lines)
├── USAGE.md                 (Documentation)
└── INTEGRATION.md           (This file)
```

Total: 1,234 lines of production code + tests + docs

## Database Schema

### LifecycleStateDef
```sql
CREATE TABLE lifecycle_lifecyclestatedef (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    created_by VARCHAR(200),
    created_on TIMESTAMP,
    updated_by VARCHAR(200),
    updated_on TIMESTAMP,
    entity_type VARCHAR(50) NOT NULL,
    state_name VARCHAR(50) NOT NULL,
    state_label VARCHAR(100) NOT NULL,
    state_type VARCHAR(10) DEFAULT 'normal',
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    description TEXT,
    UNIQUE (tenant_id, entity_type, state_name),
    INDEX (tenant_id, entity_type),
    INDEX (tenant_id, entity_type, is_default)
);
```

### LifecycleTransitionRule
```sql
CREATE TABLE lifecycle_lifecycletransitionrule (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    created_by VARCHAR(200),
    created_on TIMESTAMP,
    updated_by VARCHAR(200),
    updated_on TIMESTAMP,
    entity_type VARCHAR(50) NOT NULL,
    from_state VARCHAR(50) NOT NULL,
    to_state VARCHAR(50) NOT NULL,
    required_role VARCHAR(100),
    requires_reason BOOLEAN DEFAULT FALSE,
    is_admin_override BOOLEAN DEFAULT FALSE,
    description TEXT,
    UNIQUE (tenant_id, entity_type, from_state, to_state),
    CHECK (from_state != to_state),
    INDEX (tenant_id, entity_type),
    INDEX (tenant_id, entity_type, from_state)
);
```

### LifecycleTransitionAudit
```sql
CREATE TABLE lifecycle_lifecycletransitionaudit (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    timestamp TIMESTAMP AUTO_NOW_ADD,
    user_id UUID NOT NULL,
    user_display VARCHAR(200),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    from_state VARCHAR(50) NOT NULL,
    to_state VARCHAR(50) NOT NULL,
    reason TEXT,
    is_override BOOLEAN DEFAULT FALSE,
    ip_address INET,
    INDEX (tenant_id, entity_type, entity_id),
    INDEX (tenant_id, entity_type),
    INDEX (tenant_id, timestamp),
    INDEX (user_id)
);
```

## Architecture Compliance

This implementation follows all existing patterns from service03:

- [x] TenantModel inheritance (except audit)
- [x] TenantManager auto-filtering
- [x] UUID PKs and tenant_id fields
- [x] Audit fields (created_by, created_on, updated_by, updated_on)
- [x] Proper db_table naming conventions
- [x] Unique constraints via models.UniqueConstraint
- [x] Check constraints via CheckConstraint
- [x] Comprehensive indexes
- [x] clean() validation in models
- [x] TenantModelAdmin for admin classes
- [x] SDTATestCase for test base
- [x] Lazy imports to avoid circular dependencies
- [x] Comprehensive docstrings and source references

## Performance Considerations

### Indexes Ensure Fast Queries

- State lookups: (tenant_id, entity_type)
- Transition rules: (tenant_id, entity_type, from_state)
- Audit queries: (tenant_id, entity_type, entity_id)
- User role checks: (tenant_id, employee, role)

### Audit Log Growth

LifecycleTransitionAudit grows with each transition. Consider:
- Archive old records monthly/yearly
- Use read replicas for audit queries
- Monitor table size

### Role Checking

Role lookups happen on every transition with a required_role:
- Cached by Django ORM if using default QuerySet caching
- Consider caching user roles in session for high-volume apps

## Troubleshooting

### Import Errors

If you get "ModuleNotFoundError: No module named 'lifecycle'":
- Ensure 'lifecycle' is in INSTALLED_APPS
- Ensure you've run `python manage.py migrate`

### Integrity Errors

If you get constraint violations:
- Ensure states are created before defining transitions
- Check that transition rules reference existing states
- Verify unique constraint compliance

### Permission Errors

If PermissionDeniedError is raised:
- Verify user has required EmployeeRole
- Check role__name matches required_role exactly
- Ensure you're in correct tenant context

## Next Steps

1. See USAGE.md for detailed usage examples
2. Review tests.py for comprehensive test patterns
3. Run the test suite: `python manage.py test lifecycle`
4. Create states and transitions for your entity types
5. Integrate LifecycleMixin into your models
6. Update views to use execute_transition()

## Support

For issues or questions:
- Review the Lifecycle Framework Specification V1
- Check tests.py for usage examples
- See USAGE.md for common patterns
- Review models.py for detailed docstrings
