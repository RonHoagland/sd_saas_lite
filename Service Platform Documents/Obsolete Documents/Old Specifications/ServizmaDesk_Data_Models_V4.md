# ServizmaDesk SDTA — Data Models V4
**Document Status:** Working Draft — V4
**Date:** March 2026
**Classification:** Internal — Confidential
**Source:** Derived from `SD_System_ERD__Base_System_V7.pdf` and `ServizmaDesk_Top_Down_Specifications_V3.md`
**Supersedes:** ServizmaDesk SDTA Data Models V3

---

## Document Purpose

This document defines the detailed data model for the ServizmaDesk Tenant App (SDTA). It serves as the authoritative field-level specification for all database models, organized by tier.

> **ERD Naming Note:** The ERD uses "Inventory" as the entity name throughout. In specifications and code, this entity is called `Product`. Product in specs = Inventory in ERD.

---

## Architectural Mandates

1. **`tenant_id` on every table** — UUIDv4 foreign key for horizontal data isolation.
2. **UUIDv4 primary keys** — All primary and foreign keys use UUIDv4. No auto-incrementing integers.
3. **No Generic Foreign Keys (GFKs)** — Strict PostgreSQL RLS enforcement; no Django content-types framework.
4. **Isolated line item tables** — `QuoteLine`, `WorkOrderLine`, `InvoiceLine`, `PurchaseOrderLine`, `RequisitionLine` are separate tables; no shared generic line item table.
5. **Exclusive Arc for Notes/Documents** — Single `Note` and `Document` table with nullable FKs to every possible parent entity. A DB-level `CHECK` constraint enforces exactly one FK is populated per row.
6. **Shared Triad Tables** — `Person`, `Contact`, `Address`, `Phone`, `Social` are shared between Customers, Vendors, Carriers, Banks, and Users (Employees).
7. **User → Person Link** — The `User` table does not store name fields directly. Each User record links to a `Person` record via `person_id` FK. The Person record holds `first_name` and `last_name`.
8. **Standard Audit Metadata** — All tables (except M2M junction tables) carry four audit fields: `created_by` (CharField), `created_on` (DateTimeField), `updated_by` (CharField), and `updated_on` (DateTimeField).
    - **Implementation**: `created_on` uses `auto_now_add=True`. `updated_on` uses `auto_now=True`.
    - **Storage**: All timestamps stored in **UTC** (`TIMESTAMPTZ` in PostgreSQL).
    - **Display**: `TenantPreference.timezone` used exclusively at the UI layer for localized display.
9. **One Asset per Work Order** — Work Orders link to exactly one Asset via a direct FK. Multi-asset coordination is handled via WorkGroups.

---

# PART 1 — LITE TIER MODELS

The complete foundational model set available to all tiers.

---

## 1.1 Identity, Access & Preferences

### `User`
Represents a tenant employee with access to the SDTA. Links to a `Person` record for identity. Phone numbers, addresses, emails, and social links managed via shared Triad tables.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Required, indexed |
| `person_id` | UUID FK → Person | Required — holds first_name / last_name |
| `department_id` | UUID FK → Department | Nullable |
| `position_id` | UUID FK → Position | Nullable (Plus+) |
| `email` | EmailField | Unique per tenant; login credential |
| `password` | CharField | Hashed (bcrypt/Argon2) |
| `employee_number` | CharField | Auto-generated (E26-0001) |
| `status` | Enum | Active, On Leave, Inactive, Terminated |
| `hire_date` | DateField | Optional |
| `termination_date` | DateField | Nullable — required to release a seat |
| `failed_login_count` | IntegerField | Default: 0. Account locks at 5. |
| `force_password_change` | BooleanField | Default: False |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Lockout:** Account locked when `failed_login_count >= 5`. Unlock resets to 0.

> **Seat counting:** Active + On Leave + Inactive count toward seat limit. Terminated does not. Requires `status = Terminated` AND `termination_date` populated to release a seat.

### `Department`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | Required |
| `status` | Enum | Active, Inactive |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Role`
Defines permission level for a User.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | Administrator, User, Read-Only (Lite); custom in Pro/Enterprise |
| `is_custom` | BooleanField | False for system roles |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

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

### `RolePermission`
Defines granular CRUD permissions for a Role.

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
| `customer_start_number` | IntegerField | Default: 1 |
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
| `trouble_call_prefix` | CharField | Default: TC |
| `trouble_call_start_number` | IntegerField | |
| `work_group_prefix` | CharField | Default: WG |
| `work_group_start_number` | IntegerField | |
| `po_prefix` | CharField | Default: PO |
| `po_start_number` | IntegerField | |
| `vehicle_prefix` | CharField | Default: VS |
| `vehicle_start_number` | IntegerField | |
| `custom_email_domain` | CharField | Nullable — e.g. acmehvac.com (Pro/Enterprise add-on) |
| `domain_verification_status` | Enum | Pending, Verified, Failed — Nullable |
| `postmark_domain_id` | CharField | Nullable — Postmark's internal reference |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
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
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `SessionLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | |
| `session_id` | CharField | Unique session token |
| `login_at` | DateTimeField | |
| `logout_at` | DateTimeField | Nullable |
| `expiration_at` | DateTimeField | |
| `ip_address` | GenericIPAddressField | |
| `user_agent` | TextField | Raw User-Agent |
| `permission_snapshot` | JSONB | Permissions at login |
| `browser` | CharField | Parsed |
| `os` | CharField | Parsed |
| `device_type` | Enum | Mobile, Desktop |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
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
| `entity_type` | CharField | e.g. WorkOrder, Invoice |
| `entity_id` | UUIDField | Record identifier |
| `record_number` | CharField | Human-readable (e.g. W26-0042) |
| `details` | JSONField | Contextual change detail |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `PasswordResetToken`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | |
| `token` | CharField | Hashed |
| `expires_at` | DateTimeField | |
| `used_at` | DateTimeField | Nullable |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 1.2 Core CRM — Triad Architecture

