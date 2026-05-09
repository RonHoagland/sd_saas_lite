# ServizmaDesk SDTA — Data Models V3
**Document Status:** Working Draft — V3
**Date:** March 2026
**Classification:** Internal — Confidential
**Source:** Derived from `ServizmaDesk_Top_Down_Specifications.md` V1
**Supersedes:** ServizmaDesk SDTA Data Models V2

---

## Document Purpose

This document defines the detailed data model for the ServizmaDesk Tenant App (SDTA). It serves as the authoritative field-level specification for all database models, organized by tier.

**Tasks Completed by this Document:**
- **1A** — Detailed field-level spec for all Lite tier models
- **1B** — Directional field-level spec for Plus/Pro/Enterprise tier models
- **1C** — Delete rules policy (Section 5)

---

## Architectural Mandates

1. **`tenant_id` on every table** — UUIDv4 foreign key for horizontal data isolation.
2. **UUIDv4 primary keys** — All primary and foreign keys use UUIDv4. No auto-incrementing integers.
3. **No Generic Foreign Keys (GFKs)** — Strict PostgreSQL RLS enforcement; no Django content-types framework.
4. **Isolated line item tables** — `QuoteLine`, `WorkOrderLine`, `InvoiceLine` are separate tables; no shared generic line item table.
5. **Exclusive Arc for Notes/Documents** — Single `Note` and `Document` table with nullable FKs to every possible parent entity. A DB-level `CHECK` constraint enforces exactly one FK is populated per row.
6. **Shared Triad Tables** — `Person`, `Contact`, `Address`, `Phone`, `Social` are shared between Customers, Vendors, and Users (Employees).
7. **User → Person Link** — The `User` table does not store name fields directly. Each User record links to a `Person` record via `person_id` FK. The Person record holds `first_name` and `last_name`.
8. **Standard Audit Metadata** — All tables (except M2M junction tables) carry four audit fields: `created_by` (CharField), `created_on` (DateTimeField), `updated_by` (CharField), and `updated_on` (DateTimeField).
    - **Implementation**: `created_on` uses `auto_now_add=True`. `updated_on` uses `auto_now=True` for all models to ensure manual and ORM-level updates are captured.
    - **Storage**: All timestamps are strictly stored in **UTC** (`TIMESTAMPTZ` in PostgreSQL).
    - **Display**: The `TenantPreference.timezone` is used exclusively at the application/UI layer for localized display; it is never used for data storage calculations.

---

# PART 1 — LITE TIER MODELS

The complete foundational model set for the Lite MVP.

---

## 1.1 Identity, Access & Preferences

### `User`
Represents a tenant employee with access to the SDTA. Does not store name fields directly — links to a `Person` record for identity. Phone numbers, addresses, email addresses, and social links are managed via shared Triad tables (`Phone`, `Address`, `Social`). Notes and documents about an employee attach via the `user_id` FK on the `Note` and `Document` tables.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Required, indexed |
| `person_id` | UUID FK → Person | Required — holds first_name / last_name |
| `email` | EmailField | Unique per tenant; used as login credential (work email) |
| `password` | CharField | Hashed (bcrypt/Argon2) |
| `employee_number` | CharField | Auto-generated (E26-0001) |
| `status` | Enum | Active, On Leave, Inactive, Terminated |
| `hire_date` | DateField | Optional |
| `termination_date` | DateField | Nullable — required to release a seat (see seat counting rules) |
| `failed_login_count` | IntegerField | Default: 0. Increments on failed login. Resets on successful login or admin unlock. Account locks when value reaches 5. |
| `force_password_change` | BooleanField | Default: False. Set True when admin resets password; user must change on next login. |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

> **Lockout derivation:** An account is considered locked when `failed_login_count >= 5`. No separate `is_locked` flag is stored. The unlock action resets `failed_login_count` to 0.

> **Seat counting:** Active + On Leave + Inactive count toward the tenant seat limit. Terminated does not. An employee must have `status = Terminated` AND `termination_date` populated to release a seat.

