# ServizmaDesk SDTA — Agent Handoff Document
**Date:** March 2026
**Status:** Ready for Implementation
**Scope:** ServizmaDesk Tenant App (SDTA) — Django 5.x Backend

---

## HOW TO USE THIS DOCUMENT

This document is the single authoritative source for building the SDTA Django backend. It consolidates and supersedes all individual specification documents for implementation purposes. When this document conflicts with any individual spec, **this document wins** — it represents the final reconciled decisions.

Source specifications used to produce this document:
- ServizmaDesk Data Models V4 (primary field reference)
- ServizmaDesk Database Specification V2 (constraints, indexes, RLS)
- ServizmaDesk Technical Architecture V2 (stack decisions)
- ServizmaDesk Multi-Tenancy Specification V1 (implementation code)
- ServizmaDesk Permission Management Specification V2 (RBAC)
- ServizmaDesk Background Tasks Specification V2 (Celery inventory)
- ServizmaDesk System Status Specification V3 (lifecycle rules)
- ServizmaDesk Top-Down Specifications V4 (functional scope)
- ServizmaDesk Invoice Calculation Specification V1
- ServizmaDesk File Upload Specification V1
- ServizmaDesk Onboarding Triggers Specification V2
- ServizmaDesk Stripe Webhook Specification V1

---

# PART 1 — ARCHITECTURAL MANDATES

These rules are absolute. No exceptions. Any code that violates these mandates must be rejected.

| # | Mandate | Detail |
|---|---|---|
| M1 | **PostgreSQL 16+ only** | SQLite is prohibited in ALL environments including local dev |
| M2 | **UUIDv4 primary keys everywhere** | Auto-incrementing integers are strictly prohibited |
| M3 | **`tenant_id` on every tenant-scoped table** | Non-nullable UUID on every SDTA model except Django system tables and `User` |
| M4 | **No Generic Foreign Keys** | Django's content-types framework is prohibited. Use explicit nullable FKs |
| M5 | **Hard delete by default** | Soft delete (`is_deleted` flag) is prohibited unless explicitly specified in a lifecycle rule |
| M6 | **No raw card data** | PCI SAQ A compliance. Stripe handles all card data |
| M7 | **All timestamps in UTC** | `TIMESTAMPTZ` in PostgreSQL. Display conversion at UI layer via `TenantPreference.timezone` |
| M8 | **No hardcoded secrets** | All secrets via `python-decouple` environment variables |
| M9 | **Fat models, thin views** | Business logic lives in `models.py` or `services.py`, never in views |
| M10 | **HTMX v2.x only for dynamic interactions** | Alpine.js and Hyperscript are explicitly prohibited |
| M11 | **Tailwind CSS only** | Vanilla CSS permitted only for extreme edge cases |
| M12 | **Monetary values as NUMERIC(12,2)** | Never use float for money |
| M13 | **Isolated line item tables** | `QuoteLine`, `WorkOrderLine`, `InvoiceLine`, `PurchaseOrderLine`, `RequisitionLine` are separate tables — no shared generic line item table |
| M14 | **One Asset per Work Order** | Multi-asset coordination is handled via WorkGroups only |
| M15 | **No cross-database queries** | SDP and SDTA communicate exclusively via the Internal REST API |

---

# PART 2 — TECHNOLOGY STACK

| Component | Selection |
|---|---|
| Language | Python 3.12+ |
| Framework | Django 5.x |
| Database | PostgreSQL 16+ |
| Task Queue | Celery + Redis |
| Cache / Broker | Redis (managed DigitalOcean instance) |
| File Storage | DigitalOcean Spaces (S3-compatible) via `django-storages` + `boto3` |
| Email | Postmark via Postmark Python SDK |
| SMS | Twilio |
| Payments | Stripe (Connect Standard for tenant payments) |
| PDF (Plus+) | WeasyPrint |
| PDF (Lite) | CSS `@media print` |
| Config | `python-decouple` |
| Web Server | Gunicorn + Nginx |
| Monitoring | Sentry |

---

# PART 3 — DJANGO PROJECT STRUCTURE

## 3.1 App Layout

```
sdta/
├── config/                  # settings.py, urls.py, wsgi.py, asgi.py
├── apps/
│   ├── users/               # User (Employee), Tenant, Roles, Permissions, Sessions
│   ├── crm/                 # Customer, Person, Contact, Address, Phone, Social, Asset, TroubleCall, Lead, Opportunity
│   ├── service/             # WorkOrder, Quote, Invoice, Payment, WorkGroup, Task, Agreement, PM, ChecklistTemplate
│   ├── inventory/           # Product, BundleItem, Warehouse, SubLocation, LocationAssignedInventory, InventoryCount, InventoryTransfer, Pricebook
│   ├── procurement/         # Vendor, PurchaseOrder, Receiving, VendorBill, VendorPayment, Requisition, RMA
│   ├── finance/             # Ledger, Accounting, Bank, Carrier, InvPriceHistory, Stripe models
│   ├── workflow/            # WorkFlow, WFStep, WFStepToDo, WFTool, WFInventory, WFSafetyForm, SafetyForm, WOSFAnswer
│   ├── fleet/               # Vehicle, VehicleMaintenance, MileageLog, VehicleInventory
│   ├── infrastructure/      # Note, Document, Notification, StatusChangeLog, AuditEvent, SequenceTracker, StorageTracker, SystemErrorLog, OnboardingState
│   └── communications/      # CommunicationTemplate, CommunicationTrigger, CommTriggerTemplates, TriggerLog, CustomerPointBase, TriggerPointLog
```

## 3.2 Settings Pattern

```python
# config/settings.py
from decouple import config

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('SDTA_DB_NAME'),
        'USER': config('SDTA_DB_USER'),
        'PASSWORD': config('SDTA_DB_PASSWORD'),
        'HOST': config('SDTA_DB_HOST'),
        'PORT': config('SDTA_DB_PORT', default='5432'),
        'OPTIONS': {'sslmode': config('DB_SSLMODE', default='require')},
        'CONN_MAX_AGE': 60,
    }
}

AUTH_USER_MODEL = 'users.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'apps.users.middleware.TenantMiddleware',   # Must be early
    # ... rest of middleware
]
```

---

# PART 4 — MULTI-TENANCY IMPLEMENTATION

Copy this code exactly. Do not modify the core logic.

## 4.1 Thread-Local Tenant Context

```python
# apps/users/tenant_context.py
from asgiref.local import Local

_thread_locals = Local()

def set_current_tenant_id(tenant_id):
    _thread_locals.tenant_id = tenant_id

def get_current_tenant_id():
    return getattr(_thread_locals, 'tenant_id', None)

def clear_current_tenant_id():
    if hasattr(_thread_locals, 'tenant_id'):
        del _thread_locals.tenant_id
```

## 4.2 Tenant Manager

```python
# apps/users/managers.py
from django.db import models
from .tenant_context import get_current_tenant_id

class TenantManager(models.Manager):
    def get_queryset(self):
        tenant_id = get_current_tenant_id()
        if tenant_id:
            return super().get_queryset().filter(tenant_id=tenant_id)
        return super().get_queryset()
```

## 4.3 Base Tenant Model

```python
# apps/users/models_base.py
import uuid
from django.db import models
from .managers import TenantManager
from .tenant_context import get_current_tenant_id

class TenantModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, editable=False)
    updated_by = models.CharField(max_length=255)

    objects = TenantManager()
    all_objects = models.Manager()  # Bypass for system tasks

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        current_tenant_id = get_current_tenant_id()
        if not self.tenant_id:
            if current_tenant_id:
                self.tenant_id = current_tenant_id
            else:
                raise ValueError("Cannot save TenantModel without a tenant_id in context.")
        if current_tenant_id and self.tenant_id != current_tenant_id:
            raise PermissionError("Tenant ID mismatch: Attempted to save data for a different tenant.")
        super().save(*args, **kwargs)
```

## 4.4 Tenant Middleware

```python
# apps/users/middleware.py
from django.db import connection
from .tenant_context import set_current_tenant_id, clear_current_tenant_id

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            tenant_id = str(request.user.tenant_id)
            set_current_tenant_id(tenant_id)
            with connection.cursor() as cursor:
                # SET LOCAL required for PgBouncer transaction mode
                cursor.execute("SET LOCAL app.current_tenant_id = %s", [tenant_id])
        try:
            response = self.get_response(request)
        finally:
            clear_current_tenant_id()
        return response
```

## 4.5 PostgreSQL RLS Policy (apply to every SDTA table)

```sql
ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON <table_name>
    AS PERMISSIVE FOR ALL TO sdta_app
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);
```

---

# PART 5 — ALL MODEL DEFINITIONS

## IMPORTANT NOTES FOR AGENT

1. All models (except `User`) inherit from `TenantModel`
2. `User` extends `AbstractUser` — it does NOT inherit from `TenantModel`. It is the source of tenant context, not a consumer
3. `tenant_id` on `User` is a plain `UUIDField`, not a FK
4. All monetary fields use `DecimalField(max_digits=12, decimal_places=2)`
5. All percentage/rate fields use `DecimalField(max_digits=7, decimal_places=4)`
6. All enum fields use Django `TextChoices` classes
7. Junction tables (M2M) do NOT carry `created_by`/`updated_by` unless specified
8. `created_by` and `updated_by` are `CharField(max_length=255)` — they store the string name/ID of who acted, not a FK, for immutable audit purposes
9. `Note` and `Document` models use the Exclusive Arc pattern — exactly one parent FK populated, enforced by DB CHECK constraint
10. `Contact`, `Address`, `Phone` use Exclusive Arc — exactly one parent FK populated

---

## 5.1 APP: `users/`

### `User` (extends AbstractUser)

```python
# AUTH_USER_MODEL = 'users.User'
# USERNAME_FIELD = 'email'
# Removes default 'username' field

class UserStatus(models.TextChoices):
    ACTIVE = 'Active'
    ON_LEAVE = 'On Leave'
    INACTIVE = 'Inactive'
    TERMINATED = 'Terminated'

class User(AbstractUser):
    # Remove username — email is the login credential
    username = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True, editable=False)  # Plain field, NOT FK
    # first_name and last_name inherited from AbstractUser
    email = models.EmailField(unique=False)  # Unique per tenant enforced via Meta unique_together
    employee_number = models.CharField(max_length=20)  # Auto-generated E26-0001
    status = models.CharField(max_length=20, choices=UserStatus.choices, default=UserStatus.ACTIVE)
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    profile_photo = models.FileField(upload_to='profiles/', null=True, blank=True)
    failed_login_count = models.IntegerField(default=0)
    force_password_change = models.BooleanField(default=False)
    prev_employee_id = models.UUIDField(null=True, blank=True)  # Self-ref to prior employment record
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        unique_together = [('tenant_id', 'email'), ('tenant_id', 'employee_number')]

    # Seat billing rule: Active + On Leave + Inactive count against seats. Terminated does not.
    # Lite tier cap: Active + On Leave + Inactive <= 10
    # Account locks when failed_login_count >= 5
```