### `Customer`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_number` | CharField | Auto-generated (C26-0001) |
| `status` | Enum | Active, Inactive, Hold, Closed |
| `account_type` | Enum | Residential, Commercial |
| `company_name` | CharField | Required for Commercial, optional for Residential |
| `assigned_to` | UUID FK → User | Optional |
| `lead_source` | CharField | Dropdown (customizable) |
| `tax_exempt` | BooleanField | Default: False |
| `customer_since` | DateField | Optional |
| `hold_date` | DateTimeField | Nullable — required when Hold |
| `hold_reason` | TextField | Nullable — required when Hold |
| `closed_at` | DateTimeField | Nullable — required when Closed |
| `account_number` | CharField | Required |
| `account_terms` | CharField | Dropdown (customizable) |
| `credit_limit` | DecimalField | Required |
| `credit_status` | Enum | Good, Fair, Poor |
| `tax_rate` | DecimalField | Optional — overrides tenant default |
| `tags` | ArrayField/JSON | Free-text tags |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Person`
Permanent human identity. Deliberately minimal.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `first_name` | CharField | Required |
| `last_name` | CharField | Required |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Contact`
Bridge table linking a `Person` to a `Customer`, `Vendor`, `Carrier`, or `Bank`.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `person_id` | UUID FK → Person | Required |
| `customer_id` | UUID FK → Customer | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `carrier_id` | UUID FK → Carrier | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `role_title` | CharField | Optional |
| `department` | CharField | Optional |
| `is_primary` | BooleanField | One primary per parent entity |
| `status` | Enum | Active, Left |
| `start_date` | DateField | Optional |
| `left_date` | DateField | Nullable |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Constraint:** Exactly one of `customer_id`, `vendor_id`, `carrier_id`, or `bank_id` must be populated (DB CHECK).

### `Address`
Physical or mailing addresses. Shared across entities.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `carrier_id` | UUID FK → Carrier | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `asset_id` | UUID FK → Asset | Nullable — physical site |
| `user_id` | UUID FK → User | Nullable — employee address |
| `warehouse_id` | UUID FK → Warehouse | Nullable |
| `work_group_id` | UUID FK → WorkGroup | Nullable |
| `address_type` | Enum | Service, Billing, Mailing, Other |
| `is_primary` | BooleanField | |
| `street` | CharField | |
| `city` | CharField | |
| `state` | CharField | |
| `zip` | CharField | |
| `country` | CharField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Constraint:** Exactly one parent FK populated.

### `Phone`
Phone numbers. Shared across entities. Duplicates permitted.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `carrier_id` | UUID FK → Carrier | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `user_id` | UUID FK → User | Nullable |
| `warehouse_id` | UUID FK → Warehouse | Nullable |
| `phone_type` | Enum | Mobile, Office, Home, Fax, Other |
| `number` | CharField | |
| `is_primary` | BooleanField | |
| `extension` | CharField | Optional |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
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
| `user_id` | UUID FK → User | Nullable |
| `type` | Enum | Email, Facebook, LinkedIn, Instagram, Twitter/X, YouTube, Website, Other |
| `value` | CharField | Email address or full URL |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Constraint:** At least one parent FK required.

---

## 1.3 Assets & Product Catalog

### `Asset`
Customer-owned equipment. The primary organizing entity.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `asset_number` | CharField | Auto-generated (A26-0001) |
| `customer_id` | UUID FK → Customer | Required |
| `address_id` | UUID FK → Address | Optional — defaults to primary service address |
| `parent_asset_id` | UUID FK → Asset | Nullable — nested/child assets (Pro/Enterprise) |
| `status` | Enum | Active, Inactive, Decommissioned |
| `asset_category` | CharField | Dropdown (customizable) |
| `asset_type` | CharField | Dropdown (customizable per category) |
| `make` | CharField | Manufacturer |
| `model` | CharField | |
| `serial_number` | CharField | |
| `installation_date` | DateField | Optional |
| `condition` | Enum | Excellent, Good, Fair, Poor |
| `refrigerant_type` | CharField | Optional |
| `capacity_size` | CharField | Optional |
| `warranty_start_date` | DateField | Optional |
| `warranty_end_date` | DateField | Optional |
| `warranty_provider` | CharField | Optional |
| `warranty_notes` | TextField | Optional |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Calculated fields:** `age` (from installation_date), `warranty_status` (Active/Expired/N/A) — display only.

### `Product`
Central catalog. Product in specs = Inventory in ERD.

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
| `preferred_vendor_id` | UUID FK → Vendor | Nullable (Plus+) |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `BundleItem`
Items within a Product Bundle. ERD: Kit Items (FKMasterInventory, FK Inventory).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `bundle_id` | UUID FK → Product | Parent bundle product |
| `product_id` | UUID FK → Product | Included item |
| `quantity` | DecimalField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 1.4 TroubleCall & Service Delivery

