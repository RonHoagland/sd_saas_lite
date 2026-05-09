# lifecycle/tests.py
# Comprehensive tests for Lifecycle Framework models and services.
# Source: Lifecycle Framework Specification V1, Sections 1–4.

import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models import Q

from tests.base import SDTATestCase
from lifecycle.models import (
    LifecycleStateDef,
    LifecycleTransitionRule,
    LifecycleTransitionAudit
)
from lifecycle.services import (
    execute_transition,
    get_available_transitions,
    get_transition_history
)
from lifecycle.exceptions import (
    TransitionDeniedError,
    PermissionDeniedError,
    ReasonRequiredError,
    FinalStateError,
)
from users.models import User, Role, EmployeeRole
from crm.models import Person


class LifecycleStateDefTest(SDTATestCase):
    """Tests for LifecycleStateDef model."""

    def test_create_state_def(self):
        """Test creating a state definition."""
        state = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='task',
            state_name='ACTIVE',
            state_label='Active',
            state_type=LifecycleStateDef.StateTypeChoices.NORMAL,
        )
        self.assertEqual(state.entity_type, 'task')
        self.assertEqual(state.state_name, 'ACTIVE')
        self.assertEqual(state.state_label, 'Active')

    def test_unique_constraint_state_per_entity(self):
        """Test UNIQUE (tenant_id, entity_type, state_name)."""
        LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='task',
            state_name='ACTIVE',
            state_label='Active',
        )
        with self.assertRaises(Exception):  # IntegrityError
            LifecycleStateDef.objects.create(
                tenant_id=self.tenant_id,
                entity_type='task',
                state_name='ACTIVE',
                state_label='Active (duplicate)',
            )

    def test_is_default_enforcement(self):
        """Test that only one state is default per (tenant_id, entity_type)."""
        # Create first state as default
        state1 = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='task',
            state_name='DRAFT',
            state_label='Draft',
            is_default=True,
        )
        self.assertTrue(state1.is_default)

        # Create second state as default
        state2 = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='task',
            state_name='ACTIVE',
            state_label='Active',
            is_default=True,
        )

        # Reload state1 — should no longer be default
        state1.refresh_from_db()
        self.assertFalse(state1.is_default)
        self.assertTrue(state2.is_default)

    def test_is_default_no_enforcement_across_entity_types(self):
        """Test that is_default is enforced PER entity_type."""
        state1 = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='task',
            state_name='ACTIVE',
            state_label='Active',
            is_default=True,
        )
        # Different entity_type — should be allowed to have its own default
        state2 = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='workorder',
            state_name='ACTIVE',
            state_label='Active',
            is_default=True,
        )
        state1.refresh_from_db()
        self.assertTrue(state1.is_default)
        self.assertTrue(state2.is_default)


class LifecycleTransitionRuleTest(SDTATestCase):
    """Tests for LifecycleTransitionRule model."""

    def setUp(self):
        super().setUp()
        # Create state definitions
        self.draft = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='task',
            state_name='DRAFT',
            state_label='Draft',
        )
        self.active = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='task',
            state_name='ACTIVE',
            state_label='Active',
        )
        self.completed = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='task',
            state_name='COMPLETED',
            state_label='Completed',
            state_type=LifecycleStateDef.StateTypeChoices.FINAL,
        )

    def test_create_transition_rule(self):
        """Test creating a transition rule."""
        rule = LifecycleTransitionRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='task',
            from_state='DRAFT',
            to_state='ACTIVE',
        )
        self.assertEqual(rule.from_state, 'DRAFT')
        self.assertEqual(rule.to_state, 'ACTIVE')

    def test_unique_constraint_transition_per_entity(self):
        """Test UNIQUE (tenant_id, entity_type, from_state, to_state)."""
        LifecycleTransitionRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='task',
            from_state='DRAFT',
            to_state='ACTIVE',
        )
        with self.assertRaises(Exception):  # IntegrityError
            LifecycleTransitionRule.objects.create(
                tenant_id=self.tenant_id,
                entity_type='task',
                from_state='DRAFT',
                to_state='ACTIVE',
            )

    def test_check_constraint_from_ne_to(self):
        """Test CHECK (from_state != to_state)."""
        with self.assertRaises(Exception):  # IntegrityError
            LifecycleTransitionRule.objects.create(
                tenant_id=self.tenant_id,
                entity_type='task',
                from_state='DRAFT',
                to_state='DRAFT',
            )

    def test_clean_from_state_must_exist(self):
        """Test clean() validates from_state exists."""
        rule = LifecycleTransitionRule(
            tenant_id=self.tenant_id,
            entity_type='task',
            from_state='NONEXISTENT',
            to_state='ACTIVE',
        )
        with self.assertRaises(ValidationError):
            rule.clean()

    def test_clean_to_state_must_exist(self):
        """Test clean() validates to_state exists."""
        rule = LifecycleTransitionRule(
            tenant_id=self.tenant_id,
            entity_type='task',
            from_state='DRAFT',
            to_state='NONEXISTENT',
        )
        with self.assertRaises(ValidationError):
            rule.clean()

    def test_clean_final_state_blocks_transition(self):
        """Test clean() blocks transitions from final states (no override)."""
        rule = LifecycleTransitionRule(
            tenant_id=self.tenant_id,
            entity_type='task',
            from_state='COMPLETED',
            to_state='ACTIVE',
            is_admin_override=False,
        )
        with self.assertRaises(ValidationError):
            rule.clean()

    def test_clean_final_state_allowed_with_override(self):
        """Test clean() allows final state transitions with admin_override."""
        rule = LifecycleTransitionRule(
            tenant_id=self.tenant_id,
            entity_type='task',
            from_state='COMPLETED',
            to_state='ACTIVE',
            is_admin_override=True,
        )
        # Should not raise
        rule.full_clean()
        rule.save()
        self.assertTrue(rule.is_admin_override)