### `UserPreference`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `user_id` | UUID FK → User | Unique |
| `ui_theme` | Enum | Light, Dark, System |
| `default_landing_page` | CharField | |
| audit fields | | |

### `Department`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `name` | CharField(255) | Required |
| `status` | Enum | Active, Inactive |
| audit fields | | |

### `EmployeeDepartment` (junction — Employee ↔ Department, many-to-many)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `employee_id` | UUID FK → User | |
| `department_id` | UUID FK → Department | |

### `Position`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `department_id` | UUID FK → Department | Required |
| `title` | CharField(255) | |
| `description` | TextField | |
| `status` | Enum | Active, Inactive |
| audit fields | | |

### `EmployeePosition` (junction — Employee ↔ Position, many-to-many)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `employee_id` | UUID FK → User | |
| `position_id` | UUID FK → Position | |

### `Role`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `name` | CharField(100) | Administrator, User, Read-Only (system); custom in Pro+ |
| `is_custom` | BooleanField | False for system roles — system roles are immutable |
| audit fields | | |

### `EmployeeRole` (junction — Employee ↔ Role)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `employee_id` | UUID FK → User | |
| `role_id` | UUID FK → Role | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `RolePermission`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `role_id` | UUID FK → Role | |
| `resource_key` | CharField(100) | From Permission Registry (e.g. `service_invoice`) |
| `can_create` | BooleanField | Default False |
| `can_view` | BooleanField | Default False |
| `can_edit` | BooleanField | Default False |
| `can_delete` | BooleanField | Default False |
| audit fields | | |

> Permission logic: Additive union across all employee roles. If ANY role grants a permission, it is granted. No "Deny" concept.

### `TenantPreference` (one per tenant)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Unique |
| `company_name` | CharField(255) | Required |
| `company_logo` | FileField | Object storage |
| `address` | CharField(255) | |
| `city` | CharField(100) | |
| `state` | CharField(100) | |
| `zip` | CharField(20) | |
| `country` | CharField(100) | |
| `phone` | CharField(50) | |
| `fax` | CharField(50) | Optional |
| `email` | EmailField | |
| `website` | URLField | Optional |
| `default_currency` | CharField(10) | e.g. USD |
| `currency_symbol` | CharField(5) | e.g. $ |
| `decimal_precision` | IntegerField | Default: 2 |
| `timezone` | CharField(100) | IANA timezone string |
| `date_format` | Enum | MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD |
| `phone_country_code` | CharField(10) | e.g. +1 |
| `phone_format` | Enum | US, International |
| `default_tax_rate` | DecimalField(7,4) | |
| `tax_label` | CharField(50) | e.g. Sales Tax |
| `default_payment_terms` | Enum | Due on Receipt, Net 15, Net 30, Net 45, Net 60, Custom |
| `default_quote_expiration_days` | IntegerField | Default: 30 |
| `fiscal_year_start_month` | IntegerField | 1-12, Default: 1 |
| `numbering_reset_period` | Enum | Annual, Never |
| `customer_prefix` | CharField(10) | Default: C |
| `customer_start_number` | IntegerField | Default: 1 |
| `asset_prefix` | CharField(10) | Default: A |
| `asset_start_number` | IntegerField | Default: 1 |
| `work_order_prefix` | CharField(10) | Default: W |
| `work_order_start_number` | IntegerField | Default: 1 |
| `quote_prefix` | CharField(10) | Default: Q |
| `quote_start_number` | IntegerField | Default: 1 |
| `invoice_prefix` | CharField(10) | Default: I |
| `invoice_start_number` | IntegerField | Default: 1 |
| `payment_prefix` | CharField(10) | Default: P |
| `payment_start_number` | IntegerField | Default: 1 |
| `task_prefix` | CharField(10) | Default: T |
| `task_start_number` | IntegerField | Default: 1 |
| `product_prefix` | CharField(10) | Default: XT |
| `product_start_number` | IntegerField | Default: 1 |
| `employee_prefix` | CharField(10) | Default: E |
| `employee_start_number` | IntegerField | Default: 1 |
| `trouble_call_prefix` | CharField(10) | Default: TC |
| `trouble_call_start_number` | IntegerField | Default: 1 |
| `work_group_prefix` | CharField(10) | Default: WG |
| `work_group_start_number` | IntegerField | Default: 1 |
| `po_prefix` | CharField(10) | Default: PO |
| `po_start_number` | IntegerField | Default: 1 |
| `vehicle_prefix` | CharField(10) | Default: V |
| `vehicle_start_number` | IntegerField | Default: 1 |
| `custom_email_domain` | CharField(255) | Nullable — Pro/Enterprise add-on |
| `domain_verification_status` | Enum | Pending, Verified, Failed — Nullable |
| `postmark_domain_id` | CharField(100) | Nullable |
| audit fields | | |

### `TenantState` (SDTA local cache — synced from SDP)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Unique |
| `tier` | Enum | Lite, Plus, Pro, Enterprise |
| `status` | Enum | Active, Suspended, Read-Only |
| `seat_limit` | IntegerField | |
| `storage_limit_bytes` | BigIntegerField | |
| `last_synced_at` | DateTimeField | |
| `created_by` | CharField | 'System' |
| `created_at` | DateTimeField | |
| `updated_by` | CharField | 'System' |
| `updated_at` | DateTimeField | |

### `TenantAddOn`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `addon_type` | Enum | Fleet, SMS_Extra, Storage_5GB, Storage_10GB, QB_CSV_Export |
| `status` | Enum | Active, Cancelled, Expired |
| `unit_limit` | IntegerField | Nullable |
| `purchased_on` | DateTimeField | |
| `created_by` | CharField | 'System' |
| `created_at` | DateTimeField | |
| `updated_by` | CharField | 'System' |
| `updated_at` | DateTimeField | |

### `TenantSyncLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `sync_type` | Enum | ProvisionTenant, UpdateStatus, UpdateLimits, UnlockAdmin, ForceSync |
| `status` | Enum | Success, Failed |
| `response_code` | IntegerField | |
| `occurred_at` | DateTimeField | |
| `created_by` | CharField | 'System' |
| `created_at` | DateTimeField | |

