"""
Numbering and Identity Services Models

Implements human-readable number generation per Platform Core Numbering & Identity spec.
Provides collision-free, deterministic numbering with audit trail.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel


class NumberingRule(BaseModel):
	"""
	Defines how numbers are generated for an entity type.
	
	Per specification: Core provides the mechanism, modules define their rules.
	"""
	
	RESET_CHOICES = [
		('none', 'No Reset'),
		('yearly', 'Reset Each Year'),
		('monthly', 'Reset Each Month'),
	]
	
	# Entity type identifier (e.g., "invoice", "workorder", "client")
	entity_type = models.CharField(
		max_length=50,
		unique=True,
		help_text="Entity type this rule applies to (e.g., 'invoice')"
	)
	
	# Enable/disable numbering for this entity
	is_enabled = models.BooleanField(
		default=True,
		help_text="Whether numbering is active for this entity"
	)
	
	# Format components
	prefix = models.CharField(
		max_length=50,
		blank=True,
		help_text="Static prefix (e.g., 'INV', 'WO')"
	)
	
	include_year = models.BooleanField(
		default=False,
		help_text="Include year in number format"
	)
	
	year_format = models.CharField(
		max_length=4,
		choices=[('YYYY', 'Full Year (2026)'), ('YY', 'Short Year (26)')],
		default='YYYY',
		help_text="Year format if include_year is True"
	)
	
	include_month = models.BooleanField(
		default=False,
		help_text="Include MM in number format"
	)

	# Custom Format Support
	custom_format = models.CharField(
		max_length=50,
		blank=True,
		null=True,
		help_text="Custom formatter function name (e.g., 'alpha_year')"
	)
	
	# Sequence configuration
	sequence_length = models.PositiveIntegerField(
		default=5,
		help_text="Length of numeric sequence part (padded with zeros)"
	)
	
	delimiter = models.CharField(
		max_length=5,
		default='-',
		help_text="Delimiter between format components"
	)
	
	# Reset behavior
	reset_behavior = models.CharField(
		max_length=20,
		choices=RESET_CHOICES,
		default='none',
		help_text="When to reset sequence (yearly, monthly, or never)"
	)
	
	# Documentation
	description = models.TextField(
		blank=True,
		help_text="Description of this numbering rule"
	)
	
	class Meta:
		indexes = [
			models.Index(fields=['entity_type']),
			models.Index(fields=['is_enabled']),
		]
	
	def __str__(self):
		return f"{self.entity_type} Numbering"


class NumberSequence(models.Model):
	"""
	Atomic sequence counter for a numbering rule.
	
	Stores current sequence value. Atomically incremented to ensure no duplicates.
	Uses database-level locking for concurrency safety.
	"""
	
	# Reference to numbering rule
	rule = models.OneToOneField(
		NumberingRule,
		on_delete=models.CASCADE,
		related_name='sequence',
		help_text="The numbering rule this sequence belongs to"
	)
	
	# Current sequence value
	current_value = models.PositiveIntegerField(
		default=0,
		help_text="Current sequence counter (incremented with each assignment)"
	)
	
	# Reset tracking
	last_reset_date = models.DateField(
		null=True,
		blank=True,
		help_text="Date sequence was last reset"
	)
	
	class Meta:
		# No permissions - internal use only
		permissions = []
	
	def __str__(self):
		return f"Sequence for {self.rule.entity_type}: {self.current_value}"


class AssignedNumber(BaseModel):
	"""
	Record of an assigned number for a specific entity instance.
	
	Per specification:
	- Numbers are assigned once and never change (immutable)
	- Immutable once created
	"""
	
	# Reference to numbering rule
	rule = models.ForeignKey(
		NumberingRule,
		on_delete=models.PROTECT,
		related_name='assigned_numbers',
		help_text="The numbering rule used to generate this number"
	)
	
	# Entity reference
	entity_type = models.CharField(
		max_length=50,
		help_text="Type of entity assigned this number"
	)
	
	entity_id = models.UUIDField(
		help_text="UUID of entity assigned this number"
	)
	
	# The actual assigned number (immutable)
	number = models.CharField(
		max_length=100,
		help_text="The generated human-readable number"
	)
	
	# Assignment details
	assigned_at = models.DateTimeField(
		auto_now_add=True,
		editable=False,
		help_text="When this number was assigned"
	)
	
	assigned_by = models.ForeignKey(
		'auth.User',
		on_delete=models.PROTECT,
		related_name='assigned_numbers',
		help_text="User/system that triggered the assignment"
	)
	
	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=['entity_type', 'number'],
				name='unique_number_per_entity_type'
			),
			models.UniqueConstraint(
				fields=['entity_type', 'entity_id'],
				name='unique_entity_assignment'
			),
		]
		indexes = [
			models.Index(fields=['entity_type']),
			models.Index(fields=['entity_id']),
			models.Index(fields=['number']),
			models.Index(fields=['assigned_at']),
		]
	
	def save(self, *args, **kwargs):
		"""AssignedNumbers are immutable once created."""
		# Only check immutability on updates (pk is set and this is an update)
		if self.pk is not None and 'force_insert' not in kwargs:
			# Check if this is a real update (not force_insert=True which is creation)
			try:
				existing = AssignedNumber.objects.get(pk=self.pk)
				# If we get here, it's a real update attempt
				raise ValidationError("Assigned numbers are immutable and cannot be modified")
			except AssignedNumber.DoesNotExist:
				# Object doesn't exist, this is creation
				pass
		super().save(*args, **kwargs)
	
	def delete(self, *args, **kwargs):
		"""AssignedNumbers are immutable and cannot be deleted."""
		raise ValidationError("Assigned numbers are immutable and cannot be deleted")
	
	def __str__(self):
		return f"{self.entity_type}: {self.number}"