### `EmployeeRole`
Junction table mapping employees to multiple roles.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `employee_id` | UUID FK → User | |
| `role_id` | UUID FK → Role | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `Role`
Defines permission level for a User.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | Administrator, User, Read-Only (Lite); custom in Pro/Enterprise |
| `is_custom` | BooleanField | False for system roles |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_on` | DateTimeField | |

### `RolePermission`
Defines granular CRUD permissions for a Role. See **[Permission Specification](file:///Users/ronhoagland/.gemini/antigravity/brain/63427f0e-2cdd-4ddf-91be-5443c157608b/permission_spec_v1.md)**.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `role_id` | UUID FK → Role | |
| `resource_key` | CharField | Unique within Role (e.g., `service_invoice`) |
| `can_create` | Boolean | |
| `can_view` | Boolean | |
| `can_edit` | Boolean | |
| `can_delete` | Boolean | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `TenantPreference`
Global settings for the tenant. One record per tenant.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Unique |
| `company_name` | CharField | Required |
| `company_logo` | FileField | Stored in object storage |
| `address` | CharField | |
| `city` | CharField | |
| `state` | CharField | |
| `zip` | CharField | |
| `country` | CharField | |
| `phone` | CharField | |
| `fax` | CharField | Optional |
| `email` | EmailField | |
| `website` | URLField | Optional |
| `default_currency` | CharField | e.g. USD, CAD |
| `currency_symbol` | CharField | e.g. $ |
| `decimal_precision` | IntegerField | Default: 2 |
| `timezone` | CharField | IANA timezone string |
| `date_format` | Enum | MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD |
| `phone_country_code` | CharField | e.g. +1 |
| `phone_format` | Enum | US, international, etc. |
| `default_tax_rate` | DecimalField | Percentage |
| `tax_label` | CharField | e.g. "Sales Tax", "VAT" |
| `default_payment_terms` | Enum | Due on Receipt, Net 15, Net 30, Net 45, Net 60, Custom |
| `default_quote_expiration_days` | IntegerField | Default: 30 |
| `fiscal_year_start_month` | IntegerField | 1–12, default: 1 |
| `numbering_reset_period` | Enum | Annual, Never |
| `customer_prefix` | CharField | Default: C |
| `customer_start_number` | IntegerField | Default: 1 — Subject to Forward-Only constraint against SequenceTracker |
| `asset_prefix` | CharField | Default: A |
| `asset_start_number` | IntegerField | |
| `work_order_prefix` | CharField | Default: W |
| `work_order_start_number` | IntegerField | |
| `quote_prefix` | CharField | Default: Q |
| `quote_start_number` | IntegerField | |
| `invoice_prefix` | CharField | Default: I |
| `invoice_start_number` | IntegerField | |
| `payment_prefix` | CharField | Default: P |
| `payment_start_number` | IntegerField | |
| `task_prefix` | CharField | Default: T |
| `task_start_number` | IntegerField | |
| `product_prefix` | CharField | Default: XT |
| `product_start_number` | IntegerField | |
| `employee_prefix` | CharField | Default: E |
| `employee_start_number` | IntegerField | Default: 1 |
| `smtp_host` | CharField | Optional — tenant SMTP |
| `smtp_port` | IntegerField | |
| `smtp_username` | CharField | |
| `smtp_password` | CharField | Encrypted |
| `smtp_use_tls` | BooleanField | |
| `smtp_use_ssl` | BooleanField | |
| `smtp_from_name` | CharField | |
| `smtp_from_email` | EmailField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `UserPreference`
Per-user settings.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | Unique |
| `ui_theme` | Enum | Light, Dark, System |
| `default_landing_page` | CharField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `SessionLog`
Tracks authenticated login sessions.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | |
| `session_id` | CharField | Unique session token identifier |
| `login_at` | DateTimeField | |
| `logout_at` | DateTimeField | Nullable |
| `expiration_at` | DateTimeField | |
| `ip_address` | GenericIPAddressField | |
| `user_agent` | TextField | Raw User-Agent string |
| `permission_snapshot` | JSONB | State of combined permissions at login |
| `browser` | CharField | Parsed |
| `os` | CharField | Parsed |
| `device_type` | Enum | Mobile, Desktop |
| `created_by` | CharField | Username of the logging-in user |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `AuditEvent`
Immutable history log. Never deleted.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `session_id` | UUID FK → SessionLog | |
| `user_id` | UUID FK → User | |
| `event_timestamp` | DateTimeField | |
| `action` | Enum | Created, Updated, Deleted, Approved, Voided, etc. |
| `entity_type` | CharField | e.g. WorkOrder, Invoice, Customer |
| `entity_id` | UUIDField | Record identifier |
| `record_number` | CharField | Human-readable (e.g. W26-0042) |
| `details` | JSONField | Contextual change detail |
| `created_by` | CharField | Username of the acting user, or 'System' for background tasks |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `PasswordResetToken`
Time-limited single-use token for password resets.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | |
| `token` | CharField | Hashed |
| `expires_at` | DateTimeField | |
| `used_at` | DateTimeField | Nullable — set on first use |
| `created_by` | CharField | Username of the admin who initiated the reset, or 'System' |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

---

## 1.2 Core CRM — Triad Architecture

### `Customer`
The top-level billing entity.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_number` | CharField | Auto-generated (e.g. C26-0001) |
| `status` | Enum | Active, Inactive |
| `account_type` | Enum | Residential, Commercial |
| `company_name` | CharField | Required for Commercial, optional for Residential |
| `assigned_to` | UUID FK → User | Optional |
| `lead_source` | CharField | Dropdown (customizable list) |
| `tax_exempt` | BooleanField | Default: False |
| `customer_since` | DateField | Optional |
| `account_number` | CharField | Required |
| `account_terms` | CharField | Dropdown (customizable list) |
| `credit_limit` | DecimalField | Required |
| `credit_status` | Enum | Good, Fair, Poor |
| `tax_rate` | DecimalField | Optional — overrides tenant default if set |
| `tags` | ArrayField/JSON | Free-text tags |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `Person`
Permanent human identity. Deliberately minimal — only identity fields. Audit metadata is standard per Mandate 8.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `first_name` | CharField | Required |
| `last_name` | CharField | Required |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

> **Note:** No record number — Person is handled behind the scenes and is never shown as a standalone list to the user.

### `Contact`
Bridge table linking a `Person` to a `Customer` (or `Vendor`).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `person_id` | UUID FK → Person | Required |
| `customer_id` | UUID FK → Customer | Nullable — one of customer or vendor required |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `role_title` | CharField | Optional |
| `department` | CharField | Optional |
| `is_primary` | BooleanField | One primary per Customer |
| `status` | Enum | Active, Left |
| `start_date` | DateField | Optional |
| `left_date` | DateField | Nullable — set when status → Left |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