### `SessionLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `user_id` | UUID FK → User (SET NULL on delete) | |
| `session_token` | CharField | Unique session identifier |
| `login_at` | DateTimeField | |
| `logout_at` | DateTimeField | Nullable |
| `expiration_at` | DateTimeField | |
| `ip_address` | GenericIPAddressField | |
| `user_agent` | TextField | Raw User-Agent string |
| `permission_snapshot` | JSONField | Permissions at login — for forensic audit |
| `browser` | CharField | Parsed from user_agent |
| `os` | CharField | Parsed from user_agent |
| `device_type` | Enum | Mobile, Desktop |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_at` | DateTimeField | |

### `PasswordResetToken`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `user_id` | UUID FK → User | |
| `token` | CharField | Hashed |
| `expires_at` | DateTimeField | |
| `used_at` | DateTimeField | Nullable |
| audit fields | | |

---

## 5.2 APP: `crm/`

### `Person` (permanent CRM identity — NOT the login user)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `first_name` | CharField(100) | Required |
| `last_name` | CharField(100) | Required |
| audit fields | | |

> Person is never deleted when a Contact is removed. History is preserved.

### `Customer`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `customer_number` | CharField(20) | Auto-generated C26-0001 |
| `status` | Enum | Active, Inactive, Hold, Closed |
| `account_type` | Enum | Residential, Commercial |
| `company_name` | CharField(255) | Required for Commercial, optional for Residential |
| `assigned_to` | UUID FK → User (SET NULL) | Optional |
| `zone_id` | UUID FK → Zone | Nullable |
| `lead_source` | CharField(100) | Customizable |
| `tax_exempt` | BooleanField | Default: False |
| `customer_since` | DateField | Optional |
| `hold_date` | DateTimeField | Nullable — required when status = Hold |
| `hold_reason` | TextField | Nullable — required when status = Hold |
| `closed_at` | DateTimeField | Nullable — required when status = Closed |
| `closed_reason` | TextField | Nullable — required when status = Closed |
| `account_number` | CharField(100) | Required |
| `account_terms` | CharField(100) | Customizable |
| `credit_limit` | DecimalField(12,2) | Required |
| `credit_status` | Enum | Good, Fair, Poor |
| `tax_rate` | DecimalField(7,4) | Nullable — overrides tenant default when set |
| `tags` | ArrayField(CharField) | PostgreSQL ArrayField |
| audit fields | | |

### `Contact` (links Person to Customer, Vendor, Carrier, or Bank)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `person_id` | UUID FK → Person | Required |
| `customer_id` | UUID FK → Customer | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `carrier_id` | UUID FK → Carrier | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `role_title` | CharField(100) | Optional |
| `department` | CharField(100) | Optional |
| `is_primary` | BooleanField | One primary per parent entity |
| `status` | Enum | Active, Left |
| `start_date` | DateField | Optional |
| `left_date` | DateField | Nullable — populated when status = Left |
| audit fields | | |

> DB CHECK CONSTRAINT: Exactly one of customer_id, vendor_id, carrier_id, bank_id must be non-null

### `Address`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `customer_id` | UUID FK → Customer | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `carrier_id` | UUID FK → Carrier | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `asset_id` | UUID FK → Asset | Nullable |
| `user_id` | UUID FK → User | Nullable |
| `warehouse_id` | UUID FK → Warehouse | Nullable |
| `work_group_id` | UUID FK → WorkGroup | Nullable |
| `address_type` | Enum | Service, Billing, Mailing, Other |
| `is_primary` | BooleanField | |
| `street` | CharField(255) | |
| `city` | CharField(100) | |
| `state` | CharField(100) | |
| `zip` | CharField(20) | |
| `country` | CharField(100) | |
| audit fields | | |

> DB CHECK CONSTRAINT: Exactly one parent FK must be non-null

### `Phone`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `customer_id` | UUID FK → Customer | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `carrier_id` | UUID FK → Carrier | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `user_id` | UUID FK → User | Nullable |
| `warehouse_id` | UUID FK → Warehouse | Nullable |
| `phone_number` | CharField(50) | |
| `phone_type` | Enum | Mobile, Work, Home, Fax, Other |
| `is_primary` | BooleanField | |
| audit fields | | |

> DB CHECK CONSTRAINT: Exactly one parent FK must be non-null

### `Social` (emails, social media, web profiles)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `customer_id` | UUID FK → Customer | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `person_id` | UUID FK → Person | Nullable |
| `user_id` | UUID FK → User | Nullable |
| `type` | Enum | Email, Facebook, LinkedIn, Instagram, Twitter/X, YouTube, Website, Other |
| `value` | CharField(500) | Email address or full URL |
| audit fields | | |

> DB CHECK CONSTRAINT: At least one of contact_id, person_id, or user_id must be non-null

### `Zone` (Territory/Zone — for service area assignment)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `name` | CharField(100) | Required |
| `description` | TextField | Optional |
| `status` | Enum | Active, Inactive |
| audit fields | | |

### `EmployeeZone` (junction — Employee ↔ Zone, many-to-many)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `zone_id` | UUID FK → Zone | |
| `employee_id` | UUID FK → User | |

### `Asset`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `asset_number` | CharField(20) | Auto-generated A26-0001 |
| `customer_id` | UUID FK → Customer | Required |
| `address_id` | UUID FK → Address | Nullable — defaults to customer primary service address |
| `parent_asset_id` | UUID FK → Asset (self, SET NULL) | Nullable — nested assets Pro/Enterprise |
| `status` | Enum | Active, Inactive, Decommissioned |
| `asset_category` | CharField(100) | Customizable |
| `asset_type` | CharField(100) | Customizable per category |
| `make` | CharField(100) | Manufacturer |
| `model` | CharField(100) | |
| `serial_number` | CharField(100) | |
| `installation_date` | DateField | Optional |
| `condition` | Enum | Excellent, Good, Fair, Poor |
| `refrigerant_type` | CharField(50) | Optional |
| `capacity_size` | CharField(100) | Optional |
| `warranty_start_date` | DateField | Optional |
| `warranty_end_date` | DateField | Optional |
| `warranty_provider` | CharField(255) | Optional |
| `warranty_notes` | TextField | Optional |
| audit fields | | |

> Calculated display fields (not stored): `age` from installation_date, `warranty_status` (Active/Expired/N/A) from warranty dates

### `TroubleCall`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `trouble_call_number` | CharField(20) | Auto-generated TC26-0001 |
| `customer_id` | UUID FK → Customer | Required |
| `asset_id` | UUID FK → Asset | Nullable — linked during triage |
| `address_id` | UUID FK → Address | Nullable — service location |
| `status` | Enum | New, Triaged, Converted to Work Order, Converted to Quote, Cancelled |
| `source` | Enum | Phone, Customer Portal, Web Widget, Email, Referral |
| `issue_category` | CharField(100) | Customizable |
| `urgency` | Enum | Low, Normal, High, Emergency |
| `description` | TextField | Customer's exact issue description |
| `triage_notes` | TextField | Internal dispatcher notes |
| `requested_datetime` | DateTimeField | Nullable — customer's preferred window |
| `created_by` | CharField | 'System' if from widget |
| audit fields | | |

> Lifecycle: New → Triaged → Converted to Work Order / Converted to Quote / Cancelled. LOCKED after conversion or cancellation.

### `Lead` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `lead_number` | CharField(20) | Auto-generated L26-0001 |
| `customer_id` | UUID FK → Customer | Nullable — populated on conversion |
| `first_name` | CharField(100) | Captured before Customer record exists |
| `last_name` | CharField(100) | |
| `phone` | CharField(50) | |
| `email` | EmailField | |
| `source` | Enum | Referral, Website, Advertisement, Trade Show, Cold Call, Other |
| `status` | Enum | New, Contacted, Qualified, Converted, Lost |
| `notes` | TextField | |
| audit fields | | |

> Lead is NEVER deleted on conversion. Status set to Converted, customer_id populated.

### `Opportunity` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `opportunity_number` | CharField(20) | Auto-generated OP26-0001 |
| `customer_id` | UUID FK → Customer | Required |
| `lead_id` | UUID FK → Lead | Nullable — originating lead |
| `name` | CharField(255) | |
| `status` | Enum | Open, Won, Lost |
| `estimated_value` | DecimalField(12,2) | |
| `expected_close_date` | DateField | |
| `assigned_to` | UUID FK → User | |
| `notes` | TextField | |
| audit fields | | |

### `OpportunityAssignedContact` (junction — Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `opportunity_id` | UUID FK → Opportunity (CASCADE) | |
| `contact_id` | UUID FK → Contact | |
| `customer_id` | UUID FK → Customer | Denormalized for query efficiency |
| `role_in_opportunity` | CharField(255) | e.g. Decision Maker, Budget Holder |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

---

## 5.3 APP: `service/`

### `WorkOrder`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_order_number` | CharField(20) | Auto-generated W26-0001 |
| `customer_id` | UUID FK → Customer | Required |
| `asset_id` | UUID FK → Asset | Nullable — one asset per WO |
| `trouble_call_id` | UUID FK → TroubleCall | Nullable — originating call |
| `workflow_id` | UUID FK → WorkFlow | Nullable — SOP (Pro+) |
| `prev_maint_id` | UUID FK → PreventativeMaintenance | Nullable — originating PM |
| `work_group_id` | UUID FK → WorkGroup | Nullable (Plus+) |
| `wg_division_id` | UUID FK → WGDivision | Nullable (Plus+) |
| `vehicle_id` | UUID FK → Vehicle | Nullable — Fleet add-on |
| `converted_to_invoice_id` | UUID FK → Invoice | Nullable — backlink |
| `status` | Enum | Draft, Scheduled, In Progress, On Hold, Completed, Closed, Cancelled |
| `priority` | Enum | Low, Normal, High, Urgent |
| `work_order_type` | CharField(100) | Customizable |
| `assigned_to` | UUID FK → User | Nullable — primary technician |
| `scheduled_date` | DateTimeField | Nullable |
| `hold_date` | DateTimeField | Nullable — required when status = On Hold |
| `hold_reason` | TextField | Nullable — required when status = On Hold |
| `closed_at` | DateTimeField | Nullable — required when status = Closed |
| `estimated_duration` | DurationField | Nullable |
| `title` | CharField(255) | |
| `description` | TextField | |
| `internal_notes` | TextField | |
| `customer_facing_notes` | TextField | Plus+ only |
| `is_recurring` | BooleanField | Default: False |
| `recurrence_pattern` | JSONField | Nullable |
| audit fields | | |

> Lifecycle: Draft → Scheduled (auto when scheduled_date set) → In Progress (auto when start_date or TimeEntry recorded) → On Hold → Completed → Closed / Cancelled. Cannot revert to Draft once In Progress. Completed/Closed/Cancelled LOCKED — reversion requires Admin + reason.

### `WorkOrderTeam` (junction — additional techs)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_order_id` | UUID FK → WorkOrder (CASCADE) | |
| `employee_id` | UUID FK → User | |

### `WorkOrderLine`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_order_id` | UUID FK → WorkOrder (RESTRICT) | |
| `product_id` | UUID FK → Product | Nullable — can be free-text item |
| `item_name` | CharField(255) | |
| `item_type` | Enum | Service, Product - Inventory, Product - Non-Inventory |
| `description` | TextField | |
| `unit_cost` | DecimalField(12,2) | Internal cost |
| `unit_price` | DecimalField(12,2) | Customer price |
| `quantity` | DecimalField(12,4) | |
| `is_discount` | BooleanField | Default False — forces is_tax_charged=False when True |
| `is_surcharge` | BooleanField | Default False |
| `is_tax_charged` | BooleanField | Default True |
| `sort_order` | IntegerField | |
| audit fields | | |

### `WorkOrderChecklistItem`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_order_id` | UUID FK → WorkOrder (CASCADE) | |
| `label` | CharField(255) | |
| `is_complete` | BooleanField | Default False |
| `notes` | TextField | Optional |
| `sort_order` | IntegerField | |
| audit fields | | |

### `WorkOrderSubtask`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_order_id` | UUID FK → WorkOrder (CASCADE) | |
| `name` | CharField(255) | |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Open, In Progress, Completed |
| `due_date` | DateField | Nullable |
| `notes` | TextField | |
| audit fields | | |

