"""
Lifecycle Framework Models - Status and Lifecycle Framework

Implements the Lifecycle Framework per Platform Core Specification.
Defines state registration, transition rules, and audit logging.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import BaseModel


class LifecycleStateDef(BaseModel):
    """
    Registers allowed lifecycle states for an entity type.
    
    Modules define their state sets by creating instances of this model.
    Per specification: Core provides the mechanism, modules define their states.
    """
    
    STATE_TYPE_CHOICES = [
        ('normal', 'Normal State'),
        ('locked', 'Locked State'),
        ('final', 'Final State'),
    ]
    
    # Entity type identifier (e.g., "order", "invoice", "quote")
    entity_type = models.CharField(
        max_length=50,
        help_text="Entity type this state applies to (e.g., 'order')"
    )
    
    # State name/value
    state_name = models.CharField(
        max_length=50,
        help_text="Machine-readable state name (e.g., 'draft', 'approved')"
    )
    
    # Display label
    state_label = models.CharField(
        max_length=100,
        help_text="Human-friendly display label (e.g., 'Draft')"
    )
    
    # State classification
    state_type = models.CharField(
        max_length=20,
        choices=STATE_TYPE_CHOICES,
        default='normal',
        help_text="Classification: normal, locked (no edits), or final (no transitions)"
    )
    
    # Whether this is the default initial state
    is_default = models.BooleanField(
        default=False,
        help_text="Default initial state for new records"
    )
    
    # Optional description
    description = models.TextField(
        blank=True,
        help_text="Documentation about this state"
    )
    
    class Meta:
        # Ensure only one default per entity type
        constraints = [
            models.UniqueConstraint(
                fields=['entity_type', 'state_name'],
                name='unique_entity_state'
            ),
        ]
        indexes = [
            models.Index(fields=['entity_type']),
            models.Index(fields=['entity_type', 'is_default']),
        ]
    
    def save(self, *args, **kwargs):
        """Enforce that only one default state per entity type."""
        if self.is_default:
            # Deactivate other defaults for this entity
            LifecycleStateDef.objects.filter(
                entity_type=self.entity_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.entity_type}: {self.state_label} ({self.state_name})"


class LifecycleTransitionRule(BaseModel):
    """
    Defines allowed state transitions for an entity type.
    
    Per specification: Transitions must be explicit. If not defined, transition is denied.
    """
    
    # Entity type this rule applies to
    entity_type = models.CharField(
        max_length=50,
        help_text="Entity type (e.g., 'order')"
    )
    
    # From state
    from_state = models.CharField(
        max_length=50,
        help_text="Starting state for this transition"
    )
    
    # To state
    to_state = models.CharField(
        max_length=50,
        help_text="Destination state for this transition"
    )
    
    # Optional permission requirement
    required_permission = models.CharField(
        max_length=100,
        blank=True,
        help_text="Permission required for this transition (e.g., 'approve')"
    )
    
    # Whether a reason is required for this transition
    requires_reason = models.BooleanField(
        default=False,
        help_text="Whether transition must include a reason text"
    )
    
    # Optional description
    description = models.TextField(
        blank=True,
        help_text="Documentation about when/why this transition occurs"
    )
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['entity_type', 'from_state', 'to_state'],
                name='unique_entity_transition'
            ),
        ]
        indexes = [
            models.Index(fields=['entity_type']),
            models.Index(fields=['entity_type', 'from_state']),
        ]
    
    def clean(self):
        """Validate that from_state and to_state are valid for entity_type."""
        if self.from_state == self.to_state:
            raise ValidationError(
                "Self-transitions (same from and to state) are not permitted"
            )
    
    def __str__(self):
        return f"{self.entity_type}: {self.from_state} → {self.to_state}"


class LifecycleTransitionAudit(models.Model):
    """
    Immutable audit log of all lifecycle state transitions.
    
    Per specification: Every successful transition must generate an audit entry.
    Audit entries must be immutable (no deletes, updates, or user attribution needed).
    """
    
    # Timestamp (immutable, set at creation)
    timestamp = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        help_text="When the transition occurred"
    )
    
    # User who performed transition
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='lifecycle_transitions',
        help_text="User who performed this transition"
    )
    
    # Entity information
    entity_type = models.CharField(
        max_length=50,
        help_text="Type of entity that changed state"
    )
    
    entity_id = models.UUIDField(
        help_text="ID of the entity that changed state"
    )
    
    # State change
    from_state = models.CharField(
        max_length=50,
        help_text="Previous lifecycle state"
    )
    
    to_state = models.CharField(
        max_length=50,
        help_text="New lifecycle state"
    )
    
    # Optional reason
    reason = models.TextField(
        blank=True,
        help_text="Reason for state transition (if provided)"
    )
    
    # Override flag
    is_override = models.BooleanField(
        default=False,
        help_text="Whether this was an administrative override transition"
    )
    
    class Meta:
        # Make immutable: no permissions for delete or change
        permissions = []
        indexes = [
            models.Index(fields=['entity_type']),
            models.Index(fields=['entity_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
        ]
    
    def delete(self, *args, **kwargs):
        """Audit entries cannot be deleted."""
        raise ValidationError("Lifecycle audit entries are immutable and cannot be deleted")
    
    def save(self, *args, **kwargs):
        """Audit entries cannot be modified after creation."""
        if self.pk is not None:
            raise ValidationError("Lifecycle audit entries are immutable and cannot be modified")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.entity_type}:{self.entity_id} {self.from_state}→{self.to_state} at {self.timestamp}"