> **Constraint:** Exactly one of `customer_id` or `vendor_id` must be populated (DB `CHECK` constraint).

### `Address`
Physical or mailing addresses. Shared across entities.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `asset_id` | UUID FK → Asset | Nullable — physical site |
| `user_id` | UUID FK → User | Nullable — employee address |
| `address_type` | Enum | Service, Billing, Mailing, Other |
| `is_primary` | BooleanField | |
| `street` | CharField | |
| `city` | CharField | |
| `state` | CharField | |
| `zip` | CharField | |
| `country` | CharField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

> **Constraint:** Exactly one parent FK populated (Customer, Contact, Vendor, User, or Asset).

### `Phone`
Phone numbers. Shared across entities. Duplicates permitted.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `user_id` | UUID FK → User | Nullable |
| `phone_type` | Enum | Mobile, Office, Home, Fax, Other |
| `number` | CharField | |
| `is_primary` | BooleanField | |
| `extension` | CharField | Optional |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

> **Constraint:** Exactly one parent FK populated.

### `Social`
Emails, social media links, web profiles. Shared across entities.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `person_id` | UUID FK → Person | Nullable |
| `user_id` | UUID FK → User | Nullable — employee social/email |
| `type` | Enum | Email, Facebook, LinkedIn, Instagram, Twitter/X, YouTube, Website, Other |
| `value` | CharField | Email address or full URL |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

> **Constraint:** At least one parent FK required (Contact, Person, or User). Links to Person for personal identities and Contact for entity-scoped (Customer/Vendor) identities.

---

## 1.3 Assets & Product Catalog

### `Asset`
Customer-owned equipment. The primary organizing entity of the platform.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `asset_number` | CharField | Auto-generated (e.g. A26-0001) |
| `customer_id` | UUID FK → Customer | Required |
| `address_id` | UUID FK → Address | Optional — defaults to primary service address |
| `parent_asset_id` | UUID FK → Asset | Nullable — for nested/child assets (Pro/Enterprise) |
| `status` | Enum | Active, Inactive, Decommissioned |
| `asset_category` | CharField | Dropdown (customizable): HVAC, Plumbing, Electrical, Appliance, Other |
| `asset_type` | CharField | Dropdown (customizable per category) |
| `make` | CharField | Manufacturer |
| `model` | CharField | |
| `serial_number` | CharField | |
| `installation_date` | DateField | Optional |
| `condition` | Enum | Excellent, Good, Fair, Poor |
| `refrigerant_type` | CharField | Optional — HVAC specific |
| `capacity_size` | CharField | Optional — e.g. "3 Ton", "50 Gallon" |
| `warranty_start_date` | DateField | Optional |
| `warranty_end_date` | DateField | Optional |
| `warranty_provider` | CharField | Optional |
| `warranty_notes` | TextField | Optional |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

> **Calculated field:** `age` (from `installation_date` — display only), `warranty_status` (Active / Expired / N/A — display only).

### `Product`
Central catalog of all products and services. Refers to both inventory and labor.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `product_number` | CharField | Auto-generated (XT-0001) |
| `name` | CharField | Required |
| `type` | Enum | Service, Product - Inventory, Product - Non-Inventory |
| `category` | CharField | Dropdown (customizable) |
| `sku` | CharField | Optional |
| `unit_cost` | DecimalField | Internal cost |
| `unit_price` | DecimalField | Customer price |
| `description` | TextField | |
| `taxable` | BooleanField | Default: True |
| `is_bundle` | BooleanField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `BundleItem`
Items within a Product Bundle.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `bundle_id` | UUID FK → Product | The parent bundle product |
| `product_id` | UUID FK → Product | The included item |
| `quantity` | DecimalField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `Project`
A collection of work orders, quotes, and invoices for a larger job.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `project_number` | CharField | Auto-generated (e.g. P26-0001) |
| `customer_id` | UUID FK → Customer | Required |
| `name` | CharField | Required |
| `description` | TextField | Optional |
| `status` | Enum | Open, In Progress, On Hold, Completed, Cancelled |
| `start_date` | DateField | Optional |
| `end_date` | DateField | Optional |
| `assigned_to` | UUID FK → User | Optional |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

---

## 1.4 Service Delivery & Financials