### `TaskTime` (time entries per subtask)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `subtask_id` | UUID FK → WorkOrderSubtask (CASCADE) | |
| `employee_id` | UUID FK → User | |
| `clock_in` | DateTimeField | |
| `clock_out` | DateTimeField | Nullable |
| `total_hours` | DecimalField(8,2) | Calculated |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `TaskToDo`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `subtask_id` | UUID FK → WorkOrderSubtask (CASCADE) | |
| `employee_id` | UUID FK → User | |
| `label` | CharField(255) | |
| `is_complete` | BooleanField | Default False |
| `sort_order` | IntegerField | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `TimeEntry` (clock-in/out per employee per Work Order)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_order_id` | UUID FK → WorkOrder (CASCADE) | |
| `user_id` | UUID FK → User | |
| `clock_in` | DateTimeField | |
| `clock_out` | DateTimeField | Nullable |
| `total_hours` | DecimalField(8,2) | Calculated |
| `labor_cost` | DecimalField(12,2) | Calculated from hours × employee rate |
| audit fields | | |

### `ChecklistTemplate`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `name` | CharField(255) | |
| `work_order_type` | CharField(100) | Optional — auto-applies when WO type matches |
| audit fields | | |

### `ChecklistTemplateItem`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `template_id` | UUID FK → ChecklistTemplate (CASCADE) | |
| `label` | CharField(255) | |
| `sort_order` | IntegerField | |
| audit fields | | |

### `Quote`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `quote_number` | CharField(20) | Auto-generated Q26-0001 |
| `customer_id` | UUID FK → Customer | Required |
| `opportunity_id` | UUID FK → Opportunity | Nullable (Plus+) |
| `converted_to_work_order_id` | UUID FK → WorkOrder | Nullable — backlink |
| `converted_to_invoice_id` | UUID FK → Invoice | Nullable — backlink |
| `work_group_id` | UUID FK → WorkGroup | Nullable (Plus+) |
| `contact_id` | UUID FK → Contact | Nullable |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Draft, Sent, Viewed, Accepted, Rejected, Expired, Converted |
| `quote_date` | DateField | Defaults to today |
| `expiration_date` | DateField | |
| `tax_rate` | DecimalField(7,4) | Frozen at creation |
| `notes` | TextField | Customer-visible |
| `internal_notes` | TextField | |
| `deposit_required` | BooleanField | Plus+ |
| `deposit_type` | Enum | Fixed, Percentage — Nullable |
| `deposit_value` | DecimalField(12,2) | Nullable |
| `approval_name` | CharField(255) | Who approved (Plus+) |
| `approval_at` | DateTimeField | Nullable |
| `approval_ip` | GenericIPAddressField | Nullable |
| audit fields | | |

> Lifecycle: LOCKED once status reaches Sent or beyond. Date fields cleared on backward progression. Expiration auto-set by background task.

### `QuoteAsset` (junction)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `quote_id` | UUID FK → Quote | |
| `asset_id` | UUID FK → Asset | |

### `QuoteLine`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `quote_id` | UUID FK → Quote (RESTRICT) | |
| `product_id` | UUID FK → Product | Nullable |
| `group_label` | CharField(255) | Optional grouping label |
| `item_name` | CharField(255) | |
| `item_type` | Enum | Service, Product - Inventory, Product - Non-Inventory |
| `sku` | CharField(100) | Optional |
| `description` | TextField | |
| `unit_cost` | DecimalField(12,2) | |
| `unit_price` | DecimalField(12,2) | |
| `quantity` | DecimalField(12,4) | |
| `is_discount` | BooleanField | Default False |
| `is_surcharge` | BooleanField | Default False |
| `is_tax_charged` | BooleanField | Default True |
| `visible_to_customer` | BooleanField | Default True |
| `sort_order` | IntegerField | |
| audit fields | | |

### `Invoice`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `invoice_number` | CharField(20) | Auto-generated I26-0001 |
| `customer_id` | UUID FK → Customer | Required |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `quote_id` | UUID FK → Quote | Nullable |
| `work_group_id` | UUID FK → WorkGroup | Nullable (Plus+) |
| `contact_id` | UUID FK → Contact | Nullable |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Draft, Issued, Viewed, Partially Paid, Paid, Overdue, Void, Written Off |
| `invoice_date` | DateField | |
| `due_date` | DateField | |
| `due_date_method` | Enum | Creation Date + N, Sent Date + N, WO Completion + N, Manual |
| `due_date_offset_days` | IntegerField | Nullable |
| `tax_rate` | DecimalField(7,4) | FROZEN at Issued status |
| `line_item_total` | DecimalField(12,2) | Stored — pre-tax subtotal (Step 2 of calc) |
| `line_item_tax_total` | DecimalField(12,2) | Stored — tax total (Step 3 of calc) |
| `invoice_total` | DecimalField(12,2) | Stored — grand total (Step 4 of calc) |
| `deposit_applied` | DecimalField(12,2) | From quote deposit |
| `stripe_payment_link_id` | CharField(255) | Nullable |
| `stripe_payment_link_url` | URLField | Nullable |
| `notes` | TextField | Customer-visible |
| `internal_notes` | TextField | |
| `is_recurring` | BooleanField | Plus+ |
| `recurrence_pattern` | JSONField | Nullable |
| `void_date` | DateTimeField | Nullable — required when Void |
| `void_reason` | TextField | Nullable — required when Void |
| audit fields | | |

> Invoice Calculation Order: (1) LineAmount = Qty × UnitPrice per line, (2) Subtotal = sum(non-discount) - sum(discount), (3) TaxTotal = sum(is_tax_charged lines) × tax_rate, (4) InvoiceTotal = Subtotal + TaxTotal. Tax rate source: Customer.tax_rate if set, else TenantPreference.default_tax_rate. FROZEN at Issued.

### `InvoiceAsset` (junction)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `invoice_id` | UUID FK → Invoice | |
| `asset_id` | UUID FK → Asset | |

### `InvoiceLine`

Same structure as `QuoteLine` but with `invoice_id` FK instead of `quote_id`.

### `Payment`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `payment_number` | CharField(20) | Auto-generated P26-0001 |
| `invoice_id` | UUID FK → Invoice | Required |
| `customer_id` | UUID FK → Customer | Denormalized for reporting |
| `employee_id` | UUID FK → User | Who recorded the payment |
| `vehicle_maint_id` | UUID FK → VehicleMaintenance | Nullable — fleet expense |
| `stripe_response_id` | UUID FK → StripeResponse | Nullable |
| `payment_date` | DateField | |
| `amount` | DecimalField(12,2) | |
| `payment_method` | Enum | Credit/Debit Card, Cash, Check, Bank Transfer, Other |
| `reference_number` | CharField(100) | |
| `stripe_payment_intent_id` | CharField(255) | Nullable |
| `notes` | TextField | |
| audit fields | | |

### `Task` (standalone — not tied to a Work Order)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `task_number` | CharField(20) | Auto-generated T26-0001 |
| `title` | CharField(255) | |
| `description` | TextField | |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Open, In Progress, Completed |
| `due_date` | DateField | Nullable |
| `priority` | Enum | Low, Normal, High, Urgent |
| `customer_id` | UUID FK → Customer | Nullable |
| `asset_id` | UUID FK → Asset | Nullable |
| `notes` | TextField | |
| audit fields | | |

### `Agreement` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `agreement_number` | CharField(20) | Auto-generated |
| `name` | CharField(255) | e.g. Gold Service Plan |
| `description` | TextField | |
| `status` | Enum | Pending, Active, Expired, Cancelled |
| `start_date` | DateField | |
| `end_date` | DateField | Nullable — ongoing |
| `renewal_type` | Enum | Manual, Auto-Renew |
| `pricing_amount` | DecimalField(12,2) | |
| `pricing_frequency` | Enum | Monthly, Quarterly, Annual |
| `discount_percentage` | DecimalField(7,4) | Discount on additional work |
| `cancelled_at` | DateTimeField | Nullable — required when Cancelled |
| `cancelled_reason` | TextField | Nullable — required when Cancelled |
| audit fields | | |

### `CustomerAgreement` (three-way junction: Customer + Agreement + Asset — Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `customer_id` | UUID FK → Customer (RESTRICT) | Required |
| `agreement_id` | UUID FK → Agreement (RESTRICT) | Required |
| `asset_id` | UUID FK → Asset (RESTRICT) | Required — asset-centric design |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `PreventativeMaintenance` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `pm_number` | CharField(20) | Auto-generated |
| `asset_id` | UUID FK → Asset | Required |
| `customer_agreement_id` | UUID FK → CustomerAgreement | Required |
| `workflow_id` | UUID FK → WorkFlow | Required for Pro+; nullable for Plus |
| `customer_id` | UUID FK → Customer | Denormalized |
| `status` | Enum | Active, Paused, Expired, Cancelled |
| `frequency` | Enum | Daily, Weekly, Monthly, Quarterly, Semi-Annual, Annual, Custom |
| `visits_per_period` | IntegerField | |
| `start_date` | DateField | |
| `end_date` | DateField | Nullable |
| `default_assignee_id` | UUID FK → User | Nullable |
| `auto_gen_work_orders` | BooleanField | Default False |
| `advance_gen_days` | IntegerField | Days ahead to generate WO |
| `cancelled_reason` | TextField | Nullable — required when Cancelled |
| audit fields | | |

### `WorkGroup` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_group_number` | CharField(20) | Auto-generated WG26-0001 |
| `name` | CharField(255) | User-defined label |
| `customer_id` | UUID FK → Customer | Required |
| `address_id` | UUID FK → Address | Service location |
| `status` | Enum | Open, In Progress, Completed, Cancelled |
| `notes` | TextField | |
| `cancelled_reason` | TextField | Nullable — required when Cancelled |
| audit fields | | |