### `TroubleCall`
Entry point for customer service requests. ERD: TroubleCall (FK Asset, FK Customer).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `trouble_call_number` | CharField | Auto-generated (TC26-0001) |
| `customer_id` | UUID FK → Customer | Required |
| `asset_id` | UUID FK → Asset | Nullable — linked when asset is identified |
| `address_id` | UUID FK → Address | Nullable — service location |
| `status` | Enum | New, Triaged, Converted to Work Order, Converted to Quote, Cancelled |
| `source` | Enum | Phone, Customer Portal, Web Widget, Email, Referral |
| `issue_category` | CharField | Dropdown |
| `urgency` | Enum | Low, Normal, High, Emergency |
| `description` | TextField | Customer's issue description |
| `triage_notes` | TextField | Internal dispatcher/CSR notes |
| `requested_datetime` | DateTimeField | Customer's preferred window |
| `created_by` | CharField | 'System' if from widget |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `WorkOrder`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_order_number` | CharField | Auto-generated (W26-0001) |
| `customer_id` | UUID FK → Customer | Required |
| `asset_id` | UUID FK → Asset | Required — one asset per WO |
| `trouble_call_id` | UUID FK → TroubleCall | Nullable — originating call |
| `workflow_id` | UUID FK → WorkFlow | Nullable — operational SOP (Pro/Enterprise) |
| `prev_maint_id` | UUID FK → PreventativeMaintenance | Nullable — originating PM |
| `work_group_id` | UUID FK → WorkGroup | Nullable — dispatch group (Plus+) |
| `wg_division_id` | UUID FK → WGDivision | Nullable |
| `vehicle_id` | UUID FK → Vehicle | Nullable — Fleet add-on |
| `converted_to_invoice_id` | UUID FK → Invoice | Nullable — backlink |
| `status` | Enum | Draft, Scheduled, In Progress, On Hold, Completed, Closed, Cancelled |
| `priority` | Enum | Low, Normal, High, Urgent |
| `work_order_type` | CharField | Dropdown (customizable) |
| `assigned_to` | UUID FK → User | Nullable — primary/lead technician |
| `scheduled_date` | DateTimeField | |
| `hold_date` | DateTimeField | Nullable — required when On Hold |
| `hold_reason` | TextField | Nullable — required when On Hold |
| `closed_at` | DateTimeField | Nullable — required when Closed |
| `estimated_duration` | DurationField | |
| `title` | CharField | |
| `description` | TextField | |
| `internal_notes` | TextField | |
| `customer_facing_notes` | TextField | Plus+ only |
| `is_recurring` | BooleanField | |
| `recurrence_pattern` | JSONField | Nullable |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `WorkOrderTeam`
M2M junction for additional technicians on a Work Order.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_order_id` | UUID FK → WorkOrder | |
| `employee_id` | UUID FK → User | |

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
| `is_discount` | BooleanField | Default: False. Forces is_tax_charged = False |
| `is_surcharge` | BooleanField | Default: False |
| `is_tax_charged` | BooleanField | Default: True |
| `sort_order` | IntegerField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
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
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `WorkOrderSubtask`
ERD: Tasks (FK WorkOrder, FK Employee).

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
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `TaskTime`
ERD: TaskTimes (FK Task, FK Employee).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `subtask_id` | UUID FK → WorkOrderSubtask | |
| `employee_id` | UUID FK → User | |
| `clock_in` | DateTimeField | |
| `clock_out` | DateTimeField | Nullable |
| `total_hours` | DecimalField | Calculated |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `TaskToDo`
ERD: TaskToDos (FK Task, FK Employee).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `subtask_id` | UUID FK → WorkOrderSubtask | |
| `employee_id` | UUID FK → User | |
| `label` | CharField | |
| `is_complete` | BooleanField | |
| `sort_order` | IntegerField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

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
| `labor_cost` | DecimalField | Calculated |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 1.5 Quotes & Invoices

### `Quote`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `quote_number` | CharField | Auto-generated (Q26-0001) |
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
| `tax_rate` | DecimalField | Frozen at creation |
| `notes` | TextField | Customer-visible |
| `internal_notes` | TextField | |
| `deposit_required` | BooleanField | Plus+ |
| `deposit_type` | Enum | Fixed, Percentage |
| `deposit_value` | DecimalField | |
| `approval_name` | CharField | Who approved (Plus+) |
| `approval_at` | DateTimeField | |
| `approval_ip` | GenericIPAddressField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
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
| `group_label` | CharField | Optional |
| `item_name` | CharField | |
| `item_type` | Enum | Service, Product - Inventory, Product - Non-Inventory |
| `sku` | CharField | Optional |
| `description` | TextField | |
| `unit_cost` | DecimalField | |
| `unit_price` | DecimalField | |
| `quantity` | DecimalField | |
| `is_discount` | BooleanField | Default: False |
| `is_surcharge` | BooleanField | Default: False |
| `is_tax_charged` | BooleanField | Default: True |
| `visible_to_customer` | BooleanField | |
| `sort_order` | IntegerField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Invoice`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `invoice_number` | CharField | Auto-generated (I26-0001) |
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
| `due_date_offset_days` | IntegerField | |
| `tax_rate` | DecimalField | Frozen at issue |
| `line_item_total` | DecimalField | Calculated |
| `line_item_tax_total` | DecimalField | Calculated |
| `invoice_total` | DecimalField | Calculated |
| `stripe_payment_link_id` | CharField | Nullable |
| `stripe_payment_link_url` | URLField | Nullable |
| `deposit_applied` | DecimalField | From quote deposit |
| `notes` | TextField | Customer-visible |
| `internal_notes` | TextField | |
| `is_recurring` | BooleanField | Plus+ |
| `recurrence_pattern` | JSONField | Nullable |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
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
| `is_discount` | BooleanField | Default: False |
| `is_surcharge` | BooleanField | Default: False |
| `is_tax_charged` | BooleanField | Default: True |
| `visible_to_customer` | BooleanField | |
| `sort_order` | IntegerField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Payment`
Incoming payments from customers. ERD: Payments (FK Invoice, FK Customer, FK Employee, FK VehicleMaint, FK Stripe Response).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `payment_number` | CharField | Auto-generated (P26-0001) |
| `invoice_id` | UUID FK → Invoice | Required |
| `customer_id` | UUID FK → Customer | Denormalized for reporting |
| `employee_id` | UUID FK → User | Who recorded the payment |
| `vehicle_maint_id` | UUID FK → VehicleMaintenance | Nullable — fleet expense |
| `stripe_response_id` | UUID FK → StripeResponse | Nullable |
| `payment_date` | DateField | |
| `amount` | DecimalField | |
| `payment_method` | Enum | Credit/Debit Card, Cash, Check, Bank Transfer, Other |
| `reference_number` | CharField | |
| `stripe_payment_intent_id` | CharField | Nullable |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 1.6 Checklist Templates