### `WorkOrder`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_order_number` | CharField | Auto-generated (e.g. W26-0001) |
| `customer_id` | UUID FK → Customer | Required |
| `project_id` | UUID FK → Project | Nullable |
| `quote_id` | UUID FK → Quote | Nullable — backlink if converted from quote |
| `vehicle_id` | UUID FK → Vehicle | Nullable — Fleet add-on only |
| `converted_to_invoice_id` | UUID FK → Invoice | Nullable — backlink if converted to invoice |
| `status` | Enum | Draft, Scheduled, In Progress, On Hold, Completed, Closed, Cancelled |
| `priority` | Enum | Low, Normal, High, Urgent |
| `work_order_type` | CharField | Dropdown (customizable) |
| `assigned_to` | UUID FK → User | Nullable |
| `scheduled_date` | DateTimeField | |
| `hold_date` | DateTimeField | Nullable — required when status is On Hold |
| `hold_reason` | TextField | Nullable — required when status is On Hold |
| `closed_at` | DateTimeField | Nullable — required when status is Closed |
| `estimated_duration` | DurationField | |
| `title` | CharField | |
| `description` | TextField | |
| `internal_notes` | TextField | |
| `customer_facing_notes` | TextField | Plus+ only |
| `is_recurring` | BooleanField | |
| `recurrence_pattern` | JSONField | Nullable — stores recurrence config |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `WorkOrderAsset` (M2M junction)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_order_id` | UUID FK → WorkOrder | |
| `asset_id` | UUID FK → Asset | |

### `WorkOrderLine`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_order_id` | UUID FK → WorkOrder | |
| `product_id` | UUID FK → Product | Nullable — can be free-text |
| `item_name` | CharField | |
| `item_type` | Enum | Service, Product - Inventory, Product - Non-Inventory |
| `description` | TextField | |
| `unit_cost` | DecimalField | |
| `unit_price` | DecimalField | |
| `quantity` | DecimalField | |
| `is_discount` | BooleanField | Default: False. If True, forced tax_charged = False |
| `is_surcharge` | BooleanField | Default: False. Labeling only |
| `is_tax_charged` | BooleanField | Default: True. |
| `sort_order` | IntegerField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `WorkOrderChecklistItem`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_order_id` | UUID FK → WorkOrder | |
| `label` | CharField | |
| `is_complete` | BooleanField | |
| `notes` | TextField | Optional |
| `sort_order` | IntegerField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `WorkOrderSubtask`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_order_id` | UUID FK → WorkOrder | |
| `name` | CharField | |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Open, In Progress, Completed |
| `due_date` | DateField | |
| `notes` | TextField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `TimeEntry`
Clock-in/out records per employee per Work Order.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_order_id` | UUID FK → WorkOrder | |
| `user_id` | UUID FK → User | |
| `clock_in` | DateTimeField | |
| `clock_out` | DateTimeField | Nullable |
| `total_hours` | DecimalField | Calculated |
| `labor_cost` | DecimalField | Calculated from hours × employee rate |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `Quote`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `quote_number` | CharField | Auto-generated (e.g. Q26-0001) |
| `customer_id` | UUID FK → Customer | Required |
| `converted_to_work_order_id` | UUID FK → WorkOrder | Nullable — backlink if converted (formerly work_order_id) |
| `converted_to_invoice_id` | UUID FK → Invoice | Nullable — backlink if converted |
| `project_id` | UUID FK → Project | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Draft, Sent, Viewed, Accepted, Rejected, Expired, Converted |
| `quote_date` | DateField | Defaults to today |
| `expiration_date` | DateField | |
| `tax_rate` | DecimalField | Frozen at time of creation; defaults from Customer/Tenant |
| `notes` | TextField | Customer-visible |
| `internal_notes` | TextField | Not visible to customer |
| `deposit_required` | BooleanField | Plus+ |
| `deposit_type` | Enum | Fixed, Percentage |
| `deposit_value` | DecimalField | |
| `approval_name` | CharField | Who approved (Plus+) |
| `approval_at` | DateTimeField | When approved |
| `approval_ip` | GenericIPAddressField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `QuoteAsset` (M2M junction)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `quote_id` | UUID FK → Quote | |
| `asset_id` | UUID FK → Asset | |

### `QuoteLine`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `quote_id` | UUID FK → Quote | |
| `product_id` | UUID FK → Product | Nullable |
| `group_label` | CharField | Optional — for line item grouping |
| `item_name` | CharField | |
| `item_type` | Enum | Service, Product - Inventory, Product - Non-Inventory |
| `sku` | CharField | Optional |
| `description` | TextField | |
| `unit_cost` | DecimalField | |
| `unit_price` | DecimalField | |
| `quantity` | DecimalField | |
| `is_discount` | BooleanField | Default: False. Forces is_tax_charged = False |
| `is_surcharge` | BooleanField | Default: False. Labeling only |
| `is_tax_charged` | BooleanField | Default: True. |
| `visible_to_customer` | BooleanField | |
| `sort_order` | IntegerField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `Invoice`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `invoice_number` | CharField | Auto-generated (e.g. I26-0001) |
| `customer_id` | UUID FK → Customer | Required |
| `work_order_id` | UUID FK → WorkOrder | Nullable — backlink if converted from work order |
| `quote_id` | UUID FK → Quote | Nullable — backlink if converted from quote |
| `project_id` | UUID FK → Project | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Draft, Issued, Viewed, Partially Paid, Paid, Overdue, Void, Written Off |
| `invoice_date` | DateField | Defaults to today |
| `due_date` | DateField | |
| `due_date_method` | Enum | Creation Date + N, Sent Date + N, WO Completion + N, Manual |
| `due_date_offset_days` | IntegerField | |
| `tax_rate` | DecimalField | Frozen at time of issue; defaults from Customer/Tenant |
| `line_item_total` | DecimalField | Calculated: Sum of lines (incl. discounts) |
| `line_item_tax_total` | DecimalField | Calculated: Total tax on taxable lines |
| `invoice_total` | DecimalField | Calculated: line_item_total + line_item_tax_total |
| `stripe_payment_link_id` | CharField | Nullable |
| `stripe_payment_link_url` | URLField | Nullable |
| `deposit_applied` | DecimalField | From quote deposit |
| `notes` | TextField | Customer-visible |
| `internal_notes` | TextField | |
| `is_recurring` | BooleanField | Plus+ |
| `recurrence_pattern` | JSONField | Nullable |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `InvoiceAsset` (M2M junction)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `invoice_id` | UUID FK → Invoice | |
| `asset_id` | UUID FK → Asset | |

### `InvoiceLine`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `invoice_id` | UUID FK → Invoice | |
| `product_id` | UUID FK → Product | Nullable |
| `group_label` | CharField | Optional |
| `item_name` | CharField | |
| `item_type` | Enum | Service, Product - Inventory, Product - Non-Inventory |
| `sku` | CharField | Optional |
| `description` | TextField | |
| `unit_cost` | DecimalField | |
| `unit_price` | DecimalField | |
| `quantity` | DecimalField | |
| `is_discount` | BooleanField | Default: False. Forces is_tax_charged = False |
| `is_surcharge` | BooleanField | Default: False. Labeling only |
| `is_tax_charged` | BooleanField | Default: True. |
| `visible_to_customer` | BooleanField | |
| `sort_order` | IntegerField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `Payment`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `payment_number` | CharField | Auto-generated (e.g. P26-0001) |
| `invoice_id` | UUID FK → Invoice | Required |
| `customer_id` | UUID FK → Customer | Denormalized for reporting |
| `payment_date` | DateField | |
| `amount` | DecimalField | |
| `payment_method` | Enum | Credit/Debit Card, Cash, Check, Bank Transfer, Other |
| `reference_number` | CharField | For check/transfer |
| `stripe_payment_intent_id` | CharField | Nullable — Stripe payments |
| `notes` | TextField | |
| `created_by` | CharField | Username of actor, or 'System' for Stripe webhook payments |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `LedgerEntry`
### `Ledger`
The authoritative financial net balance trace for all accounts.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `payment_id` | UUID FK → Payment | Link to transaction |
| `customer_id` | UUID FK → Customer | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `purchasing_id`| UUID FK → Purchasing | Link to PO |
| `invoice_id` | UUID FK → Invoice | Link to Invoice |
| `entry_type` | Enum | Debit, Credit |
| `amount` | Decimal | |
| `running_balance`| Decimal | Calculated at write-time |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---

## 1.5 Checklist Templates

### `ChecklistTemplate`
Reusable checklist structures that auto-apply to Work Orders by type.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | Required |
| `work_order_type` | CharField | Optional — auto-applies when WO type matches |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `ChecklistTemplateItem`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `template_id` | UUID FK → ChecklistTemplate | |
| `label` | CharField | |
| `sort_order` | IntegerField | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

---

## 1.6 General Purpose Tasks

### `Task`
Standalone tasks not tied to a specific Work Order. (For subtasks, see `WorkOrderSubtask`).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `task_number` | CharField | Auto-generated (T26-0001) |
| `title` | CharField | |
| `description` | TextField | |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Open, In Progress, Completed |
| `due_date` | DateField | |
| `priority` | Enum | Low, Normal, High, Urgent |
| `customer_id` | UUID FK → Customer | Optional |
| `asset_id` | UUID FK → Asset | Optional |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 1.7 Attachments — Exclusive Arc Pattern

### `Note`
Master internal commentary record. A DB-level `CHECK` constraint enforces exactly one parent FK is populated.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `note_type` | Enum | Internal Note, Call, Email, Site Visit, Customer Comment, Reminder |
| `body` | TextField | |
| `customer_id` | UUID FK | |
| `contact_id` | UUID FK | |
| `quote_id` | UUID FK | |
| `invoice_id` | UUID FK | |
| `work_order_id` | UUID FK | |
| `asset_id` | UUID FK | |
| `payment_id` | UUID FK | |
| `user_id` | UUID FK | (Employee) |
| `vendor_id` | UUID FK | (Plus+) |
| `purchase_order_id`| UUID FK | (Plus+) |
| `project_id` | UUID FK | (Plus+) |
| `task_id` | UUID FK | |
| `vehicle_id` | UUID FK | (Fleet Add-on) |
| `service_request_id`| UUID FK | (Lite/Plus) |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Document`
Master file attachment record. A DB-level `CHECK` constraint enforces exactly one parent FK is populated.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `file_name` | CharField | |
| `file_key` | CharField | S3/Spaces key |
| `file_size_bytes` | BigIntegerField| |
| `mime_type` | CharField | |
| `customer_id` | UUID FK | |
| `contact_id` | UUID FK | |
| `person_id` | UUID FK | (Identity docs) |
| `quote_id` | UUID FK | |
| `invoice_id` | UUID FK | |
| `work_order_id` | UUID FK | |
| `asset_id` | UUID FK | |
| `payment_id` | UUID FK | |
| `user_id` | UUID FK | (Employee docs) |
| `vendor_id` | UUID FK | (Plus+) |
| `purchase_order_id`| UUID FK | (Plus+) |
| `project_id` | UUID FK | (Plus+) |
| `task_id` | UUID FK | |
| `vehicle_id` | UUID FK | (Fleet Add-on) |
| `service_request_id`| UUID FK | (Lite/Plus) |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