class ExecuteTransitionTest(SDTATestCase):
    """Tests for execute_transition service function."""

    def setUp(self):
        super().setUp()
        # Create state definitions
        self.draft = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            state_name='Not Started',
            state_label='Not Started',
        )
        self.active = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            state_name='In Progress',
            state_label='In Progress',
        )
        self.approved = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            state_name='Completed',
            state_label='Completed',
        )

        # Create transition rule
        self.rule = LifecycleTransitionRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            from_state='Not Started',
            to_state='In Progress',
        )

        self.user = self.make_user(email=f'exec-{uuid.uuid4().hex[:10]}@example.com')

    def test_execute_transition_happy_path(self):
        """Test successful transition execution."""
        # Create a mock entity with status field
        from tasks.models import Task
        entity = Task.objects.create(
            title='Test Task',
            status='Not Started',
        )
        # Override lifecycle_entity_type
        entity.lifecycle_entity_type = 'test_task'

        # Execute transition
        audit = execute_transition(entity, 'In Progress', self.user, reason='Looks good')

        # Verify entity was updated
        entity.refresh_from_db()
        self.assertEqual(entity.status, 'In Progress')

        # Verify audit record was created
        self.assertIsNotNone(audit)
        self.assertEqual(audit.from_state, 'Not Started')
        self.assertEqual(audit.to_state, 'In Progress')
        self.assertEqual(audit.reason, 'Looks good')

    def test_execute_transition_deny_by_default(self):
        """Test TransitionDeniedError when no rule exists."""
        from tasks.models import Task
        entity = Task.objects.create(
            title='Test Task',
            status='In Progress',
        )
        entity.lifecycle_entity_type = 'test_task'

        with self.assertRaises(TransitionDeniedError):
            execute_transition(entity, 'Completed', self.user)

    def test_execute_transition_role_requirement(self):
        """Test PermissionDeniedError when user lacks required role."""
        # Create a role and a rule requiring it
        role = Role.objects.create(
            tenant_id=self.tenant_id,
            name='Approver',
        )
        rule = LifecycleTransitionRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            from_state='In Progress',
            to_state='Completed',
            required_role='Approver',
        )

        from tasks.models import Task
        entity = Task.objects.create(
            title='Test Task',
            status='In Progress',
        )
        entity.lifecycle_entity_type = 'test_task'

        # User doesn't have the Approver role
        with self.assertRaises(PermissionDeniedError):
            execute_transition(entity, 'Completed', self.user)

    def test_execute_transition_role_requirement_granted(self):
        """Test successful transition with role requirement met."""
        role = Role.objects.create(
            tenant_id=self.tenant_id,
            name='Approver',
        )
        rule = LifecycleTransitionRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            from_state='In Progress',
            to_state='Completed',
            required_role='Approver',
        )
        # Grant user the role
        EmployeeRole.objects.create(
            tenant_id=self.tenant_id,
            employee=self.user,
            role=role,
        )

        from tasks.models import Task
        entity = Task.objects.create(
            title='Test Task',
            status='In Progress',
        )
        entity.lifecycle_entity_type = 'test_task'

        # Should succeed now
        audit = execute_transition(entity, 'Completed', self.user)
        self.assertIsNotNone(audit)
        entity.refresh_from_db()
        self.assertEqual(entity.status, 'Completed')

    def test_execute_transition_reason_requirement(self):
        """Test ReasonRequiredError when reason is required but missing."""
        rule = LifecycleTransitionRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            from_state='In Progress',
            to_state='Completed',
            requires_reason=True,
        )

        from tasks.models import Task
        entity = Task.objects.create(
            title='Test Task',
            status='In Progress',
        )
        entity.lifecycle_entity_type = 'test_task'

        # Without reason
        with self.assertRaises(ReasonRequiredError):
            execute_transition(entity, 'Completed', self.user)

        # With reason
        audit = execute_transition(entity, 'Completed', self.user, reason='Good to go')
        self.assertEqual(audit.reason, 'Good to go')

    def test_execute_transition_final_state_blocks(self):
        """Test FinalStateError when transitioning from final state without override."""
        final = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            state_name='Cancelled',
            state_label='Cancelled',
            state_type=LifecycleStateDef.StateTypeChoices.FINAL,
        )
        # Transition FROM final state. Create with override=True first so model validation
        # allows persistence, then flip to False at DB layer to exercise service behavior.
        rule = LifecycleTransitionRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            from_state='Cancelled',
            to_state='Not Started',
            is_admin_override=True,
        )
        LifecycleTransitionRule.all_objects.filter(pk=rule.pk).update(is_admin_override=False)

        from tasks.models import Task
        entity = Task.objects.create(
            title='Test Task',
            status='Cancelled',
        )
        entity.lifecycle_entity_type = 'test_task'

        with self.assertRaises(FinalStateError):
            execute_transition(entity, 'Not Started', self.user)


