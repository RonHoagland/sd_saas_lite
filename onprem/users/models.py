# users/models.py
# Source: Data Models V6, Section 1.1.
# AUTH_USER_MODEL = 'users.User'
#
# User extends AbstractBaseUser directly (required by Django auth framework).
# All other models extend TenantModel and inherit audit fields from the base.

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from crm.models import Person
from config.base_models import TenantModel
from config.tenant_context import get_current_tenant_id
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


# ─── User ─────────────────────────────────────────────────────────────────────

class UserManager(BaseUserManager):

    def get_queryset(self):
        tenant_id = get_current_tenant_id()
        qs = super().get_queryset()
        if tenant_id:
            return qs.filter(tenant_id=tenant_id)
        return qs

    def create_user(self, username, tenant_id=None, password=None, email='', **extra_fields):
        """
        Create a tenant user. Login identifier is the tenant subdomain + username.

        Username uniqueness is per-tenant (see Meta.unique_together). Two tenants
        may each have a user named `admin`. The DB raises IntegrityError on a
        within-tenant collision; callers must handle or pre-validate.
        """
        if not username:
            raise ValueError("Username is required.")
        if not email:
            raise ValueError("Email is required.")
        username = str(username).strip().lower()
        if '@' in username:
            raise ValueError(
                "Username must not contain '@'. Use a separate email address field."
            )

        normalized_email = self.normalize_email(email)

        if not tenant_id:
            tenant_id = get_current_tenant_id() or uuid.uuid4()

        person = extra_fields.pop('person', None)
        if person is None:
            person = Person.all_objects.create(
                tenant_id=tenant_id,
                first_name=extra_fields.pop('first_name', 'System'),
                last_name=extra_fields.pop('last_name', 'User'),
                created_by='system',
                updated_by='system',
            )

        user = self.model(username=username, email=normalized_email,
                          tenant_id=tenant_id, person=person, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, email=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_tenant_admin', True)
        if not email:
            raise ValueError("Email is required.")
        return self.create_user(
            username, password=password, email=email, **extra_fields
        )


class User(AbstractBaseUser, NumberingMixin, LifecycleMixin):
    """
    Tenant employee with system access. Links to Person for name fields.
    Source: Data Models V6, Section 1.1 — User model.
    ERD: Employees entity (Employee V4).
    Django admin authenticates via StaffUserBackend, not this model.

    Note: Cannot extend TenantModel — AbstractBaseUser defines its own id
    and manager machinery. Audit fields are declared explicitly here.
    """
    numbering_entity_type = 'employee'
    lifecycle_entity_type = 'employee'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        ON_LEAVE = 'On Leave', 'On Leave'
        INACTIVE = 'Inactive', 'Inactive'
        TERMINATED = 'Terminated', 'Terminated'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    # Person link — names live on Person, not User.
    person = models.ForeignKey('crm.Person', on_delete=models.PROTECT,
                               related_name='users')
    department = models.ForeignKey('users.Department', null=True, blank=True,
                                   on_delete=models.SET_NULL)
    position = models.ForeignKey('users.Position', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='primary_users')
    prev_employee = models.ForeignKey('self', null=True, blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name='rehired_as')

    # Username + email are unique PER TENANT, not globally. Two tenants may each
    # have a user named `admin` with email `admin@example.com`. Login resolves the
    # tenant first (workspace field on the splash form), then looks up the user
    # within that tenant. See LITE_DECISIONS.md §N.
    username = models.CharField(max_length=150)
    email = models.EmailField()
    employee_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                              default=StatusChoices.ACTIVE)
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    failed_login_count = models.IntegerField(default=0)
    is_tenant_admin = models.BooleanField(default=False)
    force_password_change = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
    mfa_phone = models.CharField(max_length=30, blank=True)
    mfa_exempt = models.BooleanField(default=False)

    # Audit fields — explicit here because User cannot extend TenantModel.
    created_by = models.CharField(max_length=200, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=200, blank=True)
    updated_on = models.DateTimeField(auto_now=True)

    # Required by AbstractBaseUser
    is_active = models.BooleanField(default=True)
    # Tenant users never have Django admin access — that is StaffUser only.
    is_staff = models.BooleanField(default=False)
    # Not PermissionsMixin — tenant users have no Django permissions framework access.
    is_superuser = False

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    # Note: Django emits auth.W004 because USERNAME_FIELD is not globally unique.
    # That is intentional — ServizDesk uses workspace-scoped uniqueness, see
    # LITE_DECISIONS.md §N. The warning is silenced via SILENCED_SYSTEM_CHECKS
    # in settings.py.

    objects = UserManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'users_user'
        unique_together = [
            ('tenant_id', 'username'),
            ('tenant_id', 'email'),
        ]
        indexes = [
            models.Index(fields=['tenant_id']),
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'username']),
        ]

    def __str__(self):
        return f'{self.username} ({self.tenant_id})'

    def has_perm(self, perm, obj=None):
        return False

    def has_module_perms(self, app_label):
        return False