# PART 2 — PLUS / PRO / ENTERPRISE TIER MODELS

Optional modules and advanced entities gated by tenant subscription.

---

## 2.1 Maintenance Plans (Plus+)

### `MaintenancePlan`
Recurring service schedules for Assets.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | |
| `name` | CharField | e.g. "Annual HVAC Tune-Up" |
| `status` | Enum | Active, Paused, Expired, Cancelled |
| `frequency` | Enum | Daily, Weekly, Monthly, Quarterly, Semi-Annual, Annual, Custom |
| `visits_per_period`| Integer | |
| `start_date` | DateField | |
| `end_date` | DateField | Optional |
| `renewal_type` | Enum | Manual, Auto-Renew |
| `checklist_template_id` | UUID FK → ChecklistTemplate | Auto-applies to generated WOs |
| `default_assignee_id` | UUID FK → User | |
| `auto_gen_work_orders` | Boolean | |
| `advance_gen_days` | Integer | How far ahead to create upcoming WOs |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `MaintenancePlanAsset`
Junction table linking plan to specific assets.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `plan_id` | UUID FK → MaintenancePlan | |
| `asset_id` | UUID FK → Asset | |

---

## 2.2 Purchasing & Vendors (Plus+)

### `Vendor`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vendor_name` | CharField | Required |
| `account_number` | CharField | Optional |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `PurchaseOrder`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `po_number` | CharField | PO26-0001 |
| `vendor_id` | UUID FK → Vendor | |
| `status` | Enum | Draft, Sent, Partially Received, Received, Cancelled |
| `order_date` | DateField | |
| `expected_date` | DateField | |
| `work_order_id` | UUID FK → WorkOrder | Optional |
| `project_id` | UUID FK → Project | Optional |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `PurchaseOrderLine`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `purchase_order_id` | UUID FK → PurchaseOrder| |
| `product_id` | UUID FK → Product | |
| `quantity_ordered` | Decimal | |
| `quantity_received`| Decimal | |
| `unit_cost` | Decimal | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 2.3 Warehouse & Inventory (Plus+)