### `ChecklistTemplate`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | Required |
| `work_order_type` | CharField | Optional — auto-applies when WO type matches |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `ChecklistTemplateItem`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `template_id` | UUID FK → ChecklistTemplate | |
| `label` | CharField | |
| `sort_order` | IntegerField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 1.7 General Purpose Tasks

### `Task`
Standalone tasks not tied to a Work Order.

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

## 1.8 Attachments — Exclusive Arc Pattern

### `Note`
DB-level CHECK constraint enforces exactly one parent FK per row.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `note_type` | Enum | Internal Note, Call, Email, Site Visit, Customer Comment, Reminder |
| `body` | TextField | |
| `customer_id` | UUID FK | Nullable |
| `contact_id` | UUID FK | Nullable |
| `lead_id` | UUID FK | Nullable |
| `opportunity_id` | UUID FK | Nullable |
| `quote_id` | UUID FK | Nullable |
| `invoice_id` | UUID FK | Nullable |
| `work_order_id` | UUID FK | Nullable |
| `asset_id` | UUID FK | Nullable |
| `trouble_call_id` | UUID FK | Nullable |
| `prev_maint_id` | UUID FK | Nullable |
| `workflow_id` | UUID FK | Nullable |
| `payment_id` | UUID FK | Nullable |
| `vendor_payment_id` | UUID FK | Nullable |
| `user_id` | UUID FK | Nullable (Employee) |
| `vendor_id` | UUID FK | Nullable |
| `purchase_order_id` | UUID FK | Nullable |
| `work_group_id` | UUID FK | Nullable |
| `task_id` | UUID FK | Nullable |
| `vehicle_id` | UUID FK | Nullable |
| `warehouse_id` | UUID FK | Nullable |
| `ledger_id` | UUID FK | Nullable |
| `requisition_id` | UUID FK | Nullable |
| `rma_id` | UUID FK | Nullable |
| `equipment_id` | UUID FK | Nullable |
| `safety_form_id` | UUID FK | Nullable |
| `vendor_bill_id` | UUID FK | Nullable |
| `service_request_id` | UUID FK | Nullable — legacy compat |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Document`
Same exclusive arc pattern as Notes.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `file_name` | CharField | |
| `file_key` | CharField | S3/Spaces key |
| `file_size_bytes` | BigIntegerField | |
| `mime_type` | CharField | |
| *(all parent FKs)* | | Same as Note entity — same exclusive arc |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Implementation Note:** Document has the identical set of nullable parent FKs as Note. For brevity they are not repeated here — refer to the Note model above.

---

## 1.9 System Utilities & Operations

### `SequenceTracker`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `entity_type` | CharField | e.g. Customer, WorkOrder, Invoice |
| `year` | IntegerField | Nullable — for annual reset |
| `last_value` | IntegerField | Current counter — seeded at start_number - 1 |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Notification`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | Nullable — null = all admins |
| `message` | TextField | |
| `severity` | Enum | Info, Warning, Error |
| `is_dismissed` | BooleanField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `StatusChangeLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `entity_name` | CharField | e.g. WorkOrder, Invoice |
| `record_id` | UUIDField | |
| `pre_status` | CharField | |
| `post_status` | CharField | |
| `reason` | TextField | Required for Voids, Reversions |
| `acted_by` | UUID FK → User | Optional |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `SystemErrorLog`

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
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---

## 1.10 Stripe Integration

### `StripeConnection`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Unique |
| `stripe_account_id` | CharField | |
| `access_token` | CharField | Encrypted |
| `is_active` | BooleanField | |
| `connected_at` | DateTimeField | |
| `disconnected_at` | DateTimeField | Nullable |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `StripeResponse`
ERD: StripeResponse (FK Invoice, FK Customer, FK Stripe ID, FK StripeLog).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `invoice_id` | UUID FK → Invoice | |
| `customer_id` | UUID FK → Customer | |
| `stripe_connection_id` | UUID FK → StripeConnection | |
| `stripe_log_id` | UUID FK → StripeLog | Nullable |
| `stripe_payment_intent_id` | CharField | |
| `amount` | DecimalField | |
| `status` | CharField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `StripeLog`
ERD: StripeLog(12month) (FK Customer, FK Stripe ID).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | |
| `stripe_connection_id` | UUID FK → StripeConnection | |
| `event_type` | CharField | |
| `payload` | JSONField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `StripeConnectionLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `event` | Enum | Connected, Disconnected, Token Revoked |
| `occurred_at` | DateTimeField | |
| `details` | JSONField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `StripeAPIRequestLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `endpoint` | CharField | |
| `method` | CharField | |
| `response_status` | IntegerField | |
| `requested_at` | DateTimeField | |
| `duration_ms` | IntegerField | |
| `error_message` | TextField | Nullable |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `WebhookLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `stripe_event_id` | CharField | Unique — idempotency |
| `event_type` | CharField | |
| `processed_at` | DateTimeField | |
| `status` | Enum | Processed, Failed, Skipped |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---

