# ServizmaDesk SDTA — Data Models V2
**Document Status:** Working Draft — V2
**Date:** March 2026
**Classification:** Internal — Confidential
**Source:** Derived from `ServizmaDesk_Top_Down_Specifications.md` V1

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
6. **Shared Triad Tables** — `Person`, `Contact`, `Address`, `Phone`, `Social` are shared between Customers and Vendors.

---

# PART 1 — LITE TIER MODELS

The complete foundational model set for the Lite MVP.

---

## 1.1 Identity, Access & Preferences

### `User`
Represents a tenant employee with access to the SDTA.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Required, indexed |
| `email` | EmailField | Unique per tenant |
| `password` | CharField | Hashed (bcrypt) |
| `first_name` | CharField | |
| `last_name` | CharField | |
| `employee_number` | CharField | Auto-generated (E26-0001) |
| `role` | FK → Role | Required |
| `status` | Enum | Active, Inactive |
| `phone` | CharField | Optional |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

### `Role`
Defines permission level for a User.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | Administrator, User, Read-Only (Lite); custom in Pro/Enterprise |
| `is_custom` | BooleanField | False for system roles |

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
| `smtp_host` | CharField | Optional — tenant SMTP |
| `smtp_port` | IntegerField | |
| `smtp_username` | CharField | |
| `smtp_password` | CharField | Encrypted |
| `smtp_use_tls` | BooleanField | |
| `smtp_use_ssl` | BooleanField | |
| `smtp_from_name` | CharField | |
| `smtp_from_email` | EmailField | |

### `UserPreference`
Per-user settings.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | Unique |
| `ui_theme` | Enum | Light, Dark, System |
| `default_landing_page` | CharField | |

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
| `browser` | CharField | Parsed |
| `os` | CharField | Parsed |
| `device_type` | Enum | Mobile, Desktop |

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

### `PasswordResetToken`
Time-limited single-use token for password resets.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `user_id` | UUID FK → User | |
| `token` | CharField | Hashed |
| `created_at` | DateTimeField | |
| `expires_at` | DateTimeField | |
| `used_at` | DateTimeField | Nullable — set on first use |

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
| `tags` | ArrayField/JSON | Free-text tags |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

### `Person`
Permanent human identity. Deliberately minimal — only identity fields.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `first_name` | CharField | Required |
| `last_name` | CharField | Required |
| `created_at` | DateTimeField | |

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
| `created_at` | DateTimeField | |

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
| `address_type` | Enum | Service, Billing, Mailing, Other |
| `is_primary` | BooleanField | |
| `street` | CharField | |
| `city` | CharField | |
| `state` | CharField | |
| `zip` | CharField | |
| `country` | CharField | |

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
| `user_id` | UUID FK → User | Nullable |
| `phone_type` | Enum | Mobile, Office, Home, Fax, Other |
| `number` | CharField | |
| `is_primary` | BooleanField | |
| `extension` | CharField | Optional |

> **Constraint:** Exactly one parent FK populated.

### `Social`
Emails, social media links, web profiles. Shared across entities.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `contact_id` | UUID FK → Contact | Nullable |
| `person_id` | UUID FK → Person | Nullable |
| `type` | Enum | Email, Facebook, LinkedIn, Instagram, Twitter/X, YouTube, Website, Other |
| `value` | CharField | Email address or full URL |

> **Constraint:** At least one of `contact_id` or `person_id` required.

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
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

> **Calculated field:** `age` (from `installation_date` — display only), `warranty_status` (Active / Expired / N/A — display only).

### `Product`
Central catalog of all products and services.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `product_number` | CharField | Auto-generated (e.g. XT-0001) |
| `name` | CharField | Required |
| `type` | Enum | Service, Product - Inventory, Product - Non-Inventory |
| `category` | CharField | Dropdown (customizable) |
| `sku` | CharField | Optional |
| `unit_cost` | DecimalField | Internal cost |
| `unit_price` | DecimalField | Customer price |
| `description` | TextField | |
| `taxable` | BooleanField | Default: True |
| `is_bundle` | BooleanField | |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

