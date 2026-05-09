"""
Core Models - Base classes implementing Platform Core Persistence Standards

All models inherit from BaseModel to ensure:
- UUID primary keys
- Created/updated timestamps
- User attribution (created_by/updated_by)
- Soft delete support (is_active flag)
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class BaseModel(models.Model):
    """
    Abstract base model implementing Platform Core Persistence Standards.
    
    Required Fields (per specification):
    - id: UUID primary key
    - created_at: timestamp
    - updated_at: timestamp
    - created_by: user reference
    - updated_by: user reference
    - is_active: boolean flag (operational status, not workflow state)
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        help_text="Timestamp when record was created (set once, never changes)"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when record was last modified"
    )
    
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_created",
        editable=False,
        help_text="User who created this record"
    )
    
    updated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_updated",
        help_text="User who last updated this record"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Operational flag for disabling records without deleting them"
    )
    
    class Meta:
        abstract = True
        # Standard indexes per specification
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['is_active']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Override save to enforce metadata standards.
        Note: created_by and updated_by should be set by view/form layer.
        """
        if not self.pk:
            # New record - ensure created_at is set
            if not self.created_at:
                self.created_at = timezone.now()
        
        # Always update updated_at
        self.updated_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.__class__.__name__} ({self.id})"


class LifecycleModel(BaseModel):
    """
    Abstract model for entities that use the Lifecycle Framework.
    
    Adds lifecycle state tracking per Platform Core Status & Lifecycle Framework.
    """
    
    lifecycle_state = models.CharField(
        max_length=50,
        help_text="Current lifecycle state"
    )
    
    lifecycle_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Justification for state transition (required for some transitions)"
    )
    
    lifecycle_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when lifecycle_state last changed"
    )
    
    lifecycle_changed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_lifecycle_changed",
        null=True,
        blank=True,
        help_text="User who last changed lifecycle_state"
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['lifecycle_state']),
            models.Index(fields=['lifecycle_changed_at']),
        ]


# System Configuration Models per Platform Core System Configuration Specification


class Preference(BaseModel):
    """
    System-wide configuration item (Global Preferences).
    
    Implements Platform Core System Configuration specification.
    Controls runtime system behavior without code changes.
    """
    
    DATA_TYPE_CHOICES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('decimal', 'Decimal'),
        ('boolean', 'Boolean'),
        ('date', 'Date'),
        ('time', 'Time'),
        ('path', 'File/Directory Path'),
        ('password', 'Password'),
    ]
    
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique configuration key"
    )
    
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name"
    )
    
    description = models.TextField(
        help_text="Purpose and usage of this preference"
    )
    
    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
        help_text="Data type for type enforcement"
    )
    
    value = models.TextField(
        help_text="Current value (stored as text, cast by application)"
    )
    
    default_value = models.TextField(
        help_text="Default value"
    )
    
    preference_group = models.CharField(
        max_length=50,
        default='General',
        help_text="Logical grouping for UI display"
    )

    is_secret = models.BooleanField(
        default=False,
        help_text="If True, value is masked in UI"
    )

    is_locked = models.BooleanField(
        default=False,
        help_text="If True, value cannot be changed by users (system process only)"
    )

    input_type = models.CharField(
        max_length=20,
        blank=True,
        help_text="Specific UI widget hints (color, file, etc.)"
    )

    is_editable = models.BooleanField(
        default=True,
        help_text="Whether this preference can be edited by administrators"
    )
    
    class Meta:
        verbose_name = "Preference"
        verbose_name_plural = "Preferences"
        ordering = ['key']
        indexes = [
            models.Index(fields=['key']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.key})"


class ValueList(BaseModel):
    """
    Managed list of selectable values (picklists/dropdowns).
    
    Implements Platform Core System Configuration specification.
    """
    
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique value list identifier"
    )
    
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Purpose and usage of this value list"
    )
    
    class Meta:
        verbose_name = "Value List"
        verbose_name_plural = "Value Lists"
        ordering = ['name']
        indexes = [
            models.Index(fields=['key']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.key})"


class ValueListItem(BaseModel):
    """
    Individual value within a ValueList.
    
    Implements Platform Core System Configuration specification.
    """
    
    value_list = models.ForeignKey(
        ValueList,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Parent value list"
    )
    
    value = models.CharField(
        max_length=100,
        help_text="Actual value stored/used in code"
    )
    
    display_label = models.CharField(
        max_length=200,
        help_text="User-visible label"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Optional description"
    )
    
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )
    
    class Meta:
        verbose_name = "Value List Item"
        verbose_name_plural = "Value List Items"
        ordering = ['value_list', 'sort_order', 'display_label']
        unique_together = [['value_list', 'value']]
        indexes = [
            models.Index(fields=['value_list', 'is_active']),
            models.Index(fields=['value_list', 'sort_order']),
        ]
    
    def __str__(self):
        return f"{self.value_list.name}: {self.display_label}"
