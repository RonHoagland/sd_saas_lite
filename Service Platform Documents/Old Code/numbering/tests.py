"""
Tests for Numbering and Identity Services.

Tests both programming logic and user/admin workflows.
"""

import pytest
import uuid
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import NumberingRule, NumberSequence, AssignedNumber
from .utils import (
	generate_number,
	assign_number,
	get_assigned_number,
	has_assigned_number,
	get_next_sequence_value,
	format_number,
	check_reset_needed,
	NumberingError,
	NoRuleDefinedError,
	NumberingDisabledError,
	DuplicateNumberError,
)


# ============================================================================
# PROGRAMMING TESTS - Numbering logic
# ============================================================================


@pytest.mark.django_db
class TestNumberingRuleCreation:
	"""Test creating and configuring numbering rules."""
	
	def test_create_basic_rule(self):
		"""Test creating basic numbering rule."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		rule = NumberingRule.objects.create(
			entity_type='invoice',
			is_enabled=True,
			prefix='INV',
			include_year=True,
			include_month=False,
			sequence_length=6,
			delimiter='-',
			created_by=admin,
			updated_by=admin
		)
		
		assert rule.entity_type == 'invoice'
		assert rule.prefix == 'INV'
		assert rule.is_enabled is True
		assert rule.sequence_length == 6
	
	def test_rule_with_yearly_reset(self):
		"""Test rule configured with yearly reset."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		rule = NumberingRule.objects.create(
			entity_type='invoice',
			prefix='INV',
			include_year=True,
			reset_behavior='yearly',
			created_by=admin,
			updated_by=admin
		)
		
		assert rule.reset_behavior == 'yearly'
	
	def test_rule_with_monthly_reset(self):
		"""Test rule configured with monthly reset."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		rule = NumberingRule.objects.create(
			entity_type='workorder',
			prefix='WO',
			include_year=True,
			include_month=True,
			reset_behavior='monthly',
			created_by=admin,
			updated_by=admin
		)
		
		assert rule.reset_behavior == 'monthly'
		assert rule.include_month is True
	
	def test_entity_type_unique(self):
		"""Test that entity_type is unique per rule."""
		admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		
		NumberingRule.objects.create(
			entity_type='invoice',
			created_by=admin,
			updated_by=admin
		)
		
		with pytest.raises(Exception):  # IntegrityError
			NumberingRule.objects.create(
				entity_type='invoice',  # Duplicate
				created_by=admin,
				updated_by=admin
			)


@pytest.mark.django_db
class TestNumberFormatting:
	"""Test number formatting with various configurations."""
	
	def setup_method(self):
		"""Set up test rules."""
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
	
	def test_format_prefix_only(self):
		"""Test formatting with just prefix."""
		rule = NumberingRule.objects.create(
			entity_type='client',
			prefix='CLIENT',
			sequence_length=5,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		number = format_number(rule, 42)
		assert number == 'CLIENT-00042'
	
	def test_format_with_year(self):
		"""Test formatting with year component."""
		rule = NumberingRule.objects.create(
			entity_type='invoice',
			prefix='INV',
			include_year=True,
			sequence_length=6,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		number = format_number(rule, 123)
		year = timezone.now().year
		assert number == f'INV-{year}-000123'
	
	def test_format_with_year_and_month(self):
		"""Test formatting with year and month."""
		rule = NumberingRule.objects.create(
			entity_type='workorder',
			prefix='WO',
			include_year=True,
			include_month=True,
			sequence_length=4,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		number = format_number(rule, 10)
		year = timezone.now().year
		month = str(timezone.now().month).zfill(2)
		assert number == f'WO-{year}-{month}-0010'
	
	def test_format_custom_delimiter(self):
		"""Test custom delimiter between components."""
		rule = NumberingRule.objects.create(
			entity_type='invoice',
			prefix='INV',
			include_year=True,
			sequence_length=5,
			delimiter='/',
			created_by=self.admin,
			updated_by=self.admin
		)
		
		number = format_number(rule, 99)
		year = timezone.now().year
		assert number == f'INV/{year}/00099'


@pytest.mark.django_db
class TestSequenceGeneration:
	"""Test atomic sequence generation and collision prevention."""
	
	def setup_method(self):
		"""Set up test rule."""
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		self.rule = NumberingRule.objects.create(
			entity_type='invoice',
			prefix='INV',
			sequence_length=6,
			created_by=self.admin,
			updated_by=self.admin
		)
	
	def test_sequence_increments(self):
		"""Test that sequence increments with each call."""
		seq1 = get_next_sequence_value(self.rule)
		seq2 = get_next_sequence_value(self.rule)
		seq3 = get_next_sequence_value(self.rule)
		
		assert seq1 == 1
		assert seq2 == 2
		assert seq3 == 3
	
	def test_sequence_no_duplicates(self):
		"""Test that concurrent requests don't generate duplicates."""
		# Generate multiple sequences
		sequences = [get_next_sequence_value(self.rule) for _ in range(5)]
		
		# All should be unique
		assert len(sequences) == len(set(sequences))
		assert sequences == [1, 2, 3, 4, 5]


