"""
Tests for Lifecycle Framework - Status and Lifecycle Framework

Tests both programming logic and user/admin workflows.
"""

import pytest
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError

from .models import LifecycleStateDef, LifecycleTransitionRule, LifecycleTransitionAudit
from .utils import (
	get_default_state,
	is_state_locked,
	is_state_final,
	get_allowed_transitions,
	can_transition,
	validate_transition,
	perform_transition,
	InvalidTransitionError,
	MissingStateDefinitionError,
)


# ============================================================================
# PROGRAMMING TESTS - Lifecycle Framework logic
# ============================================================================


@pytest.mark.django_db
class TestLifecycleStateDefinitions:
	"""Test lifecycle state definition registration and validation."""
	
	def test_create_state_definition(self):
		"""Test creating a state definition."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		state = LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='draft',
			state_label='Draft',
			state_type='normal',
			is_default=True,
			created_by=admin,
			updated_by=admin
		)
		
		assert state.entity_type == 'order'
		assert state.state_name == 'draft'
		assert state.is_default is True
		assert state.state_type == 'normal'
	
	def test_get_default_state(self):
		"""Test retrieving default state for entity type."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		LifecycleStateDef.objects.create(
			entity_type='invoice',
			state_name='draft',
			state_label='Draft',
			is_default=True,
			created_by=admin,
			updated_by=admin
		)
		
		default = get_default_state('invoice')
		assert default == 'draft'
	
	def test_get_default_state_missing(self):
		"""Test error when no default state defined."""
		with pytest.raises(MissingStateDefinitionError):
			get_default_state('nonexistent_entity')
	
	def test_only_one_default_per_entity(self):
		"""Test that only one default state can exist per entity type."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		state1 = LifecycleStateDef.objects.create(
			entity_type='quote',
			state_name='draft',
			state_label='Draft',
			is_default=True,
			created_by=admin,
			updated_by=admin
		)
		
		state2 = LifecycleStateDef.objects.create(
			entity_type='quote',
			state_name='active',
			state_label='Active',
			is_default=True,
			created_by=admin,
			updated_by=admin
		)
		
		state1.refresh_from_db()
		assert state1.is_default is False  # First default should be deactivated
		assert state2.is_default is True
	
	def test_locked_state_detection(self):
		"""Test detecting locked states."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='locked_state',
			state_label='Locked',
			state_type='locked',
			created_by=admin,
			updated_by=admin
		)
		
		assert is_state_locked('order', 'locked_state') is True
		assert is_state_locked('order', 'normal_state') is False
	
	def test_final_state_detection(self):
		"""Test detecting final states."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='closed',
			state_label='Closed',
			state_type='final',
			created_by=admin,
			updated_by=admin
		)
		
		assert is_state_final('order', 'closed') is True
		assert is_state_final('order', 'draft') is False


@pytest.mark.django_db
class TestLifecycleTransitionRules:
	"""Test transition rule definition and enforcement."""
	
	def test_create_transition_rule(self):
		"""Test creating a transition rule."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		rule = LifecycleTransitionRule.objects.create(
			entity_type='order',
			from_state='draft',
			to_state='submitted',
			required_permission='can_submit_order',
			requires_reason=False,
			created_by=admin,
			updated_by=admin
		)
		
		assert rule.entity_type == 'order'
		assert rule.from_state == 'draft'
		assert rule.to_state == 'submitted'
		assert rule.required_permission == 'can_submit_order'
	
	def test_self_transition_not_allowed(self):
		"""Test that self-transitions are rejected."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		rule = LifecycleTransitionRule(
			entity_type='order',
			from_state='draft',
			to_state='draft',  # Same as from_state
			created_by=admin,
			updated_by=admin
		)
		
		with pytest.raises(ValidationError):
			rule.full_clean()
	
	def test_get_allowed_transitions(self):
		"""Test retrieving allowed transitions from a state."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		LifecycleTransitionRule.objects.create(
			entity_type='order',
			from_state='draft',
			to_state='submitted',
			created_by=admin,
			updated_by=admin
		)
		
		LifecycleTransitionRule.objects.create(
			entity_type='order',
			from_state='draft',
			to_state='cancelled',
			created_by=admin,
			updated_by=admin
		)
		
		transitions = get_allowed_transitions('order', 'draft')
		assert len(transitions) == 2
		to_states = [t.to_state for t in transitions]
		assert 'submitted' in to_states
		assert 'cancelled' in to_states