## 1.11 Tenant Infrastructure (SDTA Local)

### `TenantState`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Unique |
| `tier` | Enum | Lite, Plus, Pro, Enterprise |
| `status` | Enum | Active, Suspended, Read-Only |
| `seat_limit` | IntegerField | |
| `storage_limit_bytes` | BigIntegerField | |
| `last_synced_at` | DateTimeField | |
| `created_by` | CharField | 'System' |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | 'System' |
| `updated_on` | DateTimeField | |

### `StorageTracker`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Unique |
| `total_bytes_used` | BigIntegerField | |
| `created_by` | CharField | 'System' |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `DataExportLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | |
| `entity_type` | CharField | |
| `requested_at` | DateTimeField | |
| `status` | Enum | Queued, Complete, Failed |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `TenantSyncLog`

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

### `TenantAddOn`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `addon_type` | Enum | Fleet, SMS_Extra, Storage_+5GB, Storage_+10GB, QB_CSV_Export |
| `status` | Enum | Active, Cancelled, Expired |
| `unit_limit` | Integer | Nullable |
| `purchased_on` | DateTimeField | |
| `created_by` | CharField | 'System' |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | 'System' |
| `updated_on` | DateTimeField | |

### `EmailDeliveryLog`

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
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---

# PART 2 — PLUS TIER MODELS

---

## 2.1 CRM Pipeline (Plus+)

### `Lead`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `lead_number` | CharField | Auto-generated |
| `customer_id` | UUID FK → Customer | Nullable — for unqualified leads |
| `first_name` | CharField | Captured before Customer creation |
| `last_name` | CharField | |
| `phone` | CharField | |
| `email` | EmailField | |
| `source` | Enum | Referral, Website, Advertisement, Trade Show, Cold Call, Other |
| `status` | Enum | New, Contacted, Qualified, Converted, Lost |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Opportunity`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `opportunity_number` | CharField | Auto-generated |
| `customer_id` | UUID FK → Customer | Required |
| `lead_id` | UUID FK → Lead | Nullable |
| `name` | CharField | |
| `status` | Enum | Open, Won, Lost |
| `estimated_value` | DecimalField | |
| `expected_close_date` | DateField | |
| `assigned_to` | UUID FK → User | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `OpportunityAssignedContact`
ERD: Oppt-SASSIGNED-Contact (FK Opportunity, FK Contact, FK Company).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `opportunity_id` | UUID FK → Opportunity | |
| `contact_id` | UUID FK → Contact | |
| `customer_id` | UUID FK → Customer | Denormalized |
| `role_in_opportunity` | CharField | e.g. "Decision Maker" |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---

## 2.2 Service Agreements & PM (Plus+)

### `Agreement`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `agreement_number` | CharField | Auto-generated |
| `name` | CharField | e.g. "Gold Service Plan" |
| `description` | TextField | |
| `status` | Enum | Active, Expired, Cancelled, Pending |
| `start_date` | DateField | |
| `end_date` | DateField | Nullable (Ongoing) |
| `renewal_type` | Enum | Manual, Auto-Renew |
| `pricing_amount` | DecimalField | |
| `pricing_frequency` | Enum | Monthly, Quarterly, Annual |
| `discount_percentage` | DecimalField | Discount on additional work |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `CustomerAgreement`
Three-way junction: Customer + Agreement + Asset.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Required |
| `agreement_id` | UUID FK → Agreement | Required |
| `asset_id` | UUID FK → Asset | Required |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `PreventativeMaintenance`
ERD: Preventative Maintenance (FK WorkFlow, FK Assets, FK Customers, FK Cust Agreements).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `pm_number` | CharField | Auto-generated |
| `asset_id` | UUID FK → Asset | Required |
| `customer_agreement_id` | UUID FK → CustomerAgreement | Required |
| `workflow_id` | UUID FK → WorkFlow | Required (Pro+); nullable in Plus |
| `customer_id` | UUID FK → Customer | Denormalized |
| `status` | Enum | Active, Paused, Expired, Cancelled |
| `frequency` | Enum | Daily, Weekly, Monthly, Quarterly, Semi-Annual, Annual, Custom |
| `visits_per_period` | Integer | |
| `start_date` | DateField | |
| `end_date` | DateField | Nullable |
| `default_assignee_id` | UUID FK → User | |
| `auto_gen_work_orders` | Boolean | |
| `advance_gen_days` | Integer | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 2.3 WorkGroups & Dispatch (Plus+)

