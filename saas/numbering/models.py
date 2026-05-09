# numbering/models.py
# Models for the Numbering Service.
# Source: Numbering Service Specification V1, Sections 2, 3.
#
# Models:
#   NumberingRule — tenant-scoped rule for generating numbers
#   NumberSequence — tracks current sequence value and reset dates
#   AssignedNumber — immutable record of numbers assigned to entities

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from config.base_models import TenantModel


class NumberingRule(TenantModel):
    """
    Defines the numbering pattern for an entity type.
    Source: Numbering Service Specification V1, Section 2.1.

    Each tenant can have one rule per entity_type (e.g., 'customer', 'work_order').
    The rule controls prefix, year format, sequence reset behavior, etc.
    """

    class YearFormatChoices(models.TextChoices):
        YY = 'YY', 'YY'
        YYYY = 'YYYY', 'YYYY'

    class ResetBehaviorChoices(models.TextChoices):
        NONE = 'none', 'None'
        YEARLY = 'yearly', 'Yearly'
        MONTHLY = 'monthly', 'Monthly'

    entity_type = models.CharField(
        max_length=50,
        help_text='Machine key (e.g. customer, work_order, service_request)'
    )
    is_enabled = models.BooleanField(default=True)
    prefix = models.CharField(
        max_length=20,
        help_text='e.g. C, W, I, SR, YU'
    )
    include_year = models.BooleanField(default=True)
    year_format = models.CharField(
        max_length=4,
        choices=YearFormatChoices.choices,
        default=YearFormatChoices.YY
    )
    include_month = models.BooleanField(default=False)
    sequence_length = models.PositiveIntegerField(default=4)
    delimiter = models.CharField(max_length=5, default='-')
    reset_behavior = models.CharField(
        max_length=10,
        choices=ResetBehaviorChoices.choices,
        default=ResetBehaviorChoices.YEARLY
    )
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'numbering_numberingrule'
        unique_together = [('tenant_id', 'entity_type')]
        indexes = [
            models.Index(fields=['tenant_id', 'entity_type']),
            models.Index(fields=['tenant_id', 'is_enabled']),
        ]

    def __str__(self):
        return f'{self.entity_type} ({self.prefix})'


class NumberSequence(models.Model):
    """
    Tracks the current sequence value and reset dates for a numbering rule.
    Source: Numbering Service Specification V1, Section 2.2.

    NOT a TenantModel — one-to-one with NumberingRule, no audit fields needed.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    rule = models.OneToOneField(
        NumberingRule,
        on_delete=models.CASCADE,
        related_name='sequence'
    )
    current_value = models.PositiveIntegerField(default=0)
    last_reset_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'numbering_numbersequence'

    def __str__(self):
        return f'Sequence for {self.rule.entity_type} (value={self.current_value})'

    def save(self, *args, **kwargs):
        """
        Ensure tenant_id always mirrors the linked rule's tenant.
        This keeps NumberSequence consistent when created via get_or_create(rule=...).
        """
        if self.rule_id and not self.tenant_id:
            # rule is already fetched in most call paths; fallback to FK fetch if needed
            self.tenant_id = self.rule.tenant_id
        super().save(*args, **kwargs)


class AssignedNumber(TenantModel):
    """
    Immutable record of a number assigned to an entity.
    Source: Numbering Service Specification V1, Section 2.3.

    Once created, this record cannot be modified or deleted.
    """

    rule = models.ForeignKey(
        NumberingRule,
        on_delete=models.PROTECT,
        related_name='assignments'
    )
    entity_type = models.CharField(
        max_length=50,
        help_text='Denormalized from rule for fast queries'
    )
    entity_id = models.UUIDField()
    number = models.CharField(max_length=100)
    assigned_at = models.DateTimeField(auto_now_add=True, editable=False)
    assigned_by = models.CharField(
        max_length=200,
        help_text='User email or "System"'
    )

    class Meta:
        db_table = 'numbering_assignednumber'
        unique_together = [
            ('tenant_id', 'entity_type', 'number'),
            ('tenant_id', 'entity_type', 'entity_id'),
        ]
        indexes = [
            models.Index(fields=['tenant_id', 'entity_type']),
            models.Index(fields=['tenant_id', 'entity_id']),
            models.Index(fields=['tenant_id', 'number']),
            models.Index(fields=['assigned_at']),
        ]

    def __str__(self):
        return f'{self.entity_type}={self.number}'

    def save(self, *args, **kwargs):
        """Prevent modifications to existing records."""
        if self.pk and not self._state.adding:
            raise ValidationError('AssignedNumber records are immutable.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of records."""
        raise ValidationError('AssignedNumber records cannot be deleted.')
