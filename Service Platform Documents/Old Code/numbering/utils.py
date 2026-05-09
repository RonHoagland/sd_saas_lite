"""
Numbering Service Utilities - Number generation and assignment.

Implements number generation logic per Platform Core Numbering & Identity spec.
Provides collision-free, thread-safe number generation.
"""

from django.db import transaction, DatabaseError
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime

from .models import NumberingRule, NumberSequence, AssignedNumber


class NumberingError(Exception):
	"""Base exception for numbering service errors."""
	pass


class NumberingDisabledError(NumberingError):
	"""Raised when trying to assign number for disabled entity type."""
	pass


class DuplicateNumberError(NumberingError):
	"""Raised when a duplicate number would be generated."""
	pass


class NoRuleDefinedError(NumberingError):
	"""Raised when no numbering rule exists for entity type."""
	pass


def get_or_create_sequence(rule):
	"""
	Get or create the sequence counter for a numbering rule.
	
	Args:
		rule: NumberingRule instance
	
	Returns:
		NumberSequence instance
	"""
	sequence, created = NumberSequence.objects.get_or_create(rule=rule)
	return sequence


def check_reset_needed(sequence):
	"""
	Check if sequence should be reset based on reset_behavior.
	
	Args:
		sequence: NumberSequence instance
	
	Returns:
		Boolean: True if reset occurred
	"""
	rule = sequence.rule
	today = timezone.now().date()
	
	if rule.reset_behavior == 'none':
		return False
	
	if rule.reset_behavior == 'yearly':
		# Reset if year has changed
		if sequence.last_reset_date is None or sequence.last_reset_date.year != today.year:
			sequence.current_value = 0
			sequence.last_reset_date = today
			sequence.save()
			return True
	
	elif rule.reset_behavior == 'monthly':
		# Reset if month has changed
		if sequence.last_reset_date is None or sequence.last_reset_date.month != today.month or sequence.last_reset_date.year != today.year:
			sequence.current_value = 0
			sequence.last_reset_date = today
			sequence.save()
			return True
	
	return False


def get_next_sequence_value(rule):
	"""
	Atomically increment and return next sequence value for a rule.
	
	Uses database-level SELECT FOR UPDATE to ensure atomicity and
	prevent duplicates under concurrent requests.
	
	Args:
		rule: NumberingRule instance
	
	Returns:
		Integer: Next sequence value
	
	Raises:
		NumberingError: If sequence cannot be generated
	"""
	sequence = get_or_create_sequence(rule)
	
	# Check if reset is needed (non-atomic but OK, worst case sequence restarts mid-period)
	check_reset_needed(sequence)
	
	# Atomically increment sequence
	try:
		with transaction.atomic():
			# Lock the row for update (prevents concurrent increments)
			sequence = NumberSequence.objects.select_for_update().get(pk=sequence.pk)
			
			# Double-check reset after lock
			check_reset_needed(sequence)
			
			# Increment
			sequence.current_value += 1
			next_value = sequence.current_value
			sequence.save()
			
			return next_value
	except DatabaseError as e:
		raise NumberingError(f"Failed to generate sequence: {str(e)}")


def format_number(rule, sequence_value):
	"""
	Format a number according to rule definition.
	
	Args:
		rule: NumberingRule instance
		sequence_value: Integer sequence value
	
	Returns:
		String: Formatted number (e.g., "INV26-000123" or "INV-2026-000123")
	"""
	components = []
	
	# Add prefix
	if rule.prefix:
		components.append(rule.prefix)
	
	# Add year
	if rule.include_year:
		year = timezone.now().year
		if hasattr(rule, 'year_format') and rule.year_format == 'YY':
			# Last 2 digits of year
			components.append(str(year % 100).zfill(2))
		else:
			# Full 4-digit year
			components.append(str(year))
	
	# Add month
	if rule.include_month:
		month = str(timezone.now().month).zfill(2)
		components.append(month)
	
	# Custom Format: Alpha Year (Year-Letter Encoding)
	if hasattr(rule, 'custom_format') and rule.custom_format == 'alpha_year':
		# Logic: 0-9 -> J, A-I
		# 1=A, 2=B, 3=C, 4=D, 5=E, 6=F, 7=G, 8=H, 9=I, 0=J
		# Example: 2026 -> 26 -> 2=B, 6=F -> BF
		year = timezone.now().year
		year_str = str(year % 100).zfill(2) # "26"
		
		mapping = {
			'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E', 
			'6': 'F', '7': 'G', '8': 'H', '9': 'I', '0': 'J'
		}
		
		alpha_code = "".join([mapping.get(digit, 'X') for digit in year_str])
		components.append(alpha_code)

	# Add padded sequence
	sequence_str = str(sequence_value).zfill(rule.sequence_length)
	components.append(sequence_str)
	
	# Join with delimiter
	return rule.delimiter.join(components)