# ─── Supporting models — all extend TenantModel ───────────────────────────────

class Department(TenantModel):
    """Source: Data Models V6, Section 1.1."""

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                              default=StatusChoices.ACTIVE)

    class Meta:
        db_table = 'users_department'

    def __str__(self):
        return self.name


class Position(TenantModel):
    """Source: Data Models V6, Section 2.6."""

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                              default=StatusChoices.ACTIVE)

    class Meta:
        db_table = 'users_position'

    def __str__(self):
        return self.title


class Role(TenantModel):
    """Source: Data Models V6, Section 1.1."""

    name = models.CharField(max_length=100)
    is_custom = models.BooleanField(default=False)

    class Meta:
        db_table = 'users_role'

    def __str__(self):
        return self.name


class EmployeeRole(TenantModel):
    """Junction: User ↔ Role. Source: Data Models V6, Section 1.1."""

    employee = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='employee_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        db_table = 'users_employeerole'
        unique_together = [('tenant_id', 'employee', 'role')]

    def __str__(self):
        return f'{self.employee} → {self.role}'


class EmployeePosition(TenantModel):
    """Junction: User ↔ Position. Source: Data Models V6, Section 1.1."""

    employee = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='employee_positions')
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'users_employeeposition'

    def __str__(self):
        return f'{self.employee} → {self.position}'


