# config/base_models.py
# Abstract base model and manager used by every tenant-scoped model in SDTA.
# Source: Multi-Tenancy Specification V1, Section 4; Technical Architecture V2, Section 4.

import uuid
from django.db import models
from .tenant_context import get_current_tenant_id


class TenantManager(models.Manager):
    """
    Default manager for all TenantModel subclasses.

    Automatically injects a tenant_id filter on every queryset so that
    application code never accidentally reads another tenant's data.
    Falls back to an unfiltered queryset only when no tenant context is set
    (e.g. management commands, Celery tasks using the worker alias).
    """

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = get_current_tenant_id()
        if tenant_id:
            return qs.filter(tenant_id=tenant_id)
        return qs


class TenantModel(models.Model):
    """
    Abstract base class for every multi-tenant model in SDTA.

    Fields
    ------
    id          UUIDv4 primary key — no sequential integers exposed in URLs.
    tenant_id   UUID enforced at the DB level via RLS; auto-injected on save.
    created_by  CharField — who created the record (user email or 'System').
    created_on  DateTimeField (auto_now_add) — UTC.
    updated_by  CharField — who last modified the record.
    updated_on  DateTimeField (auto_now) — UTC.

    Managers
    --------
    objects       TenantManager — always filtered to current tenant (default).
    all_objects   Unfiltered manager — for system/background tasks only.

    Usage notes
    -----------
    - Never import TenantModel directly in app code; subclass it.
    - Always use `objects` in view/API code; reserve `all_objects` for
      management commands and Celery tasks running on the worker DB alias.
    - Cross-tenant writes are blocked: save() raises if the tenant_id on the
      instance does not match the current request context.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    # Standard audit metadata — Architectural Mandate #8.
    # All timestamps stored in UTC; display TZ from TenantPreference.
    created_by = models.CharField(max_length=200, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=200, blank=True)
    updated_on = models.DateTimeField(auto_now=True)

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def clean(self):
        """
        Validates that all related objects belong to the same tenant.
        Prevents cross-tenant data leakage via ID injection.
        """
        super().clean()
        for field in self._meta.fields:
            if isinstance(field, models.ForeignKey):
                # Skip when the FK isn't set. Resolving an unset required FK
                # via getattr(self, field.name) raises RelatedObjectDoesNotExist
                # in Django 5+, which would mask the proper "field is required"
                # ValidationError that field-level validation will surface.
                if getattr(self, f'{field.name}_id', None) is None:
                    continue
                related_obj = getattr(self, field.name)
                if related_obj and hasattr(related_obj, 'tenant_id'):
                    if str(related_obj.tenant_id) != str(self.tenant_id):
                        raise ValueError(
                            f"Cross-tenant integrity error: {field.name} "
                            f"belongs to a different tenant."
                        )

    def save(self, *args, **kwargs):
        """
        Enforces tenant context and triggers cleaning.
        """
        current = get_current_tenant_id()

        if not self.tenant_id and current:
            self.tenant_id = current

        if not self.tenant_id:
            # If no tenant context, this record is orphaned.
            raise ValueError("Cannot save TenantModel without a tenant_id in context.")

        if current and str(self.tenant_id) != str(current):
            raise ValueError(
                f"Cross-tenant write blocked: model tenant_id={self.tenant_id} "
                f"does not match request tenant_id={current}."
            )

        # Ensure cleaning logic runs before save.
        # Let DB enforce uniqueness/constraints; keep model-level field/type validation.
        self.full_clean(validate_unique=False, validate_constraints=False)
        super().save(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# Exclusive Arc pattern — shared by Note and Document models.
# Source: Note & Document Implementation Specification V1.
# ═══════════════════════════════════════════════════════════════════════════════

PARENT_FK_FIELDS = [
    'customer', 'contact', 'lead', 'opportunity', 'quote', 'invoice',
    'work_order', 'asset', 'service_request', 'prev_maint', 'workflow',
    'payment', 'user', 'vendor', 'purchase_order', 'work_group', 'task',
    'vehicle', 'warehouse', 'ledger', 'requisition', 'rma', 'equipment',
    'safety_form', 'vendor_bill',
]


class ExclusiveArcMixin:
    """
    Mixin providing exclusive arc constraint validation.

    Ensures exactly one parent FK is set (not zero, not multiple).
    Used by both Note (notes app) and Document (documents app).
    """

    def clean(self):
        """Validate that exactly one parent FK is set."""
        from django.core.exceptions import ValidationError
        parent_fields = [getattr(self, f'{f}_id', None) for f in PARENT_FK_FIELDS]
        set_count = sum(1 for f in parent_fields if f is not None)

        if set_count == 0:
            raise ValidationError(
                f"A {self.__class__.__name__} must be attached to exactly one parent entity."
            )
        if set_count > 1:
            raise ValidationError(
                f"A {self.__class__.__name__} cannot be attached to multiple parent entities."
            )

    def save(self, *args, **kwargs):
        """Call clean() before save to enforce exclusive arc validation."""
        self.clean()
        super().save(*args, **kwargs)