### `BundleItem`
Items within a Product Bundle.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `bundle_id` | UUID FK → Product | The parent bundle product |
| `product_id` | UUID FK → Product | The included item |
| `quantity` | DecimalField | |

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
| `vehicle_id` | UUID FK → Vehicle | Nullable — Fleet add-on only |
| `status` | Enum | Draft, Scheduled, In Progress, Completed, Cancelled |
| `priority` | Enum | Low, Normal, High, Urgent |
| `work_order_type` | CharField | Dropdown (customizable): Service Call, Repair, Installation, Maintenance, Inspection, Diagnostic |
| `assigned_to` | UUID FK → User | Nullable |
| `scheduled_date` | DateTimeField | |
| `estimated_duration` | DurationField | |
| `title` | CharField | |
| `description` | TextField | |
| `internal_notes` | TextField | |
| `customer_facing_notes` | TextField | Plus+ only |
| `is_recurring` | BooleanField | |
| `recurrence_pattern` | JSONField | Nullable — stores recurrence config |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

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
| `taxable` | BooleanField | |
| `sort_order` | IntegerField | |

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

### `Quote`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `quote_number` | CharField | Auto-generated (e.g. Q26-0001) |
| `customer_id` | UUID FK → Customer | Required |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `project_id` | UUID FK → Project | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Draft, Sent, Viewed, Approved, Rejected, Expired |
| `quote_date` | DateField | Defaults to today |
| `expiration_date` | DateField | |
| `discount_type` | Enum | Percentage, Fixed |
| `discount_value` | DecimalField | |
| `surcharge_label` | CharField | |
| `surcharge_value` | DecimalField | |
| `tax_rate` | DecimalField | Override; defaults from TenantPreference |
| `notes` | TextField | Customer-visible |
| `internal_notes` | TextField | Not visible to customer |
| `deposit_required` | BooleanField | Plus+ |
| `deposit_type` | Enum | Fixed, Percentage |
| `deposit_value` | DecimalField | |
| `approval_name` | CharField | Who approved (Plus+) |
| `approval_at` | DateTimeField | When approved |
| `approval_ip` | GenericIPAddressField | |
| `converted_to_invoice_id` | UUID FK → Invoice | Nullable |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

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
| `taxable` | BooleanField | |
| `visible_to_customer` | BooleanField | |
| `sort_order` | IntegerField | |

### `Invoice`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `invoice_number` | CharField | Auto-generated (e.g. I26-0001) |
| `customer_id` | UUID FK → Customer | Required |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `project_id` | UUID FK → Project | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Draft, Issued, Viewed, Partially Paid, Paid, Overdue, Void, Written Off |
| `invoice_date` | DateField | Defaults to today |
| `due_date` | DateField | |
| `due_date_method` | Enum | Creation Date + N, Sent Date + N, WO Completion + N, Manual |
| `due_date_offset_days` | IntegerField | |
| `discount_type` | Enum | Percentage, Fixed |
| `discount_value` | DecimalField | |
| `surcharge_label` | CharField | |
| `surcharge_value` | DecimalField | |
| `tax_rate` | DecimalField | |
| `deposit_applied` | DecimalField | From quote deposit |
| `notes` | TextField | Customer-visible |
| `internal_notes` | TextField | |
| `is_recurring` | BooleanField | Plus+ |
| `recurrence_pattern` | JSONField | Nullable |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

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
| `taxable` | BooleanField | |
| `visible_to_customer` | BooleanField | |
| `sort_order` | IntegerField | |

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
| `created_at` | DateTimeField | |

### `LedgerEntry`
Read-only running AR balance per customer.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | |
| `entry_type` | Enum | Debit (Invoice), Credit (Payment) |
| `reference_id` | UUIDField | Invoice or Payment ID |
| `reference_type` | CharField | Invoice or Payment |
| `amount` | DecimalField | |
| `entry_date` | DateField | |
| `running_balance` | DecimalField | Calculated |

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
| `created_at` | DateTimeField | |

### `ChecklistTemplateItem`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `template_id` | UUID FK → ChecklistTemplate | |
| `label` | CharField | |
| `sort_order` | IntegerField | |

---

## 1.6 Organization