### `Warehouse`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `warehouse_number` | CharField | WH26-0001 |
| `name` | CharField | |
| `type` | Enum | Physical Hub, Mobile (Van/Truck) |
| `status` | Enum | Active, Inactive |
| `assigned_user_id` | UUID FK → User | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `SubLocation`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `warehouse_id` | UUID FK → Warehouse | |
| `location_number` | CharField | e.g. B1.S1 (Bin 1, Shelf 1) |
| `location_type` | Enum | Area, Bin, Shelf, Section, Cabinet, Room |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `InventoryStock`
Tracks quantity per product, per sub-location.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `product_id` | UUID FK → Product | |
| `sub_location_id` | UUID FK → SubLocation | |
| `quantity_on_hand`| Decimal | |
| `serial_number` | CharField | Nullable — for serialized tracking (Pro/Enterprise) |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 2.4 Fleet Management (Pro/Enterprise Add-on)

### `Vehicle`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vehicle_number` | CharField | V26-0001 |
| `status` | Enum | Active, Out of Service, Decommissioned |
| `year` | Integer | |
| `make` | CharField | |
| `model` | CharField | |
| `vin` | CharField | |
| `license_plate` | CharField | |
| `license_state` | CharField | |
| `vehicle_type` | CharField | Van, Truck, Car, etc. |
| `assigned_user_id` | UUID FK → User | |
| `odometer_current` | Integer | |
| `insurance_expiry` | DateField | |
| `registration_expiry`| DateField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `VehicleMaintenance`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vehicle_id` | UUID FK → Vehicle | |
| `maintenance_number`| CharField | M26-0001 |
| `maintenance_type` | CharField | |
| `status` | Enum | Scheduled, Completed, Overdue, Cancelled |
| `scheduled_date` | DateField | |
| `completed_date` | DateField | |
| `odometer_at_service`| Integer | |
| `cost` | Decimal | |
| `performed_by` | Enum | In-House, External Shop |
| `vendor_name` | CharField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `MileageLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vehicle_id` | UUID FK → Vehicle | |
| `user_id` | UUID FK → User | (Driver) |
| `log_date` | DateField | |
| `odometer_start` | Integer | |
| `odometer_end` | Integer | |
| `miles_driven` | Integer | |
| `purpose` | CharField | |
| `work_order_id` | UUID FK → WorkOrder | Optional |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 1.8 System Utilities & Operations

### `SequenceTracker`
Tenant-scoped auto-incrementing counters for collision-free record number generation.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `entity_type` | CharField | e.g. Customer, WorkOrder, Invoice |
| `year` | IntegerField | Nullable — for annual reset |
| `last_value` | IntegerField | Current counter value — seeding: start_number - 1 |
| `created_by` | CharField | Username of actor whose action triggered the increment, or 'System' |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username of actor whose action triggered the increment, or 'System' |
| `updated_on` | DateTimeField | |

### `Notification`
In-app dismissible banner alerts for Administrators.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | Nullable — null means all admins |
| `message` | TextField | |
| `severity` | Enum | Info, Warning, Error |
| `is_dismissed` | BooleanField | |
| `created_by` | CharField | Username of actor, or 'System' for webhook/background-generated notifications |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `StripeConnection`
Tenant's Stripe Connect integration state.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Unique |
| `stripe_account_id` | CharField | Stripe connected account ID |
| `access_token` | CharField | Encrypted OAuth token |
| `is_active` | BooleanField | |
| `connected_at` | DateTimeField | |
| `disconnected_at` | DateTimeField | Nullable |
| `created_by` | CharField | Username of the admin who connected Stripe |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `StripeConnectionLog`
Audit trail for Stripe connect/disconnect events.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `event` | Enum | Connected, Disconnected, Token Revoked |
| `occurred_at` | DateTimeField | |
| `details` | JSONField | |
| `created_by` | CharField | Username of actor, or 'System' for token revocation events |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `StripeAPIRequestLog`
Outgoing Stripe API requests for debugging.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `endpoint` | CharField | |
| `method` | CharField | GET, POST, etc. |
| `response_status` | IntegerField | HTTP status code |
| `requested_at` | DateTimeField | |
| `duration_ms` | IntegerField | |
| `error_message` | TextField | Nullable |
| `created_by` | CharField | Username of actor whose action triggered the API call, or 'System' |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `WebhookLog`
Idempotency tracker for incoming Stripe events.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `stripe_event_id` | CharField | Unique — prevents duplicate processing |
| `event_type` | CharField | e.g. payment_intent.succeeded |
| `processed_at` | DateTimeField | |
| `status` | Enum | Processed, Failed, Skipped |
| `created_by` | CharField | 'System' — webhooks are inbound with no user session |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `EmailDeliveryLog`
Tracks transactional emails sent to User accounts via Postmark.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | |
| `email_type` | CharField | PasswordReset, WelcomeInvite, etc. |
| `to_address` | EmailField | |
| `sent_at` | DateTimeField | |
| `status` | Enum | Sent, Delivered, Bounced, Failed |
| `postmark_message_id` | CharField | |
| `created_by` | CharField | Username of admin who triggered the email, or 'System' |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `SystemErrorLog`
Server-side capture of exceptions, scoped to UI action.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Nullable |
| `user_id` | UUID FK → User | Nullable |
| `error_type` | CharField | Exception class name |
| `message` | TextField | |
| `traceback` | TextField | Never exposed to user |
| `occurred_at` | DateTimeField | |
| `request_path` | CharField | |
| `created_by` | CharField | Username of the user whose request caused the error, or 'System' |
| `created_on` | DateTimeField | |
| `updated_on` | DateTimeField | |
| `updated_on` | DateTimeField | |

### `StatusChangeLog`
Formal record of every status transition. Required for auditing and financial integrity.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Required |
| `entity_name` | CharField | e.g. WorkOrder, Invoice, Quote |
| `record_id` | UUIDField | ID of the record being changed |
| `pre_status` | CharField | Status before the change |
| `post_status` | CharField | Status after the change |
| `reason` | TextField | Required for certain transitions (Voids, Reversions) |
| `acted_by` | UUID FK → User | Optional link to User model |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |

---

## 1.9 Tenant Infrastructure (SDTA Local)

### `TenantState`
Local cache of tenant subscription state, synced from SDP.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Unique |
| `tier` | Enum | Lite, Plus, Pro, Enterprise |
| `status` | Enum | Active, Suspended, Read-Only |
| `seat_limit` | IntegerField | |
| `storage_limit_bytes` | BigIntegerField | |
| `last_synced_at` | DateTimeField | |
| `created_by` | CharField | 'System' — created by SDP provisioning |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | 'System' — updated by SDP sync |
| `updated_on` | DateTimeField | |

### `StorageTracker`
Running tally of tenant Document upload storage consumption.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Unique |
| `total_bytes_used` | BigIntegerField | |
| `created_by` | CharField | 'System' — created during provisioning |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username of actor whose upload/delete changed the tally, or 'System' |
| `updated_on` | DateTimeField | |

### `DataExportLog`
Audit of CSV export requests.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | |
| `entity_type` | CharField | Customers, Invoices, etc. |
| `requested_at` | DateTimeField | |
| `status` | Enum | Queued, Complete, Failed |
| `created_by` | CharField | Username of the admin who requested the export |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `TenantSyncLog`
Tracks SDTA ↔ SDP synchronization attempts.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `sync_type` | Enum | ProvisionTenant, UpdateStatus, UpdateLimits, UnlockAdmin, ForceSync |
| `status` | Enum | Success, Failed |
| `response_code` | Integer | |
| `occurred_at` | DateTimeField | |
| `created_by` | CharField | 'System' |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | 'System' |
| `updated_on` | DateTimeField | |

### `TenantAddOn`
Individual feature or limit overrides active for the tenant.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `addon_type` | Enum | Fleet, SMS_Extra, Storage_+5GB, Storage_+10GB, QB_CSV_Export |
| `status` | Enum | Active, Cancelled, Expired |
| `unit_limit` | Integer | Nullable — for capacity-based add-ons |
| `purchased_on` | DateTimeField | |
| `created_by` | CharField | 'System' — updated by SDP sync |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | 'System' — updated by SDP sync |
| `updated_on` | DateTimeField | |

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `sync_type` | CharField | SubscriptionUpdate, SeatLimitChange, etc. |
| `occurred_at` | DateTimeField | |
| `status` | Enum | Success, Failed |
| `details` | JSONField | |
| `created_by` | CharField | 'System' — sync operations are automated |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |
# PART 2 — PLUS / PRO / ENTERPRISE TIER MODELS

Optional modules and advanced entities gated by tenant subscription tier or add-ons.

---

## 2.1 Maintenance Plans (Plus+)
Recurring service schedules for Assets.

### `MaintenancePlan`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | |
| `name` | CharField | e.g. "Annual HVAC Tune-Up" |
| `status` | Enum | Active, Paused, Expired, Cancelled |
| `frequency` | Enum | Daily, Weekly, Monthly, Quarterly, Semi-Annual, Annual, Custom |
| `visits_per_period`| Integer | |
| `start_date` | DateField | |
| `end_date` | DateField | Optional |
| `renewal_type` | Enum | Manual, Auto-Renew |
| `checklist_template_id` | UUID FK → ChecklistTemplate | Auto-applies to generated WOs |
| `default_assignee_id` | UUID FK → User | |
| `auto_gen_work_orders` | Boolean | |
| `advance_gen_days` | Integer | How far ahead to create upcoming WOs |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `MaintenancePlanAsset`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `plan_id` | UUID FK → MaintenancePlan | |
| `asset_id` | UUID FK → Asset | |

---

## 2.2 Purchasing & Vendors (Plus+)

### `Vendor`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vendor_name` | CharField | Required |
| `account_number` | CharField | Optional |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Architecture:** Contacts, Addresses, Phones, and Socials link to Vendor using the same shared Triad tables as Customers.