### `WorkGroup`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_group_number` | CharField | Auto-generated |
| `customer_id` | UUID FK → Customer | Required |
| `address_id` | UUID FK → Address | Service location |
| `status` | Enum | Open, In Progress, Completed, Cancelled |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `WorkGroupTeam`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_group_id` | UUID FK → WorkGroup | |
| `employee_id` | UUID FK → User | |
| `wgt_role_id` | UUID FK → WGTRole | Role within group |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `WGTRole`
Roles within a WorkGroup (e.g., Lead Technician, Helper).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `WGDivision`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_group_id` | UUID FK → WorkGroup | |
| `address_id` | UUID FK → Address | Division-specific location |
| `name` | CharField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `WorkGroupAsset`
Rolled-up view of all assets in a WorkGroup.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_group_id` | UUID FK → WorkGroup | |
| `asset_id` | UUID FK → Asset | |

---

## 2.4 Purchasing & Vendors (Plus+)

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

> Contacts, Addresses, Phones via shared Triad tables.

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
| `work_group_id` | UUID FK → WorkGroup | Optional (Plus+) |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `PurchaseOrderLine`
ERD: P-LineItems (FK Purchase, FK Inventory, FK POR LineItem).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `purchase_order_id` | UUID FK → PurchaseOrder | |
| `product_id` | UUID FK → Product | |
| `requisition_line_id` | UUID FK → RequisitionLine | Nullable — if from requisition |
| `quantity_ordered` | Decimal | |
| `quantity_received` | Decimal | |
| `unit_cost` | Decimal | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Receiving`
ERD: Receiving (FK PLineItem, FK Inventory, FK Employee).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `po_line_id` | UUID FK → PurchaseOrderLine | Required |
| `product_id` | UUID FK → Product | Required |
| `employee_id` | UUID FK → User | Who received |
| `quantity_received` | Decimal | |
| `received_date` | DateTimeField | |
| `condition` | Enum | Good, Damaged, Partial |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `VendorBill`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vendor_id` | UUID FK → Vendor | Required |
| `bill_number` | CharField | |
| `bill_date` | DateField | |
| `due_date` | DateField | |
| `amount` | DecimalField | |
| `status` | Enum | Draft, Received, Partially Paid, Paid, Overdue, Void |
| `purchase_order_id` | UUID FK → PurchaseOrder | Nullable |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `VendorPayment`
ERD: Payments (FK Purchasing, FK Vendor, FK VendorBills).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vendor_id` | UUID FK → Vendor | Required |
| `purchase_order_id` | UUID FK → PurchaseOrder | Nullable |
| `vendor_bill_id` | UUID FK → VendorBill | Nullable |
| `payment_date` | DateField | |
| `amount` | DecimalField | |
| `payment_method` | Enum | Check, Bank Transfer, Credit Card, Other |
| `reference_number` | CharField | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Requisition`
ERD: Requisition (FK Employee, FK WorkOrder, FK Fleet).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `requisition_number` | CharField | Auto-generated |
| `employee_id` | UUID FK → User | Requestor |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `vehicle_id` | UUID FK → Vehicle | Nullable |
| `status` | Enum | New, Approved, Partially Fulfilled, Fulfilled, Cancelled |
| `fulfillment_method` | Enum | Warehouse Transfer, Purchase Order |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `RequisitionLine`
ERD: RLineItem (FK Requisition, FK PLineItem, FK Inventory).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `requisition_id` | UUID FK → Requisition | |
| `product_id` | UUID FK → Product | |
| `po_line_id` | UUID FK → PurchaseOrderLine | Nullable — when fulfilled via PO |
| `quantity_requested` | Decimal | |
| `quantity_fulfilled` | Decimal | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `RMA`
ERD: RMA (FK PLineItem, FK Inventory, FK Vendor).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `rma_number` | CharField | Auto-generated |
| `po_line_id` | UUID FK → PurchaseOrderLine | |
| `product_id` | UUID FK → Product | |
| `vendor_id` | UUID FK → Vendor | |
| `status` | Enum | Initiated, Shipped, Received by Vendor, Credited, Closed, Denied |
| `reason` | Enum | Defective, Wrong Item, Damaged, Overstock, Other |
| `quantity` | Decimal | |
| `credit_amount` | DecimalField | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 2.5 Warehouse & Inventory (Plus+)

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

> Addresses and Phones via shared Triad tables (FKWarehouse).

### `SubLocation`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `warehouse_id` | UUID FK → Warehouse | |
| `location_number` | CharField | e.g. B1.S1 |
| `location_type` | Enum | Area, Bin, Shelf, Section, Cabinet, Room |
| `description` | TextField | |
| `status` | Enum | Active, Inactive |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `LocationAssignedInventory`
ERD: Loc_Assigned_Inv (FK Location, FK Inventory).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `sub_location_id` | UUID FK → SubLocation | |
| `product_id` | UUID FK → Product | |
| `quantity_on_hand` | Decimal | |
| `serial_number` | CharField | Nullable — serialized tracking (Pro+) |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `InventoryCount`
ERD: Inventory Counts (FK Inventory).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `product_id` | UUID FK → Product | |
| `count_date` | DateTimeField | |
| `counted_by` | UUID FK → User | |
| `physical_count` | Decimal | |
| `system_count` | Decimal | |
| `variance` | Decimal | Calculated |
| `adjustment_applied` | BooleanField | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `InventoryTransfer`
ERD: Inventory Transfers (FK Location, FK Inventory).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `product_id` | UUID FK → Product | |
| `source_location_id` | UUID FK → SubLocation | |
| `dest_location_id` | UUID FK → SubLocation | |
| `quantity` | Decimal | |
| `transfer_date` | DateTimeField | |
| `initiated_by` | UUID FK → User | |
| `status` | Enum | Pending, In Transit, Completed, Cancelled |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 2.6 Financial Entities (Plus+)

### `Bank`
ERD: Banks (FK Customer).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Required |
| `bank_name` | CharField | |
| `account_type` | Enum | Checking, Savings, Line of Credit, Other |
| `routing_number` | CharField | Encrypted |
| `account_number_last4` | CharField | Last 4 only |
| `status` | Enum | Active, Inactive |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> Contacts, Phones, Addresses via shared Triad tables (FKBank).

### `Carrier`
ERD: Referenced by Accounting, Contacts, Phones, Addresses.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `carrier_name` | CharField | |
| `carrier_type` | Enum | Insurance, Surety, Freight, Other |
| `policy_number` | CharField | |
| `status` | Enum | Active, Inactive |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> Contacts, Phones, Addresses via shared Triad tables (FKCarrier).

### `Accounting`
ERD: Accounting (FK Customer, FK Carrier, FK Bank).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Nullable |
| `carrier_id` | UUID FK → Carrier | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `account_type` | CharField | Receivable, Payable, Revenue, Expense, etc. |
| `balance` | DecimalField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Ledger`
ERD: Ledger (FK Payment, FK Customer, FK Vendor, FK Purchasing, FK Invoice).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `payment_id` | UUID FK → Payment | Nullable |
| `vendor_payment_id` | UUID FK → VendorPayment | Nullable |
| `customer_id` | UUID FK → Customer | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `purchase_order_id` | UUID FK → PurchaseOrder | Nullable |
| `invoice_id` | UUID FK → Invoice | Nullable |
| `entry_type` | Enum | Debit, Credit |
| `amount` | Decimal | |
| `running_balance` | Decimal | Calculated at write-time |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `InvPriceHistory`
ERD: InvPriceHistory (Key Inventory).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `product_id` | UUID FK → Product | |
| `old_unit_cost` | DecimalField | |
| `new_unit_cost` | DecimalField | |
| `old_unit_price` | DecimalField | |
| `new_unit_price` | DecimalField | |
| `changed_at` | DateTimeField | |
| `changed_by` | UUID FK → User | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `Position`
ERD: Positions (FK Department).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `department_id` | UUID FK → Department | Required |
| `title` | CharField | Required |
| `description` | TextField | |
| `status` | Enum | Active, Inactive |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Location`
ERD: Locations (FK Department, FK Warehouse).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `department_id` | UUID FK → Department | Nullable |
| `warehouse_id` | UUID FK → Warehouse | Nullable |
| `name` | CharField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

# PART 3 — PRO / ENTERPRISE TIER MODELS

---

## 3.1 WorkFlow Engine (Pro/Enterprise)

### `WorkFlow`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | e.g. "Residential HVAC Install SOP" |
| `description` | TextField | |
| `status` | Enum | Active, Inactive, Draft |
| `work_order_type` | CharField | Nullable — auto-apply trigger |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `WFStep`
ERD: WFSteps (FK WorkFlow).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `workflow_id` | UUID FK → WorkFlow | |
| `step_name` | CharField | |
| `description` | TextField | |
| `sort_order` | Integer | |
| `estimated_duration` | DurationField | Nullable |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `WFStepToDo`
ERD: WFStepToDos (FK WFSteps).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `wf_step_id` | UUID FK → WFStep | |
| `label` | CharField | |
| `sort_order` | Integer | |
| `is_required` | BooleanField | Must complete before step done |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `WFTool`
ERD: WFTools (FK WorkFlow, FK Equipment).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `workflow_id` | UUID FK → WorkFlow | |
| `equipment_id` | UUID FK → Equipment | |

### `WFInventory`
ERD: WF Inventory (FK WorkFlow, FK Inventory).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `workflow_id` | UUID FK → WorkFlow | |
| `product_id` | UUID FK → Product | |
| `quantity_required` | Decimal | |

### `WFSafetyForm`
ERD: WFSafetyForms (FK WorkFlow, FK SafetyForm). Links required SafetyForms to a WorkFlow SOP template.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `workflow_id` | UUID FK → WorkFlow | |
| `safety_form_id` | UUID FK → SafetyForm | |

---

## 3.2 Safety & Compliance (Pro/Enterprise)

### `SafetyForm`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `form_name` | CharField | |
| `description` | TextField | |
| `status` | Enum | Active, Inactive, Draft |
| `form_definition` | JSONField | Field definitions |
| `required_before_work` | BooleanField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `WOSFAnswer`
ERD: WOSFAnswers (FK WorkOrder, FK Employee, FK SafetyForms).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_order_id` | UUID FK → WorkOrder | |
| `employee_id` | UUID FK → User | |
| `safety_form_id` | UUID FK → SafetyForm | |
| `answers` | JSONField | Completed responses |
| `completed_at` | DateTimeField | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---