### `Task`
Standalone internal tasks (not Work Order subtasks).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `task_number` | CharField | Auto-generated (e.g. T26-0001) |
| `title` | CharField | Required |
| `description` | TextField | |
| `assigned_to` | UUID FK → User | |
| `status` | Enum | Open, In Progress, Completed |
| `due_date` | DateField | |
| `priority` | Enum | Low, Normal, High, Urgent |
| `customer_id` | UUID FK → Customer | Optional |
| `asset_id` | UUID FK → Asset | Optional |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

---

## 1.7 Attachments — Exclusive Arc Pattern

Both tables service the entire platform using nullable FKs with a DB `CHECK` constraint enforcing exactly one parent.

### `Note`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `body` | TextField | |
| `created_by` | UUID FK → User | |
| `created_at` | DateTimeField | |
| `customer_id` | UUID FK → Customer | Nullable |
| `person_id` | UUID FK → Person | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `asset_id` | UUID FK → Asset | Nullable |
| `product_id` | UUID FK → Product | Nullable |
| `quote_id` | UUID FK → Quote | Nullable |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `invoice_id` | UUID FK → Invoice | Nullable |
| `payment_id` | UUID FK → Payment | Nullable |
| `task_id` | UUID FK → Task | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `purchase_order_id` | UUID FK → PurchaseOrder | Nullable |
| `vehicle_id` | UUID FK → Vehicle | Nullable |

### `Document`
File attachments stored in object storage.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `file_name` | CharField | Original filename |
| `file_key` | CharField | Object storage key |
| `file_size_bytes` | BigIntegerField | |
| `mime_type` | CharField | |
| `created_by` | UUID FK → User | |
| `created_at` | DateTimeField | |
| `customer_id` | UUID FK → Customer | Nullable |
| `person_id` | UUID FK → Person | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `asset_id` | UUID FK → Asset | Nullable |
| `product_id` | UUID FK → Product | Nullable |
| `quote_id` | UUID FK → Quote | Nullable |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `invoice_id` | UUID FK → Invoice | Nullable |
| `payment_id` | UUID FK → Payment | Nullable |
| `task_id` | UUID FK → Task | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `purchase_order_id` | UUID FK → PurchaseOrder | Nullable |
| `vehicle_id` | UUID FK → Vehicle | Nullable |

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
| `last_value` | IntegerField | Current counter value |

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
| `created_at` | DateTimeField | |

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

### `StripeConnectionLog`
Audit trail for Stripe connect/disconnect events.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `event` | Enum | Connected, Disconnected, Token Revoked |
| `occurred_at` | DateTimeField | |
| `details` | JSONField | |

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

### `StorageTracker`
Running tally of tenant Document upload storage consumption.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Unique |
| `total_bytes_used` | BigIntegerField | |
| `last_updated_at` | DateTimeField | |

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

### `TenantSyncLog`
Tracks SDTA ↔ SDP synchronization attempts.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `sync_type` | CharField | SubscriptionUpdate, SeatLimitChange, etc. |
| `occurred_at` | DateTimeField | |
| `status` | Enum | Success, Failed |
| `details` | JSONField | |

### `OnboardingState`
Tracks first-login wizard and onboarding checklist completion.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Unique |
| `wizard_completed` | BooleanField | |
| `checklist_items` | JSONField | Key-value flags per onboarding step |

---

# PART 2 — PLUS / PRO / ENTERPRISE TIER MODELS

Directional specifications. Detailed field specs to be finalized in tier-specific documents.

---

## 2.1 Project Entity (Plus+)

### `Project`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `project_number` | CharField | Auto-generated (e.g. PJ26-0001) |
| `name` | CharField | Required |
| `customer_id` | UUID FK → Customer | Required |
| `project_manager_id` | UUID FK → User | |
| `status` | Enum | Planning, In Progress, On Hold, Completed, Cancelled |
| `start_date` | DateField | |
| `target_completion_date` | DateField | |
| `budget` | DecimalField | |
| `completion_percentage` | DecimalField | Manual or auto-calculated |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

---

## 2.2 Vendor Entity (Plus+)

### `Vendor`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vendor_name` | CharField | Required |
| `account_number` | CharField | Optional |
| `notes` | TextField | |
| `created_at` | DateTimeField | |

> **Architecture:** Contacts, Addresses, Phones, and Socials link to Vendor using the same shared Triad tables as Customers.

---

## 2.3 Purchase Order Entity (Plus+)