class LifecycleTransitionAuditTest(SDTATestCase):
    """Tests for LifecycleTransitionAudit immutability."""

    def setUp(self):
        super().setUp()
        self.user = self.make_user(email=f'audit-{uuid.uuid4().hex[:10]}@example.com')

    def test_audit_record_immutable_save(self):
        """Test that audit records cannot be modified (save raises)."""
        audit = LifecycleTransitionAudit.objects.create(
            tenant_id=self.tenant_id,
            user_id=self.user.id,
            user_display=self.user.email,
            entity_type='task',
            entity_id=uuid.uuid4(),
            from_state='DRAFT',
            to_state='ACTIVE',
        )

        # Try to modify and save
        audit.reason = 'Modified after creation'
        with self.assertRaises(ValidationError):
            audit.save()

    def test_audit_record_immutable_delete(self):
        """Test that audit records cannot be deleted."""
        audit = LifecycleTransitionAudit.objects.create(
            tenant_id=self.tenant_id,
            user_id=self.user.id,
            user_display=self.user.email,
            entity_type='task',
            entity_id=uuid.uuid4(),
            from_state='DRAFT',
            to_state='ACTIVE',
        )

        with self.assertRaises(ValidationError):
            audit.delete()

    def test_audit_default_permissions_empty(self):
        """Test that audit model has no default Django admin permissions."""
        self.assertEqual(LifecycleTransitionAudit._meta.default_permissions, ())


class GetAvailableTransitionsTest(SDTATestCase):
    """Tests for get_available_transitions service."""

    def setUp(self):
        super().setUp()
        # Create state definitions
        self.draft = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            state_name='Not Started',
            state_label='Not Started',
        )
        self.active = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            state_name='In Progress',
            state_label='In Progress',
        )
        self.approved = LifecycleStateDef.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            state_name='Completed',
            state_label='Completed',
        )

        # Create transition rules
        LifecycleTransitionRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            from_state='Not Started',
            to_state='In Progress',
        )
        LifecycleTransitionRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='test_task',
            from_state='In Progress',
            to_state='Completed',
            required_role='Approver',
        )

        self.user = self.make_user(email=f'avail-{uuid.uuid4().hex[:10]}@example.com')

    def test_get_available_transitions(self):
        """Test retrieving available transitions."""
        from tasks.models import Task
        entity = Task.objects.create(
            title='Test Task',
            status='Not Started',
        )
        entity.lifecycle_entity_type = 'test_task'

        transitions = get_available_transitions(entity, self.user)

        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]['to_state'], 'In Progress')
        self.assertEqual(transitions[0]['state_label'], 'In Progress')

    def test_get_available_transitions_filtered_by_role(self):
        """Test that transitions requiring missing roles are filtered."""
        from tasks.models import Task
        entity = Task.objects.create(
            title='Test Task',
            status='In Progress',
        )
        entity.lifecycle_entity_type = 'test_task'

        transitions = get_available_transitions(entity, self.user)

        # User lacks 'Approver' role, so no transitions available
        self.assertEqual(len(transitions), 0)


class GetTransitionHistoryTest(SDTATestCase):
    """Tests for get_transition_history service."""

    def setUp(self):
        super().setUp()
        self.user = self.make_user(email=f'hist-{uuid.uuid4().hex[:10]}@example.com')
        self.entity_id = uuid.uuid4()

    def test_get_transition_history(self):
        """Test retrieving transition history."""
        # Create audit records
        LifecycleTransitionAudit.objects.create(
            tenant_id=self.tenant_id,
            user_id=self.user.id,
            user_display=self.user.email,
            entity_type='task',
            entity_id=self.entity_id,
            from_state='DRAFT',
            to_state='ACTIVE',
        )
        LifecycleTransitionAudit.objects.create(
            tenant_id=self.tenant_id,
            user_id=self.user.id,
            user_display=self.user.email,
            entity_type='task',
            entity_id=self.entity_id,
            from_state='ACTIVE',
            to_state='COMPLETED',
        )

        history = get_transition_history('task', self.entity_id, self.tenant_id)

        self.assertEqual(history.count(), 2)
        # Verify ordering (earliest first)
        first = history[0]
        second = history[1]
        self.assertEqual(first.from_state, 'DRAFT')
        self.assertEqual(second.from_state, 'ACTIVE')
