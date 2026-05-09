# users/api.py
# REST API serializers and viewsets for users app models.
#
# Models:
#   User (custom, not TenantModel), Department, Position, Role,
#   EmployeeRole, EmployeePosition, RolePermission, TenantPreference,
#   EmployeePreference, SessionLog, LoginAttemptLog, EmployeeZone

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, TenantNoDeleteViewSet, ReadOnlyTenantViewSet
from .models import (
    User, Department, Position, Role, EmployeeRole, EmployeePosition,
    RolePermission, TenantPreference, EmployeePreference, SessionLog,
    LoginAttemptLog, EmployeeZone
)


# ─── User (Custom Serializer — NOT TenantModel) ────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    person_display = serializers.CharField(source='person.name', read_only=True)
    department_display = serializers.CharField(source='department.name', read_only=True)
    position_display = serializers.CharField(source='position.title', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'tenant_id',
            'person',
            'person_display',
            'department',
            'department_display',
            'position',
            'position_display',
            'prev_employee',
            'email',
            'employee_number',
            'status',
            'hire_date',
            'termination_date',
            'failed_login_count',
            'force_password_change',
            'mfa_enabled',
            'mfa_phone',
            'mfa_exempt',
            'is_active',
            'is_tenant_admin',
            'created_by',
            'created_on',
            'updated_by',
            'updated_on',
        ]
        read_only_fields = [
            'id',
            'employee_number',
            'person_display',
            'department_display',
            'position_display',
            'created_by',
            'created_on',
            'updated_by',
            'updated_on',
        ]

    def validate_is_tenant_admin(self, value):
        """Only existing tenant admins can grant/revoke admin status."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if not getattr(request.user, 'is_tenant_admin', False):
                # If the user is not an admin, they cannot change this field.
                # If they are creating a user, they might not be able to set it either.
                if self.instance and self.instance.is_tenant_admin != value:
                    raise serializers.ValidationError("Only tenant administrators can change this field.")
                elif not self.instance and value:
                    raise serializers.ValidationError("Only tenant administrators can create new admin users.")
        return value

    def to_representation(self, instance):
        """Remove password field from output."""
        ret = super().to_representation(instance)
        # Password is AbstractBaseUser field and should never be exposed
        return ret


class UserViewSet(TenantModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = ['status', 'department_id', 'position_id', 'is_active']
    search_fields = ['email', 'employee_number', 'person__name']
    ordering_fields = ['email', 'hire_date', 'created_on', 'status']


# ─── Department ───────────────────────────────────────────────────────────────

class DepartmentSerializer(TenantModelSerializer):

    class Meta:
        model = Department
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class DepartmentViewSet(TenantModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filterset_fields = ['status']
    search_fields = ['name']
    ordering_fields = ['name', 'created_on', 'status']


# ─── Position ─────────────────────────────────────────────────────────────────

class PositionSerializer(TenantModelSerializer):
    department_display = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Position
        fields = TenantModelSerializer.Meta.fields + [
            'department',
            'department_display',
            'title',
            'description',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'department_display',
        ]


class PositionViewSet(TenantModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    filterset_fields = ['department_id', 'status']
    search_fields = ['title']
    ordering_fields = ['title', 'created_on', 'status']


# ─── Role ─────────────────────────────────────────────────────────────────────

class RoleSerializer(TenantModelSerializer):

    class Meta:
        model = Role
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'is_custom',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class RoleViewSet(TenantModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_on']


# ─── EmployeeRole ────────────────────────────────────────────────────────────

class EmployeeRoleSerializer(TenantModelSerializer):
    employee_display = serializers.CharField(source='employee.email', read_only=True)
    role_display = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = EmployeeRole
        fields = TenantModelSerializer.Meta.fields + [
            'employee',
            'employee_display',
            'role',
            'role_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'employee_display',
            'role_display',
        ]


class EmployeeRoleViewSet(TenantModelViewSet):
    queryset = EmployeeRole.objects.all()
    serializer_class = EmployeeRoleSerializer
    filterset_fields = ['employee_id', 'role_id']
    search_fields = ['employee__email', 'role__name']
    ordering_fields = ['created_on']


# ─── EmployeePosition ─────────────────────────────────────────────────────────

class EmployeePositionSerializer(TenantModelSerializer):
    employee_display = serializers.CharField(source='employee.email', read_only=True)
    position_display = serializers.CharField(source='position.title', read_only=True)

    class Meta:
        model = EmployeePosition
        fields = TenantModelSerializer.Meta.fields + [
            'employee',
            'employee_display',
            'position',
            'position_display',
            'is_primary',
            'start_date',
            'end_date',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'employee_display',
            'position_display',
        ]


class EmployeePositionViewSet(TenantModelViewSet):
    queryset = EmployeePosition.objects.all()
    serializer_class = EmployeePositionSerializer
    filterset_fields = ['employee_id', 'position_id', 'is_primary']
    search_fields = ['employee__email', 'position__title']
    ordering_fields = ['start_date', 'created_on']


# ─── RolePermission ───────────────────────────────────────────────────────────

class RolePermissionSerializer(TenantModelSerializer):
    role_display = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = RolePermission
        fields = TenantModelSerializer.Meta.fields + [
            'role',
            'role_display',
            'resource_key',
            'can_create',
            'can_view',
            'can_edit',
            'can_delete',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'role_display',
        ]


class RolePermissionViewSet(TenantModelViewSet):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    filterset_fields = ['role_id', 'resource_key']
    search_fields = ['resource_key', 'role__name']
    ordering_fields = ['created_on']


# ─── TenantPreference ─────────────────────────────────────────────────────────

class TenantPreferenceSerializer(TenantModelSerializer):

    class Meta:
        model = TenantPreference
        fields = TenantModelSerializer.Meta.fields + [
            'company_name',
            'company_logo',
            'address',
            'city',
            'state',
            'zip',
            'country',
            'phone',
            'fax',
            'email',
            'website',
            'default_currency',
            'currency_symbol',
            'decimal_precision',
            'timezone',
            'date_format',
            'phone_country_code',
            'phone_format',
            'default_tax_rate',
            'tax_label',
            'default_payment_terms',
            'default_quote_expiration_days',
            'fiscal_year_start_month',
            'numbering_reset_period',
            'customer_prefix',
            'customer_start_number',
            'asset_prefix',
            'asset_start_number',
            'work_order_prefix',
            'work_order_start_number',
            'quote_prefix',
            'quote_start_number',
            'invoice_prefix',
            'invoice_start_number',
            'payment_prefix',
            'payment_start_number',
            'task_prefix',
            'task_start_number',
            'product_prefix',
            'product_start_number',
            'employee_prefix',
            'employee_start_number',
            'service_request_prefix',
            'service_request_start_number',
            'work_group_prefix',
            'work_group_start_number',
            'po_prefix',
            'po_start_number',
            'vehicle_prefix',
            'vehicle_start_number',
            'custom_email_domain',
            'domain_verification_status',
            'postmark_domain_id',
            'mfa_required',
            'session_timeout_minutes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class TenantPreferenceViewSet(ReadOnlyTenantViewSet):
    queryset = TenantPreference.objects.all()
    serializer_class = TenantPreferenceSerializer
    filterset_fields = []
    search_fields = ['company_name']
    ordering_fields = ['created_on']


# ─── EmployeePreference ───────────────────────────────────────────────────────

class EmployeePreferenceSerializer(TenantModelSerializer):
    user_display = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = EmployeePreference
        fields = TenantModelSerializer.Meta.fields + [
            'user',
            'user_display',
            'ui_theme',
            'default_landing_page',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'user_display',
        ]


class EmployeePreferenceViewSet(TenantModelViewSet):
    queryset = EmployeePreference.objects.all()
    serializer_class = EmployeePreferenceSerializer
    filterset_fields = ['user_id', 'ui_theme']
    search_fields = ['user__email']
    ordering_fields = ['created_on']


# ─── SessionLog ───────────────────────────────────────────────────────────────

class SessionLogSerializer(TenantModelSerializer):
    user_display = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = SessionLog
        fields = TenantModelSerializer.Meta.fields + [
            'user',
            'user_display',
            'session_id',
            'login_at',
            'logout_at',
            'expiration_at',
            'ip_address',
            'user_agent',
            'permission_snapshot',
            'browser',
            'os',
            'device_type',
            'mfa_used',
            'mfa_method',
            'force_logout_at',
            'force_logout_by',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'user_display',
        ]


class SessionLogViewSet(ReadOnlyTenantViewSet):
    queryset = SessionLog.objects.all()
    serializer_class = SessionLogSerializer
    filterset_fields = ['user_id', 'device_type', 'mfa_used']
    search_fields = ['user__email', 'ip_address']
    ordering_fields = ['login_at', 'created_on']


# ─── LoginAttemptLog ──────────────────────────────────────────────────────────

class LoginAttemptLogSerializer(TenantModelSerializer):

    class Meta:
        model = LoginAttemptLog
        fields = TenantModelSerializer.Meta.fields + [
            'user_email',
            'ip_address',
            'user_agent',
            'success',
            'failure_reason',
            'mfa_attempted',
            'attempted_at',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class LoginAttemptLogViewSet(ReadOnlyTenantViewSet):
    queryset = LoginAttemptLog.objects.all()
    serializer_class = LoginAttemptLogSerializer
    filterset_fields = ['success', 'failure_reason']
    search_fields = ['user_email', 'ip_address']
    ordering_fields = ['attempted_at']


# ─── EmployeeZone ────────────────────────────────────────────────────────────

class EmployeeZoneSerializer(TenantModelSerializer):
    zone_display = serializers.CharField(source='zone.name', read_only=True)
    employee_display = serializers.CharField(source='employee.email', read_only=True)

    class Meta:
        model = EmployeeZone
        fields = TenantModelSerializer.Meta.fields + [
            'zone',
            'zone_display',
            'employee',
            'employee_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'zone_display',
            'employee_display',
        ]


class EmployeeZoneViewSet(TenantModelViewSet):
    queryset = EmployeeZone.objects.all()
    serializer_class = EmployeeZoneSerializer
    filterset_fields = ['zone_id', 'employee_id']
    search_fields = ['zone__name', 'employee__email']
    ordering_fields = ['created_on']


# ─── Router ───────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'employee-roles', EmployeeRoleViewSet, basename='employee-role')
router.register(r'employee-positions', EmployeePositionViewSet, basename='employee-position')
router.register(r'role-permissions', RolePermissionViewSet, basename='role-permission')
router.register(r'tenant-preferences', TenantPreferenceViewSet, basename='tenant-preference')
router.register(r'employee-preferences', EmployeePreferenceViewSet, basename='employee-preference')
router.register(r'session-logs', SessionLogViewSet, basename='session-log')
router.register(r'login-attempt-logs', LoginAttemptLogViewSet, basename='login-attempt-log')
router.register(r'employee-zones', EmployeeZoneViewSet, basename='employee-zone')