### `PurchaseOrder`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `po_number` | CharField | Auto-generated |
| `vendor_id` | UUID FK → Vendor | Required |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `project_id` | UUID FK → Project | Nullable |
| `order_date` | DateField | |
| `expected_delivery_date` | DateField | |
| `status` | Enum | Draft, Sent, Partially Received, Received, Cancelled |
| `created_at` | DateTimeField | |

### `PurchaseOrderLine`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `purchase_order_id` | UUID FK → PurchaseOrder | |
| `product_id` | UUID FK → Product | Nullable |
| `item_name` | CharField | |
| `quantity_ordered` | DecimalField | |
| `quantity_received` | DecimalField | Updates on receipt |
| `unit_cost` | DecimalField | |

---

## 2.4 Part Requisition Entity (Plus+)

### `PartRequisition`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `requisition_number` | CharField | Auto-generated (e.g. RQ26-0001) |
| `requested_by` | UUID FK → User | Technician |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `required_by_date` | DateField | |
| `status` | Enum | Draft, Submitted, Partially Fulfilled, Fulfilled, Cancelled |
| `fulfillment_method` | Enum | Warehouse Transfer, Direct Purchase Order |

### `PartRequisitionLine`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `requisition_id` | UUID FK → PartRequisition | |
| `product_id` | UUID FK → Product | Nullable |
| `item_name` | CharField | |
| `quantity_requested` | DecimalField | |
| `quantity_fulfilled` | DecimalField | |
| `notes` | TextField | |

---

## 2.5 Warehouse & Inventory Entity (Plus+)

### `Warehouse`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `warehouse_number` | CharField | Auto-generated (e.g. WH26-0001) |
| `name` | CharField | Required |
| `type` | Enum | Physical Hub, Mobile (Van/Truck) |
| `status` | Enum | Active, Inactive |
| `assigned_employee_id` | UUID FK → User | Optional — for Mobile type |
| `address` | CharField | For Physical Hubs |
| `notes` | TextField | |

### `SubLocation`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `location_number` | CharField | User-assigned (e.g. A1.B3.C2) |
| `warehouse_id` | UUID FK → Warehouse | Required |
| `type` | Enum | Area, Bin, Shelf, Section, Cabinet, Room |
| `description` | TextField | |
| `status` | Enum | Active, Inactive |

### `InventoryLevel`
Product quantities tracked per Sub-Location.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `product_id` | UUID FK → Product | |
| `warehouse_id` | UUID FK → Warehouse | |
| `sub_location_id` | UUID FK → SubLocation | Nullable |
| `quantity_on_hand` | DecimalField | |
| `quantity_minimum` | DecimalField | Low stock alert threshold |
| `quantity_allocated` | DecimalField | On Work Orders |
| `quantity_on_order` | DecimalField | On Purchase Orders |
| `quantity_reserved` | DecimalField | |

---

## 2.6 Maintenance Plan Entity (Plus+)

### `MaintenancePlan`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | |
| `customer_id` | UUID FK → Customer | Required |
| `status` | Enum | Active, Paused, Expired, Cancelled |
| `start_date` | DateField | |
| `end_date` | DateField | Nullable — ongoing plans |
| `renewal` | Enum | Manual, Auto-Renew |
| `frequency` | Enum | Daily, Weekly, Monthly, Quarterly, Semi-Annual, Annual, Custom |
| `visits_per_period` | IntegerField | |
| `assigned_to` | UUID FK → User | Default technician |
| `auto_generate_work_orders` | BooleanField | |
| `advance_generation_days` | IntegerField | |
| `created_at` | DateTimeField | |

### `MaintenancePlanAsset` (M2M junction)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `plan_id` | UUID FK → MaintenancePlan | |
| `asset_id` | UUID FK → Asset | |

---

## 2.7 Service Request Entity (Plus+ — Customer Portal)

### `ServiceRequest`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `request_number` | CharField | Auto-generated (e.g. SR26-0001) |
| `customer_id` | UUID FK → Customer | Nullable — may be unknown lead |
| `address_id` | UUID FK → Address | Nullable |
| `status` | Enum | New, Triaged, Converted to Work Order, Converted to Quote, Cancelled |
| `source` | Enum | Phone, Customer Portal, Web Widget, Email, Referral |
| `issue_category` | CharField | |
| `urgency` | Enum | Low, Normal, High, Emergency |
| `customer_description` | TextField | Exact customer wording |
| `triage_notes` | TextField | Internal |
| `requested_datetime` | DateTimeField | Customer's preferred window |
| `converted_to_work_order_id` | UUID FK → WorkOrder | Nullable |
| `created_at` | DateTimeField | |