@pytest.mark.django_db
class TestLifecycleTransitionValidation:
	"""Test transition validation logic."""
	
	def setup_method(self):
		"""Set up test data."""
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		self.user = User.objects.create_user('user', 'user@test.com', 'pass')
		
		# Create state definitions
		LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='draft',
			state_label='Draft',
			is_default=True,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='submitted',
			state_label='Submitted',
			created_by=self.admin,
			updated_by=self.admin
		)
		
		LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='approved',
			state_label='Approved',
			created_by=self.admin,
			updated_by=self.admin
		)
		
		LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='closed',
			state_label='Closed',
			state_type='final',
			created_by=self.admin,
			updated_by=self.admin
		)
	
	def test_can_transition_allowed(self):
		"""Test checking allowed transition."""
		LifecycleTransitionRule.objects.create(
			entity_type='order',
			from_state='draft',
			to_state='submitted',
			created_by=self.admin,
			updated_by=self.admin
		)
		
		assert can_transition('order', 'draft', 'submitted') is True
	
	def test_can_transition_not_allowed(self):
		"""Test checking disallowed transition."""
		assert can_transition('order', 'draft', 'submitted') is False
	
	def test_can_transition_self_transition_denied(self):
		"""Test that self-transitions are denied."""
		assert can_transition('order', 'draft', 'draft') is False
	
	def test_can_transition_from_final_state(self):
		"""Test that transitions from final states are denied."""
		assert can_transition('order', 'closed', 'submitted') is False
	
	def test_validate_transition_success(self):
		"""Test successful transition validation."""
		LifecycleTransitionRule.objects.create(
			entity_type='order',
			from_state='draft',
			to_state='submitted',
			requires_reason=False,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		is_valid, error = validate_transition('order', 'draft', 'submitted')
		assert is_valid is True
		assert error is None
	
	def test_validate_transition_requires_reason(self):
		"""Test validation when reason is required."""
		LifecycleTransitionRule.objects.create(
			entity_type='order',
			from_state='draft',
			to_state='cancelled',
			requires_reason=True,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		# Without reason
		is_valid, error = validate_transition('order', 'draft', 'cancelled')
		assert is_valid is False
		assert 'reason' in error.lower()
		
		# With reason
		is_valid, error = validate_transition('order', 'draft', 'cancelled', reason='Not needed')
		assert is_valid is True
		assert error is None


@pytest.mark.django_db
class TestLifecycleTransitionExecution:
	"""Test performing transitions and audit logging."""
	
	def setup_method(self):
		"""Set up test data."""
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='draft',
			state_label='Draft',
			is_default=True,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='submitted',
			state_label='Submitted',
			created_by=self.admin,
			updated_by=self.admin
		)
	
	def test_perform_transition(self):
		"""Test performing a transition and creating audit entry."""
		LifecycleTransitionRule.objects.create(
			entity_type='order',
			from_state='draft',
			to_state='submitted',
			created_by=self.admin,
			updated_by=self.admin
		)
		
		entity_id = '12345678-1234-5678-1234-567812345678'
		
		audit = perform_transition(
			entity_type='order',
			entity_id=entity_id,
			from_state='draft',
			to_state='submitted',
			user=self.admin,
			reason='Customer request'
		)
		
		assert audit.entity_type == 'order'
		assert audit.entity_id == entity_id
		assert audit.from_state == 'draft'
		assert audit.to_state == 'submitted'
		assert audit.reason == 'Customer request'
		assert audit.user == self.admin
		assert audit.is_override is False
	
	def test_perform_invalid_transition_raises_error(self):
		"""Test that invalid transitions raise InvalidTransitionError."""
		entity_id = '12345678-1234-5678-1234-567812345678'
		
		with pytest.raises(InvalidTransitionError):
			perform_transition(
				entity_type='order',
				entity_id=entity_id,
				from_state='draft',
				to_state='submitted',
				user=self.admin
			)
	
	def test_audit_entry_immutable(self):
		"""Test that audit entries cannot be modified or deleted."""
		LifecycleTransitionRule.objects.create(
			entity_type='order',
			from_state='draft',
			to_state='submitted',
			created_by=self.admin,
			updated_by=self.admin
		)
		
		entity_id = '12345678-1234-5678-1234-567812345678'
		audit = perform_transition(
			entity_type='order',
			entity_id=entity_id,
			from_state='draft',
			to_state='submitted',
			user=self.admin
		)
		
		# Try to update
		audit.reason = 'Modified reason'
		with pytest.raises(ValidationError):
			audit.save()
		
		# Try to delete
		with pytest.raises(ValidationError):
			audit.delete()


# ============================================================================
# USER/ADMIN TESTS - Admin interface workflows
# ============================================================================


class TestAdminStateDefinitionWorkflows(TestCase):
	"""Test admin workflows for state definition management."""
	
	def setUp(self):
		"""Set up test data."""
		self.client = Client()
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
	
	def test_admin_login(self):
		"""Test admin can login."""
		success = self.client.login(username='admin', password='adminpass')
		assert success is True
	
	def test_admin_can_create_state_definition(self):
		"""Test admin can create state definition via form."""
		self.client.login(username='admin', password='adminpass')
		
		response = self.client.post(
			reverse('admin:lifecycle_lifecyclestatedef_add'),
			{
				'entity_type': 'order',
				'state_name': 'draft',
				'state_label': 'Draft',
				'state_type': 'normal',
				'is_default': True,
				'description': 'Initial order state',
				'is_active': True,
			},
			follow=True,
		)
		
		assert response.status_code == 200
		state = LifecycleStateDef.objects.get(state_name='draft')
		assert state.entity_type == 'order'
		assert state.state_label == 'Draft'
	
	def test_admin_state_definition_list(self):
		"""Test admin can view state definition list."""
		self.client.login(username='admin', password='adminpass')
		
		LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='draft',
			state_label='Draft',
			is_default=True,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		response = self.client.get(reverse('admin:lifecycle_lifecyclestatedef_changelist'))
		assert response.status_code == 200
		assert b'order' in response.content
		assert b'Draft' in response.content
	
	def test_admin_can_edit_state_definition(self):
		"""Test admin can edit state definition."""
		self.client.login(username='admin', password='adminpass')
		
		state = LifecycleStateDef.objects.create(
			entity_type='order',
			state_name='draft',
			state_label='Draft',
			is_default=True,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		response = self.client.post(
			reverse('admin:lifecycle_lifecyclestatedef_change', args=[state.id]),
			{
				'entity_type': 'order',
				'state_name': 'draft',
				'state_label': 'Draft Order',  # Changed
				'state_type': 'locked',  # Changed
				'is_default': True,
				'description': '',
				'is_active': True,
			},
			follow=True,
		)
		
		assert response.status_code == 200
		state.refresh_from_db()
		assert state.state_label == 'Draft Order'
		assert state.state_type == 'locked'


class TestAdminTransitionRuleWorkflows(TestCase):
	"""Test admin workflows for transition rule management."""
	
	def setUp(self):
		"""Set up test data."""
		self.client = Client()
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
	
	def test_admin_can_create_transition_rule(self):
		"""Test admin can create transition rule."""
		self.client.login(username='admin', password='adminpass')
		
		response = self.client.post(
			reverse('admin:lifecycle_lifecycletransitionrule_add'),
			{
				'entity_type': 'order',
				'from_state': 'draft',
				'to_state': 'submitted',
				'required_permission': 'can_submit',
				'requires_reason': False,
				'description': 'Submit order for processing',
				'is_active': True,
			},
			follow=True,
		)
		
		assert response.status_code == 200
		rule = LifecycleTransitionRule.objects.get(from_state='draft')
		assert rule.to_state == 'submitted'
		assert rule.required_permission == 'can_submit'
	
	def test_admin_transition_rule_list(self):
		"""Test admin can view transition rule list."""
		self.client.login(username='admin', password='adminpass')
		
		LifecycleTransitionRule.objects.create(
			entity_type='order',
			from_state='draft',
			to_state='submitted',
			created_by=self.admin,
			updated_by=self.admin
		)
		
		response = self.client.get(reverse('admin:lifecycle_lifecycletransitionrule_changelist'))
		assert response.status_code == 200
		assert b'draft' in response.content
		assert b'submitted' in response.content


class TestAdminTransitionAuditWorkflows(TestCase):
	"""Test admin workflows for transition audit viewing."""
	
	def setUp(self):
		"""Set up test data."""
		self.client = Client()
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
	
	def test_admin_can_view_transition_audit(self):
		"""Test admin can view transition audit log (read-only)."""
		self.client.login(username='admin', password='adminpass')
		
		LifecycleTransitionAudit.objects.create(
			user=self.admin,
			entity_type='order',
			entity_id='12345678-1234-5678-1234-567812345678',
			from_state='draft',
			to_state='submitted',
			reason='Test transition'
		)
		
		response = self.client.get(reverse('admin:lifecycle_lifecycletransitionaudit_changelist'))
		assert response.status_code == 200
		assert b'order' in response.content
	
	def test_admin_cannot_add_transition_audit(self):
		"""Test admin cannot directly add audit entries (immutable)."""
		self.client.login(username='admin', password='adminpass')
		
		response = self.client.get(reverse('admin:lifecycle_lifecycletransitionaudit_add'))
		# Should not have add permission
		assert response.status_code == 403