### `PurchaseOrder`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `po_number` | CharField | PO26-0001 |
| `vendor_id` | UUID FK → Vendor | |
| `status` | Enum | Draft, Sent, Partially Received, Received, Cancelled |
| `order_date` | DateField | |
| `expected_date` | DateField | |
| `work_order_id` | UUID FK → WorkOrder | Optional |
| `project_id` | UUID FK → Project | Optional |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `PurchaseOrderLine`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `purchase_order_id` | UUID FK → PurchaseOrder| |
| `product_id` | UUID FK → Product | |
| `quantity_ordered` | Decimal | |
| `quantity_received`| Decimal | |
| `unit_cost` | Decimal | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 2.3 Warehouse & Inventory (Plus+)

### `Warehouse`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `warehouse_number` | CharField | WH26-0001 |
| `name` | CharField | |
| `type` | Enum | Physical Hub, Mobile (Van/Truck) |
| `status` | Enum | Active, Inactive |
| `assigned_user_id` | UUID FK → User | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `SubLocation`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `warehouse_id` | UUID FK → Warehouse | |
| `location_number` | CharField | e.g. B1.S1 (Bin 1, Shelf 1) |
| `location_type` | Enum | Area, Bin, Shelf, Section, Cabinet, Room |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `InventoryStock`
Tracks quantity per product, per sub-location.
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `product_id` | UUID FK → Product | |
| `sub_location_id` | UUID FK → SubLocation | |
| `quantity_on_hand`| Decimal | |
| `serial_number` | CharField | Nullable — for serialized tracking (Pro/Enterprise) |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 2.4 Advanced Pricing & Accounting (Pro+)