---

## 2.8 Pro/Enterprise Models (Directional)

The following models are required for Pro and Enterprise tiers. Full field-level specifications will be defined in per-tier specification documents.

| Model | Tier | Purpose |
|---|---|---|
| `ChartOfAccount` | Pro+ | Chart of accounts (Assets, Liabilities, Equity, Revenue, Expenses) |
| `GeneralLedgerEntry` | Pro+ | True double-entry GL journal entries |
| `JournalEntry` | Enterprise | Manual double-entry adjustments |
| `TaxJurisdiction` | Enterprise | Multi-jurisdiction tax liability tracking |
| `BankFeedConnection` | Enterprise | Plaid/Finicity integration for bank reconciliation |
| `FixedAsset` | Enterprise | Business asset depreciation tracking |
| `TaxonomyTerm` | Plus+ | User-configurable dropdown values (dynamic enumerations) |
| `PriceTier` | Pro+ | Customer-specific pricing tiers |
| `PriceTierLine` | Pro+ | Per-product pricing per tier |
| `SerializedInventoryItem` | Pro+ | Individual serialized unit tracking |
| `CommissionRule` | Pro+ | Commission calculation configuration |
| `CommissionRecord` | Pro+ | Per-invoice commission calculations |
| `AutomationRule` | Plus+ | IF [event] THEN [action] automation engine |
| `AutomationLog` | Plus+ | Execution history of automation rules |
| `CustomField` | All | Field definitions per entity type |
| `CustomFieldValue` | All | Values for custom fields per record |
| `ChecklistTemplate` | Lite+ | Moved to Lite — see Section 1.5 |
| `BusinessLocation` | Enterprise | Multi-location tenant configuration |

---

# PART 3 — FLEET MANAGEMENT ADD-ON (Pro/Enterprise)

Fleet Management is a paid add-on module. Tables exist in the database from initial deployment; UI and controllers are gated behind the add-on subscription status.

---

## 3.1 Vehicle Entity

### `Vehicle`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vehicle_number` | CharField | Auto-generated (e.g. V26-0001) |
| `status` | Enum | Active, Out of Service, Decommissioned |
| `year` | IntegerField | 4-digit |
| `make` | CharField | |
| `model` | CharField | |
| `trim_description` | CharField | Optional |
| `vin` | CharField | Unique per tenant |
| `license_plate` | CharField | |
| `license_plate_state` | CharField | |
| `color` | CharField | Optional |
| `vehicle_type` | CharField | Dropdown (customizable): Van, Truck, Car, Box Truck, Trailer, Other |
| `assigned_driver_id` | UUID FK → User | Nullable |
| `odometer_current` | IntegerField | Updated via mileage log |
| `purchase_date` | DateField | Optional |
| `purchase_price` | DecimalField | Optional |
| `notes` | TextField | |
| `registration_expiry` | DateField | |
| `insurance_policy_number` | CharField | |
| `insurance_provider` | CharField | |
| `insurance_expiry` | DateField | |
| `last_inspection_date` | DateField | |
| `next_inspection_due` | DateField | |
| `created_at` | DateTimeField | |
| `updated_at` | DateTimeField | |

---

## 3.2 VehicleMaintenance Entity

### `VehicleMaintenance`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `maintenance_number` | CharField | Auto-generated (e.g. M26-0001) |
| `vehicle_id` | UUID FK → Vehicle | Required |
| `maintenance_type` | CharField | Dropdown (customizable): Oil Change, Tire Rotation, Brake Service, etc. |
| `status` | Enum | Scheduled, Completed, Overdue, Cancelled |
| `scheduled_date` | DateField | |
| `completed_date` | DateField | Nullable |
| `odometer_at_service` | IntegerField | |
| `next_service_due_date` | DateField | Optional |
| `next_service_due_odometer` | IntegerField | Optional |
| `performed_by` | Enum | In-House, External Shop |
| `shop_vendor_name` | CharField | If External Shop |
| `cost` | DecimalField | |
| `description_notes` | TextField | |

