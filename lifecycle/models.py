# lifecycle/models.py
# Models for the Lifecycle Framework.
# Source: Lifecycle Framework Specification V1, Sections 1–3.
#
# Three model types:
#   1. LifecycleStateDef — tenant-scoped state definitions
#   2. LifecycleTransitionRule — tenant-scoped transition rules
#   3. LifecycleTransitionAudit — immutable audit log (raw fields for data preservation)

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q, CheckConstraint
from config.base_models import TenantModel


class LifecycleStateDef(TenantModel):
    """
    Defines a valid state for an entity type within a tenant.
    One per (tenant_id, entity_type, state_name).

    Attributes:
        entity_type: Logical type being managed (e.g., 'Task', 'WorkOrder')
        state_name: Machine-readable identifier (e.g., 'ACTIVE', 'DRAFT')
        state_label: Human-readable label (e.g., 'Active', 'Draft')
        state_type: 'normal' | 'locked' | 'final'
        is_default: Exactly one per (tenant_id, entity_type)
        sort_order: Display order
        description: Notes on this state

    Source: Lifecycle Framework Specification V1, Section 1.
    """

    class StateTypeChoices(models.TextChoices):
        NORMAL = 'normal', 'Normal'
        LOCKED = 'locked', 'Locked'
        FINAL = 'final', 'Final'

    entity_type = models.CharField(max_length=50)
    state_name = models.CharField(max_length=50)
    state_label = models.CharField(max_length=100)
    state_type = models.CharField(
        max_length=10,
        choices=StateTypeChoices.choices,
        default=StateTypeChoices.NORMAL
    )
    is_default = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'lifecycle_lifecyclestatedef'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'entity_type', 'state_name'],
                name='unique_state_per_entity'
            ),
        ]
        indexes = [
            models.Index(fields=['tenant_id', 'entity_type']),
            models.Index(fields=['tenant_id', 'entity_type', 'is_default']),
        ]

    def __str__(self):
        return f'{self.entity_type}:{self.state_label}'

    def save(self, *args, **kwargs):
        """
        Override save() to enforce: exactly one is_default per (tenant_id, entity_type).
        If this state is being set as default, unset all others for this entity type.
        """
        if self.is_default:
            # Clear is_default for all other states of this entity type in this tenant
            LifecycleStateDef.all_objects.filter(
                tenant_id=self.tenant_id,
                entity_type=self.entity_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)

        super().save(*args, **kwargs)


class LifecycleTransitionRule(TenantModel):
    """
    Defines a valid transition between two states for an entity type.
    One per (tenant_id, entity_type, from_state, to_state).

    Attributes:
        entity_type: Logical type being managed
        from_state: Source state_name (must exist in LifecycleStateDef)
        to_state: Target state_name (must exist in LifecycleStateDef)
        required_role: If set, user must have this role (e.g., 'Approver')
        requires_reason: If True, transition requires a reason/comment
        is_admin_override: If True, allows transition even from final states
        description: Notes on this rule

    Source: Lifecycle Framework Specification V1, Section 2.
    """

    entity_type = models.CharField(max_length=50)
    from_state = models.CharField(max_length=50)
    to_state = models.CharField(max_length=50)
    required_role = models.CharField(max_length=100, blank=True)
    requires_reason = models.BooleanField(default=False)
    is_admin_override = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'lifecycle_lifecycletransitionrule'
        constraints = [
            models.UniqueConstraint(
                fields=['tenant_id', 'entity_type', 'from_state', 'to_state'],
                name='unique_transition_per_entity'
            ),
            CheckConstraint(
                condition=~Q(from_state=models.F('to_state')),
                name='from_state_ne_to_state'
            ),
        ]
        indexes = [
            models.Index(fields=['tenant_id', 'entity_type']),
            models.Index(fields=['tenant_id', 'entity_type', 'from_state']),
        ]

    def __str__(self):
        return f'{self.entity_type}: {self.from_state} → {self.to_state}'

    def clean(self):
        """
        Validate that:
        1. from_state exists as a state_name in LifecycleStateDef
        2. to_state exists as a state_name in LifecycleStateDef
        3. from_state is not a 'final' state (unless is_admin_override=True)
        """
        super().clean()

        # Check from_state exists
        try:
            from_state_def = LifecycleStateDef.all_objects.get(
                tenant_id=self.tenant_id,
                entity_type=self.entity_type,
                state_name=self.from_state
            )
        except LifecycleStateDef.DoesNotExist:
            raise ValidationError(
                f"from_state '{self.from_state}' does not exist for "
                f"entity_type '{self.entity_type}' in this tenant."
            )

        # Check to_state exists
        try:
            to_state_def = LifecycleStateDef.all_objects.get(
                tenant_id=self.tenant_id,
                entity_type=self.entity_type,
                state_name=self.to_state
            )
        except LifecycleStateDef.DoesNotExist:
            raise ValidationError(
                f"to_state '{self.to_state}' does not exist for "
                f"entity_type '{self.entity_type}' in this tenant."
            )

        # Check from_state is not final (unless admin override)
        if (from_state_def.state_type == LifecycleStateDef.StateTypeChoices.FINAL
                and not self.is_admin_override):
            raise ValidationError(
                f"Cannot transition from final state '{self.from_state}' "
                f"unless is_admin_override=True."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class LifecycleTransitionAudit(models.Model):
    """
    Immutable audit log of state transitions. NOT a TenantModel.
    Uses raw UUID fields (no ForeignKeys) to preserve records even if
    tenant or user is deleted.

    Attributes:
        id: UUIDField primary key
        tenant_id: Raw UUID, not a FK
        timestamp: auto_now_add
        user_id: Raw UUID, not a FK
        user_display: Snapshot of user email at time of transition
        entity_type: Type being transitioned
        entity_id: Instance ID (raw UUID)
        from_state: Previous state
        to_state: New state
        reason: Optional transition reason/comment
        is_override: Whether this used admin override
        ip_address: Originating IP (if available)

    Immutability:
    - save() raises ValidationError if instance already has a pk
    - delete() always raises ValidationError
    - No Django admin add/change/delete permissions

    Source: Lifecycle Framework Specification V1, Section 3.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    user_id = models.UUIDField()
    user_display = models.CharField(max_length=200)
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    from_state = models.CharField(max_length=50)
    to_state = models.CharField(max_length=50)
    reason = models.TextField(blank=True)
    is_override = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'lifecycle_lifecycletransitionaudit'
        default_permissions = ()
        indexes = [
            models.Index(fields=['tenant_id', 'entity_type', 'entity_id']),
            models.Index(fields=['tenant_id', 'entity_type']),
            models.Index(fields=['tenant_id', 'timestamp']),
            models.Index(fields=['user_id']),
        ]

    def __str__(self):
        return f'{self.entity_type}:{self.entity_id} {self.from_state}→{self.to_state}'

    def save(self, *args, **kwargs):
        """Prevent modification of existing audit records."""
        if not self._state.adding:
            raise ValidationError("Audit records are immutable and cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of audit records."""
        raise ValidationError("Audit records are immutable and cannot be deleted.")