@pytest.mark.django_db
class TestNumberGeneration:
	"""Test number generation with various rules."""
	
	def setup_method(self):
		"""Set up test rules."""
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
	
	def test_generate_number_basic(self):
		"""Test generating a number."""
		NumberingRule.objects.create(
			entity_type='invoice',
			prefix='INV',
			is_enabled=True,
			sequence_length=6,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		number = generate_number('invoice', self.admin)
		assert number.startswith('INV-')
		assert '000001' in number
	
	def test_generate_number_increments(self):
		"""Test that subsequent numbers increment."""
		NumberingRule.objects.create(
			entity_type='invoice',
			prefix='INV',
			is_enabled=True,
			sequence_length=6,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		num1 = generate_number('invoice', self.admin)
		num2 = generate_number('invoice', self.admin)
		num3 = generate_number('invoice', self.admin)
		
		assert '000001' in num1
		assert '000002' in num2
		assert '000003' in num3
	
	def test_generate_number_no_rule(self):
		"""Test error when no rule defined."""
		with pytest.raises(NoRuleDefinedError):
			generate_number('nonexistent', self.admin)
	
	def test_generate_number_disabled(self):
		"""Test error when numbering disabled."""
		NumberingRule.objects.create(
			entity_type='invoice',
			is_enabled=False,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		with pytest.raises(NumberingDisabledError):
			generate_number('invoice', self.admin)


@pytest.mark.django_db
class TestNumberAssignment:
	"""Test assigning numbers to entity instances."""
	
	def setup_method(self):
		"""Set up test environment."""
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		self.rule = NumberingRule.objects.create(
			entity_type='invoice',
			prefix='INV',
			is_enabled=True,
			sequence_length=6,
			created_by=self.admin,
			updated_by=self.admin
		)
		self.entity_id = uuid.uuid4()
	
	def test_assign_number(self):
		"""Test assigning number to entity."""
		assigned = assign_number('invoice', self.entity_id, self.admin)
		
		assert assigned.entity_type == 'invoice'
		assert assigned.entity_id == self.entity_id
		assert assigned.number.startswith('INV-')
		assert assigned.assigned_by == self.admin
	
	def test_assigned_number_immutable(self):
		"""Test that assigned numbers cannot be modified."""
		assigned = assign_number('invoice', self.entity_id, self.admin)
		original_number = assigned.number
		
		# Try to modify
		assigned.number = 'MODIFIED'
		with pytest.raises(ValidationError):
			assigned.save()
		
		# Verify original unchanged
		assigned.refresh_from_db()
		assert assigned.number == original_number
	
	def test_assigned_number_cannot_delete(self):
		"""Test that assigned numbers cannot be deleted."""
		assigned = assign_number('invoice', self.entity_id, self.admin)
		
		with pytest.raises(ValidationError):
			assigned.delete()
		
		# Verify still exists
		assert AssignedNumber.objects.filter(pk=assigned.pk).exists()
	
	def test_entity_cannot_have_multiple_numbers(self):
		"""Test that entity cannot be assigned multiple numbers."""
		assign_number('invoice', self.entity_id, self.admin)
		
		with pytest.raises(ValidationError):
			assign_number('invoice', self.entity_id, self.admin)
	
	def test_numbers_are_unique(self):
		"""Test that each entity gets unique number."""
		id1 = uuid.uuid4()
		id2 = uuid.uuid4()
		id3 = uuid.uuid4()
		
		num1 = assign_number('invoice', id1, self.admin).number
		num2 = assign_number('invoice', id2, self.admin).number
		num3 = assign_number('invoice', id3, self.admin).number
		
		assert num1 != num2
		assert num2 != num3
		assert num1 != num3


@pytest.mark.django_db
class TestNumberLookup:
	"""Test retrieving assigned numbers."""
	
	def setup_method(self):
		"""Set up test environment."""
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'pass')
		self.rule = NumberingRule.objects.create(
			entity_type='invoice',
			prefix='INV',
			is_enabled=True,
			created_by=self.admin,
			updated_by=self.admin
		)
		self.entity_id = uuid.uuid4()
	
	def test_get_assigned_number(self):
		"""Test retrieving assigned number."""
		assigned = assign_number('invoice', self.entity_id, self.admin)
		
		number = get_assigned_number('invoice', self.entity_id)
		assert number == assigned.number
	
	def test_get_assigned_number_not_found(self):
		"""Test retrieving non-existent assignment."""
		number = get_assigned_number('invoice', uuid.uuid4())
		assert number is None
	
	def test_has_assigned_number(self):
		"""Test checking if number is assigned."""
		unassigned_id = uuid.uuid4()
		assigned_id = uuid.uuid4()
		
		assign_number('invoice', assigned_id, self.admin)
		
		assert has_assigned_number('invoice', assigned_id) is True
		assert has_assigned_number('invoice', unassigned_id) is False


# ============================================================================
# USER/ADMIN TESTS - Admin interface workflows
# ============================================================================


class TestAdminNumberingRuleWorkflows(TestCase):
	"""Test admin workflows for numbering rule management."""
	
	def setUp(self):
		"""Set up test data."""
		self.client = Client()
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
	
	def test_admin_login(self):
		"""Test admin can login."""
		success = self.client.login(username='admin', password='adminpass')
		assert success is True
	
	def test_admin_can_create_numbering_rule(self):
		"""Test admin can create numbering rule."""
		self.client.login(username='admin', password='adminpass')
		
		response = self.client.post(
			reverse('admin:numbering_numberingrule_add'),
			{
				'entity_type': 'invoice',
				'is_enabled': True,
				'prefix': 'INV',
				'include_year': True,
				'include_month': False,
				'sequence_length': 6,
				'delimiter': '-',
				'reset_behavior': 'yearly',
				'description': 'Invoice numbering',
				'is_active': True,
			},
			follow=True,
		)
		
		assert response.status_code == 200
		rule = NumberingRule.objects.get(entity_type='invoice')
		assert rule.prefix == 'INV'
		assert rule.is_enabled is True
	
	def test_admin_numbering_rule_list(self):
		"""Test admin can view numbering rule list."""
		self.client.login(username='admin', password='adminpass')
		
		NumberingRule.objects.create(
			entity_type='invoice',
			prefix='INV',
			created_by=self.admin,
			updated_by=self.admin
		)
		
		response = self.client.get(reverse('admin:numbering_numberingrule_changelist'))
		assert response.status_code == 200
		assert b'invoice' in response.content
	
	def test_admin_can_edit_numbering_rule(self):
		"""Test admin can edit numbering rule."""
		self.client.login(username='admin', password='adminpass')
		
		rule = NumberingRule.objects.create(
			entity_type='invoice',
			prefix='INV',
			is_enabled=True,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		response = self.client.post(
			reverse('admin:numbering_numberingrule_change', args=[rule.id]),
			{
				'entity_type': 'invoice',
				'is_enabled': False,  # Changed
				'prefix': 'INV',
				'include_year': False,
				'include_month': False,
				'sequence_length': 5,
				'delimiter': '-',
				'reset_behavior': 'none',
				'description': '',
				'is_active': True,
			},
			follow=True,
		)
		
		assert response.status_code == 200
		rule.refresh_from_db()
		assert rule.is_enabled is False


class TestAdminNumberSequenceWorkflows(TestCase):
	"""Test admin viewing of number sequences (read-only)."""
	
	def setUp(self):
		"""Set up test data."""
		self.client = Client()
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
	
	def test_admin_can_view_number_sequences(self):
		"""Test admin can view sequence list."""
		self.client.login(username='admin', password='adminpass')
		
		rule = NumberingRule.objects.create(
			entity_type='invoice',
			created_by=self.admin,
			updated_by=self.admin
		)
		
		response = self.client.get(reverse('admin:numbering_numbersequence_changelist'))
		assert response.status_code == 200
	
	def test_admin_cannot_add_sequence(self):
		"""Test admin cannot manually add sequences."""
		self.client.login(username='admin', password='adminpass')
		
		response = self.client.get(reverse('admin:numbering_numbersequence_add'))
		assert response.status_code == 403


class TestAdminAssignedNumberWorkflows(TestCase):
	"""Test admin viewing of assigned numbers (read-only)."""
	
	def setUp(self):
		"""Set up test data."""
		self.client = Client()
		self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'adminpass')
	
	def test_admin_can_view_assigned_numbers(self):
		"""Test admin can view assigned numbers."""
		self.client.login(username='admin', password='adminpass')
		
		rule = NumberingRule.objects.create(
			entity_type='invoice',
			created_by=self.admin,
			updated_by=self.admin
		)
		
		entity_id = uuid.uuid4()
		AssignedNumber.objects.create(
			rule=rule,
			entity_type='invoice',
			entity_id=entity_id,
			number='INV-000001',
			assigned_by=self.admin,
			created_by=self.admin,
			updated_by=self.admin
		)
		
		response = self.client.get(reverse('admin:numbering_assignednumber_changelist'))
		assert response.status_code == 200
		assert b'INV-000001' in response.content
	
	def test_admin_cannot_add_assigned_number(self):
		"""Test admin cannot manually add assigned numbers."""
		self.client.login(username='admin', password='adminpass')
		
		response = self.client.get(reverse('admin:numbering_assignednumber_add'))
		assert response.status_code == 403