## 3.3 Skills & Equipment (Pro/Enterprise)

### `Skill`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | e.g. "EPA 608 Certification" |
| `category` | Enum | Certification, License, Training, Competency |
| `status` | Enum | Active, Inactive |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `EmployeeSkill`
ERD: EmployeeSkills (FK Employee, FK Skills).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `employee_id` | UUID FK → User | |
| `skill_id` | UUID FK → Skill | |
| `date_earned` | DateField | |
| `expiration_date` | DateField | Nullable |
| `status` | Enum | Active, Expired |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `Equipment`
Company-owned tools. Distinct from Products (sold to customers) and Assets (customer-owned).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `equipment_number` | CharField | Auto-generated |
| `name` | CharField | |
| `category` | Enum | Power Tool, Hand Tool, Diagnostic, Safety, Other |
| `serial_number` | CharField | |
| `status` | Enum | Available, Checked Out, In Repair, Decommissioned |
| `purchase_date` | DateField | |
| `purchase_cost` | DecimalField | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `CheckInOut`
ERD: Check In/Out (FK Tool, FK Employee).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `equipment_id` | UUID FK → Equipment | |
| `employee_id` | UUID FK → User | |
| `checked_out_at` | DateTimeField | |
| `checked_in_at` | DateTimeField | Nullable — null = still out |
| `condition_out` | Enum | Good, Fair, Needs Repair |
| `condition_in` | Enum | Good, Fair, Damaged |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `CreditCard`
ERD: CreditCards (FK Employee).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `employee_id` | UUID FK → User | |
| `card_type` | Enum | Visa, Mastercard, Amex, Other |
| `last_four` | CharField | |
| `issuing_bank` | CharField | |
| `expiration_date` | DateField | |
| `credit_limit` | DecimalField | |
| `status` | Enum | Active, Suspended, Cancelled |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 3.4 Advanced Pricing (Pro/Enterprise)