class RolePermission(TenantModel):
    """Granular CRUD permissions per Role. Source: Data Models V6, Section 1.1."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE,
                             related_name='permissions')
    resource_key = models.CharField(max_length=100)
    can_create = models.BooleanField(default=False)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'users_rolepermission'
        unique_together = [('tenant_id', 'role', 'resource_key')]

    def __str__(self):
        return f'{self.role} — {self.resource_key}'


class TenantPreference(TenantModel):
    """Global settings for the tenant. One per tenant.
    Source: Data Models V6, Section 1.1."""

    class DateFormatChoices(models.TextChoices):
        MDY = 'MM/DD/YYYY', 'MM/DD/YYYY'
        DMY = 'DD/MM/YYYY', 'DD/MM/YYYY'
        YMD = 'YYYY-MM-DD', 'YYYY-MM-DD'

    class PaymentTermsChoices(models.TextChoices):
        DUE_ON_RECEIPT = 'Due on Receipt', 'Due on Receipt'
        NET_15 = 'Net 15', 'Net 15'
        NET_30 = 'Net 30', 'Net 30'
        NET_45 = 'Net 45', 'Net 45'
        NET_60 = 'Net 60', 'Net 60'
        CUSTOM = 'Custom', 'Custom'

    class DomainVerificationChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        VERIFIED = 'Verified', 'Verified'
        FAILED = 'Failed', 'Failed'

    # tenant_id is unique here — one preference record per tenant
    # Override the base index with a unique constraint
    tenant_id = models.UUIDField(unique=True, db_index=True)

    company_name = models.CharField(max_length=200, blank=True, default='')
    company_logo = models.FileField(upload_to='logos/', blank=True)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    fax = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    default_currency = models.CharField(max_length=3, default='USD')
    currency_symbol = models.CharField(max_length=5, default='$')
    decimal_precision = models.IntegerField(default=2)
    timezone = models.CharField(max_length=100, default='UTC')
    date_format = models.CharField(max_length=20, choices=DateFormatChoices.choices,
                                   default=DateFormatChoices.MDY)
    phone_country_code = models.CharField(max_length=5, default='+1')
    phone_format = models.CharField(max_length=20, blank=True)
    default_tax_rate = models.DecimalField(max_digits=7, decimal_places=4, default=0)
    tax_label = models.CharField(max_length=50, default='Sales Tax')
    default_payment_terms = models.CharField(max_length=20,
                                              choices=PaymentTermsChoices.choices,
                                              default=PaymentTermsChoices.DUE_ON_RECEIPT)
    default_quote_expiration_days = models.IntegerField(default=30)
    fiscal_year_start_month = models.IntegerField(default=1)
    numbering_reset_period = models.CharField(max_length=10, default='Never')
    # Numbering prefixes
    customer_prefix = models.CharField(max_length=10, default='C')
    customer_start_number = models.IntegerField(default=1)
    asset_prefix = models.CharField(max_length=10, default='A')
    asset_start_number = models.IntegerField(default=1)
    work_order_prefix = models.CharField(max_length=10, default='W')
    work_order_start_number = models.IntegerField(default=1)
    quote_prefix = models.CharField(max_length=10, default='Q')
    quote_start_number = models.IntegerField(default=1)
    invoice_prefix = models.CharField(max_length=10, default='I')
    invoice_start_number = models.IntegerField(default=1)
    payment_prefix = models.CharField(max_length=10, default='P')
    payment_start_number = models.IntegerField(default=1)
    task_prefix = models.CharField(max_length=10, default='T')
    task_start_number = models.IntegerField(default=1)
    product_prefix = models.CharField(max_length=10, default='XT')
    product_start_number = models.IntegerField(default=1)
    employee_prefix = models.CharField(max_length=10, default='E')
    employee_start_number = models.IntegerField(default=1)
    service_request_prefix = models.CharField(max_length=10, default='SR')
    service_request_start_number = models.IntegerField(default=1)
    work_group_prefix = models.CharField(max_length=10, default='WG')
    work_group_start_number = models.IntegerField(default=1)
    po_prefix = models.CharField(max_length=10, default='PO')
    po_start_number = models.IntegerField(default=1)
    vehicle_prefix = models.CharField(max_length=10, default='VS')
    vehicle_start_number = models.IntegerField(default=1)
    # Custom email domain (Pro/Enterprise add-on)
    custom_email_domain = models.CharField(max_length=200, blank=True)
    domain_verification_status = models.CharField(
        max_length=20, choices=DomainVerificationChoices.choices,
        blank=True)
    postmark_domain_id = models.CharField(max_length=100, blank=True)
    # Security
    mfa_required = models.BooleanField(default=False)
    session_timeout_minutes = models.IntegerField(default=30)

    class Meta:
        db_table = 'users_tenantpreference'

    def __str__(self):
        return f'{self.company_name} prefs'


class EmployeePreference(TenantModel):
    """Per-employee UI settings. Source: Data Models V6, Section 1.1."""

    class ThemeChoices(models.TextChoices):
        LIGHT = 'Light', 'Light'
        DARK = 'Dark', 'Dark'
        SYSTEM = 'System', 'System'

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='preferences')
    ui_theme = models.CharField(max_length=10, choices=ThemeChoices.choices,
                                default=ThemeChoices.SYSTEM)
    default_landing_page = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'users_employeepreference'

    def __str__(self):
        return f'{self.user} prefs'


class SessionLog(TenantModel):
    """Authenticated session record. Source: Data Models V6, Section 1.1."""

    class DeviceTypeChoices(models.TextChoices):
        MOBILE = 'Mobile', 'Mobile'
        DESKTOP = 'Desktop', 'Desktop'

    class MFAMethodChoices(models.TextChoices):
        SMS = 'SMS', 'SMS'
        EMAIL = 'Email', 'Email'

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                             related_name='sessions')
    session_id = models.CharField(max_length=200, unique=True)
    login_at = models.DateTimeField()
    logout_at = models.DateTimeField(null=True, blank=True)
    expiration_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    permission_snapshot = models.JSONField(default=dict, blank=True)
    browser = models.CharField(max_length=200, blank=True)
    os = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=10, choices=DeviceTypeChoices.choices,
                                   blank=True)
    mfa_used = models.BooleanField(default=False)
    mfa_method = models.CharField(max_length=10, choices=MFAMethodChoices.choices,
                                  blank=True)
    force_logout_at = models.DateTimeField(null=True, blank=True)
    force_logout_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='forced_logouts')

    class Meta:
        db_table = 'users_sessionlog'
        indexes = [
            models.Index(fields=['tenant_id', 'user_id']),
        ]

    def __str__(self):
        return f'Session {self.session_id[:8]}… ({self.tenant_id})'


class LoginAttemptLog(TenantModel):
    """
    Immutable login attempt record. Source: Data Models V6, Section 1.1.
    tenant_id is a plain UUID (not a FK) so this record survives tenant deletion.
    """

    class FailureReasonChoices(models.TextChoices):
        INVALID_PASSWORD = 'invalid_password', 'Invalid Password'
        ACCOUNT_LOCKED = 'account_locked', 'Account Locked'
        MFA_FAILED = 'mfa_failed', 'MFA Failed'
        MFA_EXPIRED = 'mfa_expired', 'MFA Expired'
        UNKNOWN_USER = 'unknown_user', 'Unknown User'

    user_email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField()
    failure_reason = models.CharField(max_length=30,
                                      choices=FailureReasonChoices.choices,
                                      blank=True)
    mfa_attempted = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_loginattemptlog'

    def __str__(self):
        return f'{self.user_email} {"✓" if self.success else "✗"} @ {self.attempted_at}'


# ─── Service Territory ─────────────────────────────────────────────────────────

class EmployeeZone(TenantModel):
    """
    Junction assigning employees to service coverage zones.
    An employee may cover multiple zones.
    Source: Data Models V6, Section 3.6 (Enterprise).
    """

    zone = models.ForeignKey('automation.TerritoryZone', on_delete=models.CASCADE,
                              related_name='assigned_employees')
    employee = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='zone_assignments')

    class Meta:
        db_table = 'users_employeezone'
        unique_together = [('tenant_id', 'zone', 'employee')]
        indexes = [
            models.Index(fields=['tenant_id', 'zone_id']),
            models.Index(fields=['tenant_id', 'employee_id']),
        ]

    def __str__(self):
        return f'{self.employee} → {self.zone}'