@transaction.atomic
def generate_number(entity_type, user=None):
	"""
	Generate a new number for an entity type.
	
	Per specification:
	- Numbers are collision-free and deterministic
	- Sequence generation is atomic and thread-safe
	- Reset occurs automatically
	
	Args:
		entity_type: String identifier (e.g., 'invoice')
		user: User performing the generation (for audit)
	
	Returns:
		String: Generated number (e.g., "INV-2026-000123")
	
	Raises:
		NoRuleDefinedError: If no rule exists for entity type
		NumberingDisabledError: If numbering disabled for entity type
		NumberingError: If number cannot be generated
	"""
	# Get numbering rule
	try:
		rule = NumberingRule.objects.get(entity_type=entity_type)
	except NumberingRule.DoesNotExist:
		raise NoRuleDefinedError(f"No numbering rule defined for: {entity_type}")
	
	# Check if enabled
	if not rule.is_enabled:
		raise NumberingDisabledError(f"Numbering disabled for: {entity_type}")
	
	# Get next sequence value (atomic)
	sequence_value = get_next_sequence_value(rule)
	
	# Format number
	number = format_number(rule, sequence_value)
	
	return number


@transaction.atomic
def assign_number(entity_type, entity_id, user, auto_generate=True):
	"""
	Assign and record a number for an entity instance.
	
	Per specification:
	- Numbers are assigned once and never change (immutable)
	- Numbers are never reused
	- Assignment is tracked for audit purposes
	
	Args:
		entity_type: String identifier (e.g., 'invoice')
		entity_id: UUID of entity being numbered
		user: User performing the assignment
		auto_generate: If True, generate new number; if False, number must exist
	
	Returns:
		AssignedNumber instance
	
	Raises:
		ValidationError: If entity already has assigned number
		NumberingError: If number cannot be generated
	"""
	# Check if already assigned
	existing = AssignedNumber.objects.filter(
		entity_type=entity_type,
		entity_id=entity_id
	).first()
	
	if existing:
		raise ValidationError(
			f"{entity_type}:{entity_id} already has assigned number: {existing.number}"
		)
	
	# Generate new number
	if auto_generate:
		number = generate_number(entity_type, user)
	else:
		raise ValidationError("Manual number assignment not supported")
	
	# Create assignment record (atomic)
	assigned = AssignedNumber.objects.create(
		rule=NumberingRule.objects.get(entity_type=entity_type),
		entity_type=entity_type,
		entity_id=entity_id,
		number=number,
		assigned_by=user,
		created_by=user,
		updated_by=user
	)
	
	return assigned


def get_assigned_number(entity_type, entity_id):
	"""
	Retrieve the assigned number for an entity.
	
	Args:
		entity_type: String identifier
		entity_id: UUID of entity
	
	Returns:
		String: Assigned number, or None if not assigned
	"""
	try:
		assigned = AssignedNumber.objects.get(
			entity_type=entity_type,
			entity_id=entity_id
		)
		return assigned.number
	except AssignedNumber.DoesNotExist:
		return None


def has_assigned_number(entity_type, entity_id):
	"""
	Check if an entity has an assigned number.
	
	Args:
		entity_type: String identifier
		entity_id: UUID of entity
	
	Returns:
		Boolean
	"""
	return AssignedNumber.objects.filter(
		entity_type=entity_type,
		entity_id=entity_id
	).exists()


class NumberingMixin:
	"""
	Mixin for models to support automatic number assignment.
	
	Provides convenient methods for number management on entities.
	
	Usage:
		class MyEntity(BaseModel, NumberingMixin):
			entity_type = 'my_entity'
	"""
	
	# Subclasses must define:
	# entity_type = 'your_entity_type'
	
	def assign_number(self, user):
		"""
		Assign a number to this entity.
		
		Args:
			user: User performing the assignment
		
		Returns:
			String: Assigned number
		
		Raises:
			ValidationError: If already assigned
			NumberingError: If number cannot be generated
		"""
		assigned = assign_number(
			entity_type=self.entity_type,
			entity_id=self.id,
			user=user
		)
		return assigned.number
	
	def get_assigned_number(self):
		"""Get this entity's assigned number."""
		return get_assigned_number(self.entity_type, self.id)
	
	def has_assigned_number(self):
		"""Check if this entity has an assigned number."""
		return has_assigned_number(self.entity_type, self.id)