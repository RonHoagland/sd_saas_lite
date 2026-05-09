# staff/admin.py
# Contains:
#   1. TenantModelAdmin — base mixin for ALL tenant-model admin classes.
#      Uses the 'worker' DB alias (sdta_migration, BYPASSRLS) so staff can
#      read and write across all tenants without RLS filtering.
#   2. StaffUserAdmin — manages ServizDesk staff accounts.

import uuid
from datetime import date, datetime
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.forms.models import model_to_dict

from infrastructure.models import SystemAudits
from staff.models import StaffUser


# ─── Base Admin Mixin ─────────────────────────────────────────────────────────

class TenantModelAdmin(admin.ModelAdmin):
    """
    Base class for all SDTA model admins.

    Switches every queryset, save, and delete operation to the 'worker'
    database alias, which connects as sdta_migration (BYPASSRLS=TRUE).
    This allows ServizDesk staff to view and modify all tenant data
    without being blocked by PostgreSQL Row-Level Security.

    All tenant model admin classes must inherit from this instead of
    admin.ModelAdmin directly.

    Adds tenant_id to list_display and list_filter so staff can filter
    by tenant when investigating issues.
    """

    # Show tenant_id in list views so staff can identify which tenant a
    # record belongs to at a glance.
    list_display = ('__str__', 'tenant_id')
    list_filter = ('tenant_id',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
    staff_view_groups = {'support', 'ops', 'engineering'}
    staff_write_groups = {'ops', 'engineering'}
    staff_delete_groups = {'engineering'}

    @staticmethod
    def _normalize_for_json(value):
        if isinstance(value, (datetime, date, uuid.UUID, Decimal)):
            return str(value)
        if isinstance(value, dict):
            return {
                key: TenantModelAdmin._normalize_for_json(val)
                for key, val in value.items()
            }
        if isinstance(value, list):
            return [TenantModelAdmin._normalize_for_json(item) for item in value]
        return value

    def _model_label(self):
        opts = self.model._meta
        if opts.app_label == 'inventory' and opts.model_name == 'inventoryitem':
            # Backward-compatible label expected by existing audit/report consumers.
            return 'inventory.product'
        return f'{opts.app_label}.{opts.model_name}'

    def _staff_groups(self, request):
        return {
            name.lower()
            for name in request.user.groups.values_list('name', flat=True)
        }

    def _can_view_staff_data(self, request):
        user = request.user
        if not user.is_authenticated or not user.is_active or not user.is_staff:
            return False
        if user.is_superuser:
            return True
        groups = self._staff_groups(request)
        return bool(groups.intersection(self.staff_view_groups))

    def _can_write_staff_data(self, request):
        user = request.user
        if user.is_superuser:
            return True
        groups = self._staff_groups(request)
        if groups.intersection(self.staff_write_groups):
            return True
        return user.has_perm(
            f'{self.model._meta.app_label}.change_{self.model._meta.model_name}'
        )

    def _can_delete_staff_data(self, request):
        user = request.user
        if user.is_superuser:
            return True
        groups = self._staff_groups(request)
        if groups.intersection(self.staff_delete_groups):
            return True
        return user.has_perm(f'{self.model._meta.app_label}.delete_{self.model._meta.model_name}')

    def has_module_permission(self, request):
        return self._can_view_staff_data(request)

    def has_view_permission(self, request, obj=None):
        return self._can_view_staff_data(request)

    def has_change_permission(self, request, obj=None):
        return self._can_write_staff_data(request)

    def has_add_permission(self, request):
        return self._can_write_staff_data(request)

    def has_delete_permission(self, request, obj=None):
        return self._can_delete_staff_data(request)

    def _build_snapshot(self, obj):
        if not obj:
            return None
        data = model_to_dict(obj)
        data['id'] = str(getattr(obj, 'pk', ''))
        return self._normalize_for_json(data)

    def _write_staff_audit(self, *, tenant_id, action, request, obj=None, before=None, after=None):
        if self.model is SystemAudits:
            return
        object_id = None
        raw_pk = getattr(obj, 'pk', None)
        if isinstance(raw_pk, uuid.UUID):
            object_id = raw_pk
        elif raw_pk:
            try:
                object_id = uuid.UUID(str(raw_pk))
            except (ValueError, TypeError):
                object_id = None
        reason = request.POST.get('_staff_reason', '').strip()
        reason_text = reason or 'No reason provided.'
        SystemAudits.all_objects.using('worker').create(
            tenant_id=tenant_id,
            actor=None,
            action=action,
            model_name=self._model_label(),
            object_id=object_id,
            before_snapshot=before,
            after_snapshot=after,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            created_by=f'{request.user.email} | reason={reason_text}',
            updated_by=request.user.email,
        )

    def get_queryset(self, request):
        """Use worker alias — bypasses RLS, returns all tenant rows."""
        return super().get_queryset(request).using('worker')

    def save_model(self, request, obj, form, change):
        """
        Save via worker alias.
        tenant_id must already be set on the object (comes from the DB for
        edits, or must be supplied in the admin form for new records).
        If tenant_id is missing on a new record, raise a clear error.
        """
        if not obj.tenant_id:
            raise ValueError(
                "tenant_id is required. Set it in the admin form before saving."
            )
        existing = None
        should_audit = isinstance(obj, self.model)
        if should_audit and change and getattr(obj, 'pk', None):
            read_alias = getattr(getattr(obj, '_state', None), 'db', None) or 'worker'
            existing = self.model.all_objects.using(read_alias).filter(pk=obj.pk).first()
        before_snapshot = self._build_snapshot(existing)
        obj.save(using='worker')
        if should_audit:
            after_snapshot = self._build_snapshot(obj)
            self._write_staff_audit(
                tenant_id=obj.tenant_id,
                action='staff_admin_update' if change else 'staff_admin_create',
                request=request,
                obj=obj,
                before=before_snapshot,
                after=after_snapshot,
            )

    def delete_model(self, request, obj):
        should_audit = isinstance(obj, self.model)
        before_snapshot = self._build_snapshot(obj)
        obj_tenant = getattr(obj, 'tenant_id', None)
        obj_id = obj.pk
        obj.delete(using='worker')
        if should_audit:
            self._write_staff_audit(
                tenant_id=obj_tenant,
                action='staff_admin_delete',
                request=request,
                obj=type('DeletedObjRef', (), {'pk': obj_id})(),
                before=before_snapshot,
                after=None,
            )

    def delete_queryset(self, request, queryset):
        to_delete = list(queryset.using('worker'))
        queryset.using('worker').delete()
        for obj in to_delete:
            self._write_staff_audit(
                tenant_id=obj.tenant_id,
                action='staff_admin_bulk_delete',
                request=request,
                obj=obj,
                before=self._build_snapshot(obj),
                after=None,
            )

    def get_object(self, request, object_id, from_field=None):
        """Fetch single objects via worker alias."""
        queryset = self.get_queryset(request)
        model = queryset.model
        field = (
            model._meta.pk if from_field is None
            else model._meta.get_field(from_field)
        )
        try:
            object_id = field.to_python(object_id)
            return queryset.get(**{field.name: object_id})
        except (model.DoesNotExist, ValueError, TypeError):
            return None


# ─── StaffUser Admin ──────────────────────────────────────────────────────────

@admin.register(StaffUser)
class StaffUserAdmin(UserAdmin):
    """
    Admin for ServizDesk internal staff accounts.
    No tenant scoping — staff accounts are global.
    """
    model = StaffUser
    list_display = ('email', 'name', 'is_active', 'is_superuser', 'created_at')
    list_filter = ('is_active', 'is_superuser')
    search_fields = ('email', 'name')
    ordering = ('email',)
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Personal', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'groups', 'user_permissions')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2',
                       'is_active', 'is_superuser'),
        }),
    )