### `Pricebook`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | |
| `is_active` | Boolean | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `PricebookEntry`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `pricebook_id` | UUID FK → Pricebook | |
| `product_id` | UUID FK → Product | |
| `price` | Decimal | Overrides standard price |

### `LotInfo`
ERD: Lot Info (FK PLineItem, FK Inventory).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `po_line_id` | UUID FK → PurchaseOrderLine | |
| `product_id` | UUID FK → Product | |
| `lot_number` | CharField | |
| `expiration_date` | DateField | Nullable |
| `quantity` | Decimal | |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---

# PART 4 — FLEET MANAGEMENT ADD-ON (Pro/Enterprise)

### `Vehicle`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vehicle_number` | CharField | VS26-0001 |
| `status` | Enum | Active, Out of Service, Decommissioned |
| `year` | Integer | |
| `make` | CharField | |
| `model` | CharField | |
| `trim` | CharField | Optional |
| `vin` | CharField | |
| `license_plate` | CharField | |
| `license_state` | CharField | |
| `color` | CharField | Optional |
| `vehicle_type` | CharField | Van, Truck, Car, etc. |
| `assigned_user_id` | UUID FK → User | Nullable |
| `odometer_current` | Integer | |
| `purchase_date` | DateField | Optional |
| `purchase_price` | DecimalField | Optional |
| `registration_expiry` | DateField | |
| `insurance_policy` | CharField | |
| `insurance_provider` | CharField | |
| `insurance_expiry` | DateField | |
| `last_inspection_date` | DateField | |
| `next_inspection_date` | DateField | |
| `notes` | TextField | |
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
| `maintenance_number` | CharField | M26-0001 |
| `maintenance_type` | CharField | |
| `status` | Enum | Scheduled, Completed, Overdue, Cancelled |
| `scheduled_date` | DateField | |
| `completed_date` | DateField | |
| `odometer_at_service` | Integer | |
| `next_service_date` | DateField | Nullable |
| `next_service_odometer` | Integer | Nullable |
| `cost` | Decimal | |
| `performed_by` | Enum | In-House, External Shop |
| `vendor_name` | CharField | |
| `description` | TextField | |
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
| `user_id` | UUID FK → User | Driver |
| `log_date` | DateField | |
| `odometer_start` | Integer | |
| `odometer_end` | Integer | |
| `miles_driven` | Integer | Calculated |
| `purpose` | CharField | |
| `work_order_id` | UUID FK → WorkOrder | Optional |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `VehicleInventory`
ERD: Vehichle Inventory (FK Fleet, FK Tools/Inventory).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vehicle_id` | UUID FK → Vehicle | |
| `product_id` | UUID FK → Product | Nullable — saleable inventory |
| `equipment_id` | UUID FK → Equipment | Nullable — company tools |
| `quantity` | Decimal | Nullable — for products |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

> **Constraint:** Exactly one of `product_id` or `equipment_id` must be populated.

---

# PART 5 — DELETE RULES

## 5.1 Policy Overview
If a top-level entity has any child records, it cannot be deleted. The user must delete all children before the parent.

> **Top-level entities:** Customer, Asset, Work Order, Quote, Invoice, Product, Vendor, WorkGroup, Vehicle, Task, Agreement, Lead, Opportunity, Equipment, SafetyForm, WorkFlow

## 5.2 Preferred Alternatives to Delete

For key entities where historical integrity matters, soft-delete (status change) is strongly preferred over hard delete.

| Entity | Preferred Alternative to Delete |
|---|---|
| Customer | Set Status = Inactive |
| Asset | Set Status = Decommissioned |
| Work Order | Set Status = Cancelled |
| Quote | Set Status = Expired or Rejected |
| Invoice | Set Status = Void |
| Employee | Set Status = Terminated |
| Vehicle | Set Status = Decommissioned |
| Agreement | Set Status = Cancelled |
| WorkGroup | Set Status = Cancelled |
| Equipment | Set Status = Decommissioned |
| WorkFlow | Set Status = Inactive |

---

*End of ServizmaDesk Data Models V4*