### `WGDivision` (sub-grouping within WorkGroup — Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_group_id` | UUID FK → WorkGroup (CASCADE) | |
| `address_id` | UUID FK → Address | Nullable — division-specific location |
| `name` | CharField(255) | |
| `status` | Enum | Open, In Progress, Completed, Cancelled |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `WGTRole` (roles within a WorkGroup — tenant-configurable — Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `name` | CharField(100) | e.g. Lead Technician, Helper, Project Manager |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `WorkGroupTeam` (junction — Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_group_id` | UUID FK → WorkGroup (CASCADE) | |
| `employee_id` | UUID FK → User | |
| `wgt_role_id` | UUID FK → WGTRole | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `WorkGroupAsset` (system-managed rolled-up view — Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_group_id` | UUID FK → WorkGroup (CASCADE) | |
| `asset_id` | UUID FK → Asset | |

> SYSTEM-MANAGED ONLY. Created/removed automatically when WOs with non-null asset_id are added/removed from a WorkGroup. Never manually edited.

---

## 5.4 APP: `inventory/`

### `Product` (ERD: Inventory)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `product_number` | CharField(20) | Auto-generated XT-0001 |
| `name` | CharField(255) | Required |
| `type` | Enum | Service, Product - Inventory, Product - Non-Inventory |
| `status` | Enum | Active, Hold, Discontinued |
| `category` | CharField(100) | Customizable |
| `sku` | CharField(100) | Optional |
| `unit_cost` | DecimalField(12,2) | Internal cost |
| `unit_price` | DecimalField(12,2) | Customer price |
| `description` | TextField | |
| `taxable` | BooleanField | Default True |
| `is_bundle` | BooleanField | Default False |
| `preferred_vendor_id` | UUID FK → Vendor | Nullable (Plus+) |
| `is_low_stock` | BooleanField | Default False — SYSTEM-MANAGED FLAG |
| `is_out_of_stock` | BooleanField | Default False — SYSTEM-MANAGED FLAG |
| `low_stock_threshold` | DecimalField(12,4) | Configurable per product |
| `discontinued_reason` | TextField | Nullable — required when Discontinued |
| audit fields | | |

> is_low_stock and is_out_of_stock are system-set flags, not status values. They trigger notifications. An Active product can carry either flag.

### `BundleItem` (ERD: Kit Items)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `bundle_id` | UUID FK → Product (CASCADE) | Parent bundle product |
| `product_id` | UUID FK → Product (RESTRICT) | Included item — cannot delete if in bundle |
| `quantity` | DecimalField(12,4) | |
| audit fields | | |

### `InvPriceHistory`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `product_id` | UUID FK → Product | |
| `old_unit_cost` | DecimalField(12,2) | |
| `new_unit_cost` | DecimalField(12,2) | |
| `old_unit_price` | DecimalField(12,2) | |
| `new_unit_price` | DecimalField(12,2) | |
| `changed_at` | DateTimeField | |
| `changed_by` | UUID FK → User | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `Warehouse` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `warehouse_number` | CharField(20) | WH26-0001 |
| `name` | CharField(255) | |
| `type` | Enum | Physical Hub, Mobile (Van/Truck) |
| `status` | Enum | Active, Inactive |
| `assigned_user_id` | UUID FK → User | Nullable |
| audit fields | | |

### `SubLocation` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `warehouse_id` | UUID FK → Warehouse | |
| `location_number` | CharField(50) | e.g. B1.S1 |
| `location_type` | Enum | Area, Bin, Shelf, Section, Cabinet, Room |
| `description` | TextField | |
| `status` | Enum | Active, Inactive |
| audit fields | | |

### `LocationAssignedInventory` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `sub_location_id` | UUID FK → SubLocation | |
| `product_id` | UUID FK → Product | |
| `quantity_on_hand` | DecimalField(12,4) | |
| `serial_number` | CharField(100) | Nullable — serialized tracking Pro+ |
| audit fields | | |

### `InventoryCount` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `product_id` | UUID FK → Product | |
| `count_date` | DateTimeField | |
| `counted_by` | UUID FK → User | |
| `physical_count` | DecimalField(12,4) | |
| `system_count` | DecimalField(12,4) | |
| `variance` | DecimalField(12,4) | Calculated |
| `adjustment_applied` | BooleanField | Default False |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `InventoryTransfer` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `product_id` | UUID FK → Product | |
| `source_location_id` | UUID FK → SubLocation | |
| `dest_location_id` | UUID FK → SubLocation | |
| `quantity` | DecimalField(12,4) | |
| `transfer_date` | DateTimeField | |
| `initiated_by` | UUID FK → User | |
| `status` | Enum | Pending, In Transit, Completed, Cancelled |
| `notes` | TextField | |
| audit fields | | |

### `Location` (ERD: Locations — FK Department, FK Warehouse)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `department_id` | UUID FK → Department | Nullable |
| `warehouse_id` | UUID FK → Warehouse | Nullable |
| `name` | CharField(255) | |
| audit fields | | |

### `Pricebook` (Pro/Enterprise)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `name` | CharField(255) | |
| `status` | Enum | Active, Inactive, Discontinued |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `PricebookEntry` (Pro/Enterprise)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `pricebook_id` | UUID FK → Pricebook | |
| `product_id` | UUID FK → Product | |
| `price` | DecimalField(12,2) | Overrides standard unit_price |

---

## 5.5 APP: `procurement/`

### `Vendor` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `vendor_name` | CharField(255) | Required |
| `account_number` | CharField(100) | Optional |
| `status` | Enum | Active, Inactive, Do Not Use |
| `do_not_use_reason` | TextField | Nullable — required when Do Not Use |
| `notes` | TextField | |
| audit fields | | |

> Contacts, Addresses, Phones via shared Triad tables with FKVendor populated.

### `PurchaseOrder` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `po_number` | CharField(20) | Auto-generated PO26-0001 |
| `vendor_id` | UUID FK → Vendor | Required |
| `employee_credit_card_id` | UUID FK → CreditCard | Nullable |
| `status` | Enum | Open, Issued, Partially Received, Received, Void |
| `order_date` | DateField | |
| `expected_date` | DateField | Nullable |
| `issued_date` | DateTimeField | Nullable — set on Issued |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `work_group_id` | UUID FK → WorkGroup | Nullable |
| `void_reason` | TextField | Nullable — required when Void |
| audit fields | | |

> Lifecycle: Open → Issued (triggers VendorBill creation in Pending) → Partially Received → Received (LOCKED) → Void (Admin + reason, auto-voids linked VendorBill)

### `PurchaseOrderLine`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `purchase_order_id` | UUID FK → PurchaseOrder (RESTRICT) | |
| `product_id` | UUID FK → Product | |
| `requisition_line_id` | UUID FK → RequisitionLine | Nullable |
| `status` | Enum | Open, Partially Received, Received |
| `quantity_ordered` | DecimalField(12,4) | |
| `quantity_received` | DecimalField(12,4) | Default 0 |
| `unit_cost` | DecimalField(12,2) | |
| audit fields | | |

### `Receiving`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `po_line_id` | UUID FK → PurchaseOrderLine (RESTRICT) | |
| `product_id` | UUID FK → Product | |
| `employee_id` | UUID FK → User | Who received |
| `quantity_received` | DecimalField(12,4) | |
| `received_date` | DateTimeField | |
| `condition` | Enum | Good, Damaged, Partial |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `LotInfo` (Pro/Enterprise — serialized/lot-tracked receiving)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `po_line_id` | UUID FK → PurchaseOrderLine (RESTRICT) | |
| `product_id` | UUID FK → Product | |
| `lot_number` | CharField(100) | |
| `expiration_date` | DateField | Nullable |
| `quantity` | DecimalField(12,4) | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `VendorBill` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `vendor_id` | UUID FK → Vendor | Required |
| `bill_number` | CharField(100) | |
| `bill_date` | DateField | |
| `due_date` | DateField | |
| `amount` | DecimalField(12,2) | |
| `status` | Enum | Pending, Received, Partially Paid, Paid, Overdue, Void |
| `purchase_order_id` | UUID FK → PurchaseOrder | Nullable |
| `notes` | TextField | |
| audit fields | | |

### `VendorPayment` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `vendor_id` | UUID FK → Vendor | Required |
| `purchase_order_id` | UUID FK → PurchaseOrder | Nullable |
| `vendor_bill_id` | UUID FK → VendorBill | Nullable |
| `payment_date` | DateField | |
| `amount` | DecimalField(12,2) | |
| `payment_method` | Enum | Check, Bank Transfer, Credit Card, Other |
| `reference_number` | CharField(100) | |
| `notes` | TextField | |
| audit fields | | |

### `Requisition` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `requisition_number` | CharField(20) | Auto-generated RQ26-0001 |
| `employee_id` | UUID FK → User | Requestor |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `vehicle_id` | UUID FK → Vehicle | Nullable |
| `status` | Enum | New, Approved, Partially Fulfilled, Fulfilled, Cancelled |
| `fulfillment_method` | Enum | Warehouse Transfer, Purchase Order |
| `required_by_date` | DateField | Nullable |
| `cancelled_reason` | TextField | Nullable |
| audit fields | | |

### `RequisitionLine` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `requisition_id` | UUID FK → Requisition (RESTRICT) | |
| `product_id` | UUID FK → Product | |
| `po_line_id` | UUID FK → PurchaseOrderLine | Nullable — when fulfilled via PO |
| `quantity_requested` | DecimalField(12,4) | |
| `quantity_fulfilled` | DecimalField(12,4) | Default 0 |
| `notes` | TextField | |
| audit fields | | |

### `RMA` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `rma_number` | CharField(20) | Auto-generated |
| `po_line_id` | UUID FK → PurchaseOrderLine | |
| `product_id` | UUID FK → Product | |
| `vendor_id` | UUID FK → Vendor | |
| `status` | Enum | Initiated, Shipped, Received by Vendor, Credited, Closed, Denied |
| `reason` | Enum | Defective, Wrong Item, Damaged, Overstock, Other |
| `quantity` | DecimalField(12,4) | |
| `credit_amount` | DecimalField(12,2) | |
| `denied_reason` | TextField | Nullable — required when Denied |
| `notes` | TextField | |
| audit fields | | |

---

## 5.6 APP: `finance/`

### `Bank` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `customer_id` | UUID FK → Customer | Required |
| `bank_name` | CharField(255) | |
| `account_type` | Enum | Checking, Savings, Line of Credit, Other |
| `routing_number` | CharField(100) | Encrypted at application layer |
| `account_number_last4` | CharField(4) | Last 4 digits only — never store full number |
| `status` | Enum | Active, Inactive |
| `notes` | TextField | |
| audit fields | | |

### `Carrier` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `carrier_name` | CharField(255) | |
| `carrier_type` | Enum | Insurance, Surety, Freight, Other |
| `policy_number` | CharField(100) | |
| `status` | Enum | Active, Inactive |
| `notes` | TextField | |
| audit fields | | |

### `Accounting` (Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `customer_id` | UUID FK → Customer | Nullable |
| `carrier_id` | UUID FK → Carrier | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `account_type` | CharField(100) | Receivable, Payable, Revenue, Expense, etc. |
| `balance` | DecimalField(12,2) | |
| audit fields | | |

### `Ledger`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `payment_id` | UUID FK → Payment | Nullable |
| `vendor_payment_id` | UUID FK → VendorPayment | Nullable |
| `customer_id` | UUID FK → Customer | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `purchase_order_id` | UUID FK → PurchaseOrder | Nullable |
| `invoice_id` | UUID FK → Invoice | Nullable |
| `entry_type` | Enum | Debit, Credit |
| `amount` | DecimalField(12,2) | |
| `running_balance` | DecimalField(12,2) | Calculated at WRITE-TIME — never updated after creation |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

> IMMUTABLE — Ledger entries are never edited or deleted. Financial corrections use new Reversing Entries.

### `StripeConnection` (one per tenant — Plus+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Unique |
| `stripe_account_id` | CharField(100) | |
| `access_token` | CharField(500) | Encrypted at application layer |
| `is_active` | BooleanField | |
| `connected_at` | DateTimeField | |
| `disconnected_at` | DateTimeField | Nullable |
| audit fields | | |

### `StripeResponse`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `invoice_id` | UUID FK → Invoice | |
| `customer_id` | UUID FK → Customer | |
| `stripe_connection_id` | UUID FK → StripeConnection | |
| `stripe_log_id` | UUID FK → StripeLog | Nullable |
| `stripe_payment_intent_id` | CharField(255) | |
| `amount` | DecimalField(12,2) | |
| `status` | CharField(100) | |
| audit fields | | |

### `StripeLog` (12-month rolling log)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `customer_id` | UUID FK → Customer | |
| `stripe_connection_id` | UUID FK → StripeConnection | |
| `event_type` | CharField(100) | |
| `payload` | JSONField | Full Stripe event payload |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `WebhookLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `stripe_event_id` | CharField(255) | UNIQUE — idempotency enforcement |
| `event_type` | CharField(100) | |
| `processed_at` | DateTimeField | |
| `status` | Enum | Processed, Failed, Skipped |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `StripeConnectionLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `event` | Enum | Connected, Disconnected, Token Revoked |
| `occurred_at` | DateTimeField | |
| `details` | JSONField | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `StripeAPIRequestLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `endpoint` | CharField(255) | |
| `method` | CharField(10) | |
| `response_status` | IntegerField | |
| `requested_at` | DateTimeField | |
| `duration_ms` | IntegerField | |
| `error_message` | TextField | Nullable |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

---

## 5.7 APP: `workflow/`

### `WorkFlow` (Pro/Enterprise)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `name` | CharField(255) | e.g. Annual HVAC Tune-Up SOP |
| `description` | TextField | |
| `status` | Enum | Draft, Active, Inactive |
| `work_order_type` | CharField(100) | Nullable — auto-apply trigger |
| audit fields | | |

> LOCKED when Active. Structure changes require new version or Admin revert to Draft with reason.

### `WFStep`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `workflow_id` | UUID FK → WorkFlow (CASCADE) | |
| `step_name` | CharField(255) | |
| `description` | TextField | |
| `sort_order` | IntegerField | |
| `estimated_duration` | DurationField | Nullable |
| audit fields | | |

### `WFStepToDo`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `wf_step_id` | UUID FK → WFStep (CASCADE) | |
| `label` | CharField(255) | |
| `sort_order` | IntegerField | |
| `is_required` | BooleanField | Must complete before step is done |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `WFTool` (junction — WorkFlow ↔ Equipment)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `workflow_id` | UUID FK → WorkFlow (CASCADE) | |
| `equipment_id` | UUID FK → Equipment (CASCADE) | |

> Advisory only — dispatcher sees a soft warning if required equipment is not checked out. Does not hard-block dispatch.

### `WFInventory` (junction — WorkFlow ↔ Product)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `workflow_id` | UUID FK → WorkFlow (CASCADE) | |
| `product_id` | UUID FK → Product | |
| `quantity_required` | DecimalField(12,4) | |

### `WFSafetyForm` (junction — WorkFlow ↔ SafetyForm)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `workflow_id` | UUID FK → WorkFlow (CASCADE) | |
| `safety_form_id` | UUID FK → SafetyForm | |

### `SafetyForm` (Pro/Enterprise)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `form_name` | CharField(255) | |
| `description` | TextField | |
| `status` | Enum | Draft, Active, Inactive |
| `form_definition` | JSONField | Field definitions array |
| `required_before_work` | BooleanField | Default False |
| audit fields | | |

> LOCKED when Active. Structure changes require new version or Admin revert.

### `WOSFAnswer` (completed safety form per Work Order — Pro/Enterprise)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `work_order_id` | UUID FK → WorkOrder (RESTRICT) | Safety answers block WO deletion |
| `employee_id` | UUID FK → User | Who completed the form |
| `safety_form_id` | UUID FK → SafetyForm | |
| `answers` | JSONField | Completed responses |
| `completed_at` | DateTimeField | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

---

## 5.8 APP: `fleet/`

All fleet models are gated behind the Fleet Management add-on. Check `TenantAddOn.addon_type = 'Fleet'` and `status = 'Active'` before any UI or controller access.

### `Vehicle`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `vehicle_number` | CharField(20) | Auto-generated V26-0001 |
| `status` | Enum | Active, Out of Service, Decommissioned |
| `year` | IntegerField | 4-digit |
| `make` | CharField(100) | |
| `model` | CharField(100) | |
| `trim` | CharField(100) | Optional |
| `vin` | CharField(17) | |
| `license_plate` | CharField(20) | |
| `license_state` | CharField(50) | |
| `color` | CharField(50) | Optional |
| `vehicle_type` | CharField(50) | Van, Truck, Car, Box Truck, Trailer, Other |
| `assigned_user_id` | UUID FK → User | Nullable |
| `odometer_current` | IntegerField | Updated via MileageLog |
| `purchase_date` | DateField | Optional |
| `purchase_price` | DecimalField(12,2) | Optional — internal |
| `registration_expiry` | DateField | |
| `insurance_policy` | CharField(100) | |
| `insurance_provider` | CharField(255) | |
| `insurance_expiry` | DateField | |
| `last_inspection_date` | DateField | Nullable |
| `next_inspection_date` | DateField | Nullable |
| `notes` | TextField | |
| audit fields | | |

### `VehicleMaintenance`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `vehicle_id` | UUID FK → Vehicle (RESTRICT) | |
| `maintenance_number` | CharField(20) | M26-0001 |
| `maintenance_type` | CharField(100) | Customizable |
| `status` | Enum | Scheduled, Completed, Overdue, Cancelled |
| `scheduled_date` | DateField | |
| `completed_date` | DateField | Nullable — required when Completed |
| `odometer_at_service` | IntegerField | Nullable — required when Completed |
| `next_service_date` | DateField | Nullable |
| `next_service_odometer` | IntegerField | Nullable |
| `cost` | DecimalField(12,2) | |
| `performed_by` | Enum | In-House, External Shop |
| `vendor_id` | UUID FK → Vendor | Nullable — when External Shop |
| `vendor_name` | CharField(255) | Nullable — when External Shop and no Vendor record |
| `description` | TextField | |
| `cancelled_reason` | TextField | Nullable — required when Cancelled |
| audit fields | | |

### `MileageLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `vehicle_id` | UUID FK → Vehicle (CASCADE) | |
| `user_id` | UUID FK → User | Driver |
| `log_date` | DateField | |
| `odometer_start` | IntegerField | |
| `odometer_end` | IntegerField | |
| `miles_driven` | IntegerField | Calculated |
| `purpose` | CharField(255) | |
| `work_order_id` | UUID FK → WorkOrder | Optional |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `VehicleInventory` (ERD: Vehicle Inventory — truck stock)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `vehicle_id` | UUID FK → Vehicle (CASCADE) | |
| `product_id` | UUID FK → Product | Nullable — saleable inventory |
| `equipment_id` | UUID FK → Equipment | Nullable — company tools |
| `quantity` | DecimalField(12,4) | Nullable — for products |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

> DB CHECK CONSTRAINT: Exactly one of product_id or equipment_id must be non-null

---

## 5.9 APP: `infrastructure/`

### `Note`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `customer_id` | UUID FK → Customer (CASCADE) | Nullable |
| `contact_id` | UUID FK → Contact (CASCADE) | Nullable |
| `lead_id` | UUID FK → Lead (CASCADE) | Nullable |
| `opportunity_id` | UUID FK → Opportunity (CASCADE) | Nullable |
| `asset_id` | UUID FK → Asset (CASCADE) | Nullable |
| `quote_id` | UUID FK → Quote (CASCADE) | Nullable |
| `work_order_id` | UUID FK → WorkOrder (CASCADE) | Nullable |
| `invoice_id` | UUID FK → Invoice (CASCADE) | Nullable |
| `trouble_call_id` | UUID FK → TroubleCall (CASCADE) | Nullable |
| `prev_maint_id` | UUID FK → PreventativeMaintenance (CASCADE) | Nullable |
| `workflow_id` | UUID FK → WorkFlow (CASCADE) | Nullable |
| `payment_id` | UUID FK → Payment (CASCADE) | Nullable |
| `vendor_payment_id` | UUID FK → VendorPayment (CASCADE) | Nullable |
| `user_id` | UUID FK → User (CASCADE) | Nullable |
| `vendor_id` | UUID FK → Vendor (CASCADE) | Nullable |
| `purchase_order_id` | UUID FK → PurchaseOrder (CASCADE) | Nullable |
| `vendor_bill_id` | UUID FK → VendorBill (CASCADE) | Nullable |
| `requisition_id` | UUID FK → Requisition (CASCADE) | Nullable |
| `rma_id` | UUID FK → RMA (CASCADE) | Nullable |
| `task_id` | UUID FK → Task (CASCADE) | Nullable |
| `vehicle_id` | UUID FK → Vehicle (CASCADE) | Nullable |
| `warehouse_id` | UUID FK → Warehouse (CASCADE) | Nullable |
| `equipment_id` | UUID FK → Equipment (CASCADE) | Nullable |
| `safety_form_id` | UUID FK → SafetyForm (CASCADE) | Nullable |
| `ledger_id` | UUID FK → Ledger | Nullable |
| `content` | TextField | The note body |
| `is_internal` | BooleanField | Default True |
| audit fields | | |

> DB CHECK CONSTRAINT: Exactly one parent FK must be non-null (Exclusive Arc — 25 parent options)

### `Document`

Same Exclusive Arc FK structure as `Note`, plus:

| Field | Type | Notes |
|---|---|---|
| `original_filename` | CharField(255) | |
| `file_key` | CharField(1000) | Full S3 path: /tenant-{uuid}/{domain}/{entity}/{record_uuid}/{file_uuid}.ext |
| `mime_type` | CharField(100) | |
| `file_size_bytes` | BigIntegerField | |
| `sha256_hash` | CharField(64) | Integrity verification |
| `scan_status` | Enum | Pending, Clean, Infected |

> ON DELETE: Documents use RESTRICT (not CASCADE) to protect storage tracking integrity. Documents block parent deletion.
> Maximum file size: 100 MB. Supported types: images, documents, CAD/vector, compressed. Prohibited: executables.
> Files are quarantined on upload, virus-scanned via ClamAV, then promoted to clean bucket.

### `SequenceTracker`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `entity_type` | CharField(50) | e.g. WorkOrder, Invoice, Customer |
| `year` | IntegerField | Nullable — for annual reset |
| `last_value` | IntegerField | Seeded at start_number - 1 |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

> UNIQUE constraint on (tenant_id, entity_type, year). Increment MUST be atomic — use SELECT ... FOR UPDATE SKIP LOCKED or similar.

### `Notification`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `user_id` | UUID FK → User | Nullable — null = all admins |
| `message` | TextField | |
| `severity` | Enum | Info, Warning, Error |
| `is_dismissed` | BooleanField | Default False |
| audit fields | | |

### `StatusChangeLog` (immutable — every status transition system-wide)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `entity_name` | CharField(100) | e.g. WorkOrder, Invoice |
| `record_id` | UUIDField | |
| `record_number` | CharField(50) | Human-readable e.g. W26-0042 |
| `pre_status` | CharField(100) | |
| `post_status` | CharField(100) | |
| `reason` | TextField | Required for Voids, Reversions, Holds |
| `acted_by` | UUID FK → User | Nullable |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `AuditEvent` (immutable — never deleted — 18-month retention)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `session_id` | UUID FK → SessionLog (SET NULL) | |
| `user_id` | UUID FK → User (SET NULL) | |
| `event_timestamp` | DateTimeField | |
| `action` | Enum | Created, Updated, Deleted, Approved, Voided, PermissionDenied, etc. |
| `entity_type` | CharField(100) | |
| `entity_id` | UUIDField | |
| `record_number` | CharField(50) | Human-readable |
| `details` | JSONField | Contextual change detail |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `SystemErrorLog` (90-day retention)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Nullable — system errors may lack tenant context |
| `user_id` | UUID FK → User | Nullable |
| `error_type` | CharField(255) | Exception class name |
| `message` | TextField | |
| `traceback` | TextField | NEVER exposed to user |
| `occurred_at` | DateTimeField | |
| `request_path` | CharField(500) | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `StorageTracker` (one per tenant)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Unique |
| `total_bytes_used` | BigIntegerField | Default 0 |
| `pending_quota_bytes` | BigIntegerField | Default 0 — files in quarantine |
| `created_by` | CharField | 'System' |
| `created_at` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_at` | DateTimeField | |

### `DataExportLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `user_id` | UUID FK → User | |
| `entity_type` | CharField(100) | |
| `requested_at` | DateTimeField | |
| `status` | Enum | Queued, Complete, Failed |
| audit fields | | |

### `EmailDeliveryLog` (12-month retention)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `user_id` | UUID FK → User | |
| `email_type` | CharField(100) | PasswordReset, WelcomeInvite, etc. |
| `to_address` | EmailField | |
| `sent_at` | DateTimeField | |
| `status` | Enum | Sent, Delivered, Bounced, Failed |
| `postmark_message_id` | CharField(255) | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `PasswordResetToken`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `user_id` | UUID FK → User | |
| `token` | CharField(255) | Hashed |
| `expires_at` | DateTimeField | |
| `used_at` | DateTimeField | Nullable |
| audit fields | | |

### `OnboardingState` (one per tenant — tracks new tenant setup progress)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Unique |
| `checklist_items` | JSONField | Keys: profile_complete, preferences_set, first_customer, first_asset, first_product, stripe_connected (optional), employees_added (optional) |
| `is_complete` | BooleanField | True when all non-optional items done |
| `created_by` | CharField | 'System' |
| `created_at` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_at` | DateTimeField | |

> Updated via Django `post_save` signals on TenantPreference, Customer, Asset, Product, StripeConnection, and User. Hidden from UI when is_complete = True.

### `TenantSyncLog`

See Section 5.1 (users app). Can live in infrastructure or users app — agent's discretion.

---

## 5.10 APP: `communications/`

All communication tables defined. No field-level spec document existed at time of handoff — these are derived from ERD V9 and system context.

### `CommunicationTemplate`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `name` | CharField(255) | |
| `channel` | Enum | SMS, Email |
| `subject` | CharField(255) | Email only — nullable for SMS |
| `body` | TextField | Supports merge fields e.g. {{customer_name}} |
| `status` | Enum | Draft, Active, Inactive |
| audit fields | | |

> LOCKED when Active. Can only be assigned to Triggers when Active. Must have at least one Active Template before a Trigger can go Active.

### `CommunicationTrigger`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `name` | CharField(255) | |
| `event_type` | CharField(100) | e.g. workorder.status_changed, invoice.created, payment.received |
| `event_condition` | JSONField | Nullable — conditions that must match for trigger to fire |
| `timing_offset_minutes` | IntegerField | 0 = immediate; negative = before event; positive = after event |
| `channel` | Enum | SMS, Email, Both |
| `status` | Enum | Draft, Active, Inactive |
| audit fields | | |

### `CommTriggerTemplates` (junction — Trigger ↔ Template, many-to-many)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `trigger_id` | UUID FK → CommunicationTrigger | |
| `template_id` | UUID FK → CommunicationTemplate | |

### `TriggerLog` (delivery log — every fired message)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `trigger_id` | UUID FK → CommunicationTrigger | |
| `template_id` | UUID FK → CommunicationTemplate | |
| `customer_id` | UUID FK → Customer | |
| `contact_id` | UUID FK → Contact | Nullable |
| `channel` | Enum | SMS, Email |
| `to_address` | CharField(255) | Email or phone number |
| `entity_type` | CharField(100) | e.g. WorkOrder, Invoice |
| `entity_id` | UUIDField | Record that fired the trigger |
| `points_consumed` | IntegerField | 1 per SMS, varies per email |
| `status` | Enum | Sent, Delivered, Failed, Bounced |
| `provider_message_id` | CharField(255) | Nullable — from Postmark or Twilio |
| `created_by` | CharField | 'System' |
| `created_at` | DateTimeField | |

### `CustomerPointBase` (tracks point allocations and usage per billing period)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Unique |
| `sms_points_allocated` | IntegerField | Per billing period — set from tier |
| `sms_points_used` | IntegerField | Default 0 — incremented on each fired SMS trigger |
| `email_points_allocated` | IntegerField | Per billing period |
| `email_points_used` | IntegerField | Default 0 |
| `storage_limit_bytes` | BigIntegerField | Copy from TenantState |
| `billing_period_start` | DateField | |
| `billing_period_end` | DateField | |
| `created_by` | CharField | 'System' |
| `created_at` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_at` | DateTimeField | |

> Points reset to 0 at billing anniversary via Celery task. Unused points do NOT roll over.

---

## 5.11 APP: `users/` — HR entities (Skills, Equipment, CreditCard)

### `Skill` (Pro/Enterprise)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `name` | CharField(255) | e.g. EPA 608 Certification |
| `category` | Enum | Certification, License, Training, Competency |
| `status` | Enum | Active, Inactive |
| audit fields | | |

### `EmployeeSkill` (junction — Pro/Enterprise)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `employee_id` | UUID FK → User (CASCADE) | |
| `skill_id` | UUID FK → Skill | |
| `date_earned` | DateField | |
| `expiration_date` | DateField | Nullable |
| `status` | Enum | Active, Expired |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `Equipment` (Pro/Enterprise — company-owned tools)

**IMPORTANT:** Equipment = company-owned tools. NOT the same as Asset (customer-owned) or Product (sold to customers).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `equipment_number` | CharField(20) | Auto-generated EQ26-0001 |
| `name` | CharField(255) | |
| `category` | Enum | Power Tool, Hand Tool, Diagnostic, Safety, Other |
| `serial_number` | CharField(100) | Optional |
| `status` | Enum | Available, Checked Out, In Repair, Decommissioned |
| `purchase_date` | DateField | Optional |
| `purchase_cost` | DecimalField(12,2) | Optional |
| `notes` | TextField | |
| audit fields | | |

### `CheckInOut` (Pro/Enterprise)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `equipment_id` | UUID FK → Equipment (RESTRICT) | Custody records block equipment deletion |
| `employee_id` | UUID FK → User | |
| `checked_out_at` | DateTimeField | |
| `checked_in_at` | DateTimeField | Nullable — null = still out |
| `condition_out` | Enum | Good, Fair, Needs Repair |
| `condition_in` | Enum | Good, Fair, Damaged — Nullable |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_at` | DateTimeField | |

### `CreditCard` (Pro/Enterprise — company expense cards)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | |
| `employee_id` | UUID FK → User | |
| `card_type` | Enum | Visa, Mastercard, Amex, Other |
| `last_four` | CharField(4) | Last 4 digits only |
| `issuing_bank` | CharField(255) | |
| `expiration_date` | DateField | |
| `credit_limit` | DecimalField(12,2) | |
| `status` | Enum | Active, Suspended, Cancelled |
| `notes` | TextField | |
| audit fields | | |

---

# PART 6 — PERMISSION SYSTEM IMPLEMENTATION

## 6.1 Permission Registry (resource keys)

| Module | Resource Key | Tier |
|---|---|---|
| CRM | `crm_customer` | Lite |
| CRM | `crm_asset` | Lite |
| CRM | `crm_troublecall` | Lite |
| CRM | `crm_lead` | Plus+ |
| CRM | `crm_opportunity` | Plus+ |
| Service | `service_quote` | Lite |
| Service | `service_workorder` | Lite |
| Service | `service_invoice` | Lite |
| Service | `service_task` | Lite |
| Service | `service_workgroup` | Plus+ |
| Service | `service_agreement` | Plus+ |
| Service | `service_pm` | Plus+ |
| Service | `service_workflow` | Pro+ |
| Financial | `fin_payment` | Lite |
| Financial | `fin_vendor_payment` | Plus+ |
| Financial | `fin_ledger` | Plus+ |
| Financial | `fin_bank` | Plus+ |
| Financial | `fin_carrier` | Plus+ |
| Financial | `fin_accounting` | Plus+ |
| Procurement | `proc_vendor` | Plus+ |
| Procurement | `proc_po` | Plus+ |
| Procurement | `proc_vendor_bill` | Plus+ |
| Procurement | `proc_requisition` | Plus+ |
| Procurement | `proc_rma` | Plus+ |
| Inventory | `inv_item` | Lite |
| Inventory | `inv_warehouse` | Plus+ |
| Inventory | `inv_count` | Plus+ |
| Inventory | `inv_transfer` | Plus+ |
| Compliance | `comp_safety_form` | Pro+ |
| Compliance | `comp_sf_answers` | Pro+ |
| HR | `hr_employee` | Lite (admin only) |
| HR | `hr_skill` | Pro+ |
| HR | `hr_equipment` | Pro+ |
| HR | `hr_credit_card` | Pro+ |
| Fleet | `fleet_vehicle` | Fleet Add-On |
| Fleet | `fleet_maintenance` | Fleet Add-On |
| Fleet | `fleet_mileage` | Fleet Add-On |

## 6.2 Decorator Implementation

```python
# apps/users/decorators.py

def tier_required(min_tier):
    """Layer 1: Tier entitlement check"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            tier_order = {'Lite': 1, 'Plus': 2, 'Pro': 3, 'Enterprise': 4}
            tenant_tier = request.user.tenant_state.tier
            if tier_order.get(tenant_tier, 0) < tier_order.get(min_tier, 0):
                raise TierUpgradeRequired(min_tier)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def permission_required(resource_key, action):
    """Layer 2: Role-based CRUD check — reads from session cache"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            perm_snapshot = request.session.get('permission_snapshot', {})
            if not perm_snapshot.get(resource_key, {}).get(f'can_{action}', False):
                # Log to AuditEvent: action=PermissionDenied
                raise PermissionDenied(resource_key, action)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage:
@tier_required('plus')
@permission_required('service_invoice', 'edit')
def edit_invoice_view(request, invoice_id):
    pass
```

## 6.3 Permission Logic Rules

- **Additive Union**: If ANY of a user's roles grants a permission, it is granted. No "Deny" concept.
- **System roles** (`is_custom=False`): Immutable — UI must block editing.
- **Safety lock**: Cannot delete the last Administrator role or remove edit permissions from the only admin role.
- **Cache**: Permission matrix cached in Redis session at login. Snapshot stored in `SessionLog.permission_snapshot` at login time.

---

# PART 7 — BACKGROUND TASKS (Celery)

All tasks use `transaction.atomic()` for multi-record writes. All tasks implement exponential backoff: `countdown=2**retry_count`. On max retries exhausted: log to Sentry + create `Notification` record.

| Task | Schedule | Purpose |
|---|---|---|
| `purge_deleted_tenant_data` | 02:00 local | Hard-delete tenants after 60-day cleanup window |
| `purge_audit_logs` | Sun 03:00 local | Delete AuditEvents older than 18 months |
| `purge_session_logs` | Sun 03:15 local | Delete SessionLogs older than 18 months |
| `purge_system_errors` | Sun 03:30 local | Delete SystemErrorLogs older than 90 days |
| `purge_stripe_request_logs` | Sun 03:45 local | Delete StripeAPIRequestLogs older than 90 days |
| `purge_webhook_logs` | Sun 04:00 local | Delete WebhookLogs older than 12 months |
| `purge_email_delivery_logs` | Sun 04:15 local | Delete EmailDeliveryLogs older than 12 months |
| `reconcile_storage_usage` | 01:00 local | Recalculate StorageTracker from Document.file_size_bytes |
| `sync_tenant_state_cache` | Every 6 hours UTC | Force-refresh TenantState from SDP for all active tenants |
| `manage_trial_lifecycle` | 00:30 local | Day 15: Read-Only; Day 45: flag for deletion |
| `generate_recurring_invoices` | 00:01 local | Pro+ — generate recurring invoice drafts |
| `update_overdue_invoices` | 00:15 local | Set Overdue on Invoices past due_date |
| `expire_quotes` | 00:20 local | Set Expired on Quotes past expiration_date |
| `generate_pm_work_orders` | 00:30 local | Plus+ — auto-generate WOs from active PMs |
| `process_agreement_expirations` | 01:15 local | Set Expired on Agreements past end_date |
| `check_employee_certification_expiry` | 06:00 local daily | Pro+ — 30-day and expired cert alerts |
| `check_fleet_compliance` | 06:15 local daily | Fleet add-on — registration/insurance/inspection alerts |
| `check_vehicle_maintenance_due` | 06:30 local daily | Fleet add-on — maintenance date/odometer alerts |
| `reset_communication_points` | 00:01 local (billing anniversary) | Reset sms_points_used and email_points_used to 0 |

> All schedules use `TenantPreference.timezone` for local time evaluation. Global UTC tasks explicitly noted.

---

# PART 8 — DATABASE INDEXES

Mandatory indexes on every table:
- `id` — UNIQUE B-Tree (PK)
- `tenant_id` — B-Tree
- `(tenant_id, id)` — composite B-Tree

Additional required indexes (implement via Django `Meta.indexes`):

```python
# Example pattern
class Meta:
    indexes = [
        models.Index(fields=['tenant_id', 'status']),
        models.Index(fields=['tenant_id', 'customer_id']),
    ]
```

Key entity-specific indexes:

| Model | Index columns |
|---|---|
| Customer | (tenant_id, status), (tenant_id, assigned_to) |
| Asset | (tenant_id, customer_id), (tenant_id, status), (tenant_id, parent_asset_id) |
| TroubleCall | (tenant_id, customer_id), (tenant_id, status), (tenant_id, asset_id) |
| WorkOrder | (tenant_id, customer_id), (tenant_id, asset_id), (tenant_id, status), (tenant_id, assigned_to), (tenant_id, scheduled_date), (tenant_id, work_group_id), (tenant_id, prev_maint_id), (tenant_id, trouble_call_id) |
| Quote | (tenant_id, customer_id), (tenant_id, status), (tenant_id, opportunity_id) |
| Invoice | (tenant_id, customer_id), (tenant_id, status), (tenant_id, due_date) |
| Payment | (tenant_id, invoice_id), (tenant_id, customer_id) |
| Lead | (tenant_id, status), (tenant_id, customer_id) |
| Opportunity | (tenant_id, customer_id), (tenant_id, status), (tenant_id, lead_id) |
| Agreement | (tenant_id, status) |
| CustomerAgreement | (tenant_id, customer_id), (tenant_id, agreement_id), (tenant_id, asset_id) |
| PreventativeMaintenance | (tenant_id, customer_agreement_id), (tenant_id, asset_id), (tenant_id, status) |
| WorkGroup | (tenant_id, customer_id), (tenant_id, status) |
| PurchaseOrder | (tenant_id, vendor_id), (tenant_id, status) |
| VendorBill | (tenant_id, vendor_id), (tenant_id, status) |
| Requisition | (tenant_id, employee_id), (tenant_id, status) |
| RMA | (tenant_id, vendor_id), (tenant_id, status) |
| LocationAssignedInventory | (tenant_id, sub_location_id), (tenant_id, product_id) |
| InventoryTransfer | (tenant_id, product_id), (tenant_id, status) |
| WorkFlow | (tenant_id, status) |
| SafetyForm | (tenant_id, status) |
| WOSFAnswer | (tenant_id, work_order_id), (tenant_id, employee_id) |
| EmployeeSkill | (tenant_id, employee_id), (tenant_id, skill_id), (tenant_id, expiration_date) |
| Equipment | (tenant_id, status) |
| CheckInOut | (tenant_id, equipment_id), (tenant_id, employee_id) |
| CreditCard | (tenant_id, employee_id) |
| Vehicle | (tenant_id, status), (tenant_id, assigned_user_id) |
| VehicleMaintenance | (tenant_id, vehicle_id), (tenant_id, status) |
| MileageLog | (tenant_id, vehicle_id), (tenant_id, user_id) |
| VehicleInventory | (tenant_id, vehicle_id) |
| Note | (tenant_id, customer_id), (tenant_id, work_order_id) — repeat per FK |
| Document | (tenant_id, customer_id), (tenant_id, work_order_id) — repeat per FK |
| SessionLog | (tenant_id, user_id) |
| AuditEvent | (tenant_id, entity_type, entity_id), (tenant_id, event_timestamp) |
| WebhookLog | stripe_event_id UNIQUE |
| SequenceTracker | (tenant_id, entity_type, year) UNIQUE |
| StatusChangeLog | (tenant_id, entity_name, record_id) |

---

# PART 9 — DELETE RULES SUMMARY

Top-level entities cannot be deleted if they have child records. Use status changes instead:

| Entity | Preferred Alternative |
|---|---|
| Customer | Status = Inactive or Closed |
| Asset | Status = Decommissioned |
| WorkOrder | Status = Cancelled |
| Quote | Status = Expired or Rejected |
| Invoice | Status = Void |
| Employee | Status = Terminated |
| Vehicle | Status = Decommissioned |
| Agreement | Status = Cancelled |
| WorkGroup | Status = Cancelled |
| Equipment | Status = Decommissioned |
| WorkFlow | Status = Inactive |
| Product | Status = Discontinued |
| Vendor | Status = Do Not Use |

---

# PART 10 — OPEN ITEMS FOR AGENT

The following items have no authoritative spec. Agent must implement reasonable defaults and flag for review:

| Item | Guidance |
|---|---|
| `Sprint`, `SprintMembers`, `Milestones`, `AssociatedTasks`, `MilestoneTasks`, `SprintTasks`, `Portfolio`, `PortfolioProjects`, `PortfolioMembers` (ERD) | These are future-state entities for ServizmaProjects product. Create stub models with basic UUID PK and tenant_id. Do not build full feature logic. |
| Communication `event_type` values for CommunicationTrigger | Define a reasonable set: `workorder.status_changed`, `workorder.scheduled`, `invoice.created`, `invoice.overdue`, `invoice.paid`, `quote.sent`, `quote.accepted`, `payment.received`, `appointment.reminder`. Expose as choices. |
| Merge field processing for CommunicationTemplate body | Implement as simple string replacement: `{{customer_name}}`, `{{tech_name}}`, `{{work_order_number}}`, `{{invoice_number}}`, `{{scheduled_date}}` |
| `Social` table — whether Employee (User) social links use `user_id` or `contact_id` FK | Use `user_id` FK directly on Social for employees. `contact_id` is for CRM contacts only. |
| `Accounting` model — relationship to Ledger | Accounting is a balance summary per Customer/Carrier/Bank. Ledger is the immutable transaction log. They are separate systems. |

---

# PART 11 — RECORD NUMBERING SYSTEM

All auto-generated record numbers follow this pattern:

```
{prefix}{2-digit-year}-{zero-padded-sequence}
Example: W26-0001, C26-0042, Q26-1337
```

Implementation using `SequenceTracker`:

```python
# apps/infrastructure/services.py

from django.db import transaction

def generate_record_number(tenant_id, entity_type, prefix, year=None, zero_pad=4):
    """
    Atomically increments SequenceTracker and returns next record number.
    Must be called within a transaction.
    """
    from apps.infrastructure.models import SequenceTracker
    with transaction.atomic():
        tracker = SequenceTracker.all_objects.select_for_update().get_or_create(
            tenant_id=tenant_id,
            entity_type=entity_type,
            year=year
        )[0]
        tracker.last_value += 1
        tracker.save(update_fields=['last_value', 'updated_at'])
        sequence = str(tracker.last_value).zfill(zero_pad)
        if year:
            return f"{prefix}{str(year)[2:]}-{sequence}"
        return f"{prefix}-{sequence}"
```

---

*End of ServizmaDesk SDTA Agent Handoff Document*
*Generated: March 2026*
*All decisions reconciled from full specification library as of this date.*