### `Pricebook`
Master pricing overrides for Products.
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | |
| `is_active` | Boolean | |
| `notes` | TextField | |

### `PricebookEntry`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `pricebook_id` | UUID FK → Pricebook | |
| `product_id` | UUID FK → Product | |
| `price` | Decimal | Overrides standard Product price |

---

## 2.5 Service Requests (Lite/Plus)

### `ServiceRequest`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `request_number` | CharField | SR26-0001 |
| `customer_id` | UUID FK → Customer | Nullable (for new leads) |
| `status` | Enum | New, Triaged, Converted to Work Order, Converted to Quote, Cancelled |
| `issue_category`| CharField | Dropdown |
| `urgency` | Enum | Low, Normal, High, Emergency |
| `description` | TextField | |
| `created_by` | CharField | 'System' if from widget |
| `created_on` | DateTimeField | |

---

# PART 3 — FLEET MANAGEMENT ADD-ON (Pro/Enterprise)

### `Vehicle`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vehicle_number` | CharField | V26-0001 |
| `status` | Enum | Active, Out of Service, Decommissioned |
| `year` | Integer | |
| `make` | CharField | |
| `model` | CharField | |
| `vin` | CharField | |
| `license_plate` | CharField | |
| `assigned_user_id`| UUID FK → User | |
| `odometer_current`| Integer | |

### `MileageLog`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vehicle_id` | UUID FK → Vehicle | |
| `user_id` | UUID FK → User | Driver |
| `log_date` | DateField | |
| `odometer_start` | Integer | |
| `odometer_end` | Integer | |
| `miles_driven` | Integer | Calculated |
| `work_order_id` | UUID FK → WorkOrder | Optional |

---

# PART 4 — AUTOMATION & WORKFLOW (Pro/Enterprise)

### `WorkflowTemplate`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | e.g. "Residential HVAC Install SOP" |
| `trigger_event` | Enum | WO Status Change, Inventory Low, etc. |

### `WorkflowStep`
| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `template_id` | UUID FK → WorkflowTemplate| |
| `step_name` | CharField | |
| `sort_order` | Integer | |

---

# PART 5 — DELETE RULES (Task 1C)

## 5.1 Policy Overview
If a **top-level entity** has any **child records**, it **cannot be deleted**. The user must delete all children before the parent.

> **Top-level entities:** Customer, Asset, Work Order, Quote, Invoice, Product, Vendor, Project, Vehicle, Task

## 5.3 Delete Rules Per Entity


For key entities where historical integrity matters, soft-delete (setting `status = Inactive` or `status = Cancelled`) is strongly preferred over hard delete. The system should surface this option to the user before offering delete in appropriate contexts.

| Entity | Preferred Alternative to Delete |
|---|---|
| Customer | Set Status = Inactive |
| Asset | Set Status = Decommissioned |
| Work Order | Set Status = Cancelled |
| Quote | Set Status = Expired or Rejected |
| Invoice | Set Status = Void |
| Employee | Set Status = Inactive |

---

*End of ServizmaDesk Data Models V3*