---

## 3.3 MileageLog Entity

### `MileageLog`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vehicle_id` | UUID FK → Vehicle | Required |
| `user_id` | UUID FK → User | Driver |
| `date` | DateField | Required |
| `odometer_start` | IntegerField | |
| `odometer_end` | IntegerField | |
| `trip_purpose` | CharField | Dropdown (customizable): Customer Job, Supply Run, Shop Drop-Off, Other |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `notes` | TextField | Optional |

> **Calculated:** `miles_driven` = `odometer_end` − `odometer_start`.
> **Validation:** `odometer_end` ≥ `odometer_start`; new entry `odometer_start` ≥ last recorded odometer for vehicle (warning, not blocking).

---

# PART 4 — SERVICE REQUEST ENTITY (Lite — Minimal)

The Lite version includes a simplified web booking widget. A `ServiceRequest` record is created with limited fields; the full Customer Portal and intake workflow is a Plus+ feature (Section 2.7 above).

---

# PART 5 — DELETE RULES (Task 1C)

## 5.1 Policy Overview

### Core Rule
If a **top-level entity** has any **child records**, it **cannot be deleted**. The user must delete all children before the parent. The system will display a blocking message listing what child records exist.

> **Top-level entities subject to this rule:** Customer, Asset, Work Order, Quote, Invoice, Product, Vendor, Project, Vehicle, Task

### Exception — Notes & Documents (Cascade Delete)
If the **only** related records on a parent entity are **Notes and/or Documents**, the system will cascade-delete those Notes and Documents automatically when the parent is deleted.

> "Only Notes and Documents" means: all other child record types (Work Orders, Invoices, Payments, Assets, etc.) must be zero. If any non-Note/non-Document child exists, the standard block rule applies.

---

## 5.2 Delete Confirmation Requirement

**All deletes — regardless of entity type — require an explicit user confirmation dialog.**

The confirmation must display the following message verbatim:

> **"This will permanently delete this record. Are you sure?"**

The dialog must provide two buttons:
- **Cancel** — Closes dialog, no action taken
- **Delete** — Confirms and executes the deletion

This confirmation is non-optional and cannot be disabled by any user role.

---

## 5.3 Delete Rules Per Entity

| Entity | Block Condition | Cascade on Delete |
|---|---|---|
| **Customer** | Has any Assets, Work Orders, Quotes, Invoices, Payments, or Projects | Notes and Documents (if only children) |
| **Asset** | Has any Work Orders or Maintenance Plan links | Notes and Documents |
| **Work Order** | Has any Invoices, Payments, or Quote conversions | Notes, Documents, Lines, Checklist Items, Subtasks, Time Entries |
| **Quote** | Has been converted to an Invoice | Notes, Documents, Lines |
| **Invoice** | Has any Payments applied | Notes, Documents, Lines |
| **Product** | Is referenced on any Quote, Work Order, or Invoice Line | Notes, Documents |
| **Vendor** | Has any Purchase Orders | Notes, Documents |
| **Project** | Has any linked Work Orders | Notes, Documents |
| **Task** | No blocking children | Notes, Documents |
| **Vehicle** | Has Maintenance Records or Mileage Log entries | Notes, Documents |
| **Contact** | — | Soft-delete preferred (set Status = Left); Person record is never deleted |
| **Person** | Has any active Contact records | — |
| **Note** | — (leaf node) | None |
| **Document** | — (leaf node) | None |
| **Payment** | — (leaf node) | None |

---

## 5.4 Soft-Delete Guidance

For key entities where historical integrity matters, soft-delete (setting `status = Inactive` or `status = Cancelled`) is strongly preferred over hard delete. The system should surface this option to the user before offering delete in appropriate contexts.

| Entity | Preferred Alternative to Delete |
|---|---|
| Customer | Set Status = Inactive |
| Asset | Set Status = Decommissioned |
| Work Order | Set Status = Cancelled |
| Quote | Set Status = Expired or Rejected |
| Invoice | Set Status = Void |
| Employee/User | Set Status = Inactive |

---

*End of ServizmaDesk Data Models V2*
