# ServizDesk SDTA — Data Models V6
**Document Status:** Working Draft — V6
**Date:** March 2026
**Classification:** Internal — Confidential
**Source:** Originally derived from `SD System ERD - Base System V12.pdf`, `SD System ERD - Employee V4.pdf`, `SD System ERD - System Logs V1.pdf`
**Supersedes:** ServizDesk SDTA Data Models V5

> **Schema Authority:** This document (Data Models V6) is the **sole authoritative specification** for database schema going forward. The source ERD PDFs served as the original design input and remain useful as visual references, but where this document and an ERD disagree, **this document wins**. Intentional divergences from the ERDs (e.g., SubAsset junction replacing self-FK, unified Payment model, tenant-scoped StripeConnection) are documented in Part 6 — ERD Reconciliation Notes. ERD PDFs are not maintained in lockstep with V6 iterations; a future ERD refresh may be generated from V6 as needed.

---

## Document Purpose

This document defines the detailed data model for the ServizDesk Tenant App (SDTA). It serves as the authoritative field-level specification for all database models, organized by tier.

> **ERD Naming Note:** The ERD uses "Inventory" as the entity name throughout. The Django model name for this entity is `InventoryItem` — this is consistent with the entity name used across all other specifications (CSV Export Specification, Top-Down Specifications, Seed Data Specification, Sequence Tracker entity types). In the Lite tier UI only, this entity is labeled "Product"; all other tiers use "Inventory Item" in the UI.

### ERD-to-V6 Entity Name Mapping

The following table maps ERD entity names (from the three source PDFs) to their corresponding Django model names in this document. Developers consulting the ERD diagrams should use this table to find the correct model specification.

| ERD Name | V6 Model Name | Notes |
|---|---|---|
| `Inventory` | `InventoryItem` (aka `Product` in Lite UI) | Documented above |
| `Purchasing` | `PurchaseOrder` | Same entity, renamed for clarity |
| `P-LineItems` | `PurchaseOrderLine` | |
| `Q-LineItems` | `QuoteLine` | |
| `WO Line Items` | `WorkOrderLine` | |
| `Invoice Line Items` | `InvoiceLine` | |
| `R LineItem` | `RequisitionLine` | |
| `Permissions` (Employee ERD) | `RolePermission` | ERD FK Roles → V6 `role_id` FK |
| `User Sessions` (Employee ERD) | `SessionLog` | |
| `Session Transactions` (Employee ERD) | `ProcessTransaction` | |
| `Navigation Audits` (System Logs ERD) | `NavigationAudit` | Minor pluralization change |
| `System Audits` (System Logs ERD) | `SystemAudit` | |
| `Issues_Errors` (System Logs ERD) | `IssuesErrors` | Aligned |
| `Payments` (ERD shows two boxes) | `Payment` (single table) | ERD splits customer/vendor payments; V6 unifies with `payment_type` discriminator |
| `Sub Assets (Assets)` | `SubAsset` | Junction table replacing former `parent_asset_id` self-FK |
| `WorkGroup (Project)` | `WorkGroup` | |
| `WG Division (Epic)` | `WGDivision` | |

---

## Architectural Mandates

1. **`tenant_id` on every table** — UUIDv4 foreign key for horizontal data isolation.
2. **UUIDv4 primary keys** — All primary and foreign keys use UUIDv4. No auto-incrementing integers.
3. **No Generic Foreign Keys (GFKs)** — Strict PostgreSQL RLS enforcement; no Django content-types framework.
4. **Isolated line item tables** — `QuoteLine`, `WorkOrderLine`, `InvoiceLine`, `PurchaseOrderLine`, `RequisitionLine` are separate tables; no shared generic line item table.
5. **Exclusive Arc for Notes/Documents** — Single `Note` and `Document` table with nullable FKs to every possible parent entity. A DB-level `CHECK` constraint enforces exactly one FK is populated per row.
6. **Shared Triad Tables** — `Person`, `Contact`, `Address`, `Phone`, `Social` are shared between Customers, Vendors, Banks, and Users (Employees).
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
| `position_id` | UUID FK → Position | Nullable — primary position (Plus+) |
| `prev_employee_id` | UUID FK → User | Nullable — links returning employee to prior User record |
| `email` | EmailField | Unique per tenant; login credential |
| `password` | CharField | Hashed (bcrypt/Argon2) |
| `employee_number` | CharField | Auto-generated (E26-0001) |
| `status` | Enum | Active, On Leave, Inactive, Terminated |
| `hire_date` | DateField | Optional |
| `termination_date` | DateField | Nullable — required to release a seat |
| `failed_login_count` | IntegerField | Default: 0. Account locks at 5. |
| `force_password_change` | BooleanField | Default: False |
| `mfa_enabled` | BooleanField | Default: False. Reflects whether the employee has MFA configured (phone number registered and MFA active for this account). |
| `mfa_phone` | CharField | Nullable. Dedicated phone number for MFA SMS delivery. Separate from Person contact phones. |
| `mfa_exempt` | BooleanField | Default: False. When True, this employee is temporarily exempt from the organization-wide MFA requirement. Used by Administrators for MFA recovery (e.g., employee lost phone). Must be set back to False once MFA is reconfigured. Every change is audit-logged. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Implementation Note:** `failed_login_count` is a display mirror of the django-axes failure count, used in the Employee management UI. Must be updated via a `post_save` signal or middleware hook when django-axes records a login failure. Reset to 0 on successful login or administrator unlock.

> **Lockout:** Account locked when `failed_login_count >= 5`. Unlock resets to 0.
> **MFA logic:** MFA is required at login when `TenantPreference.mfa_required = True` AND `User.mfa_exempt = False`. The `mfa_enabled` field tracks whether the user has a configured MFA method — it is set to True when the user registers their MFA phone. `mfa_exempt` is the administrator override for temporary recovery and must never be used as a permanent MFA bypass.

> **Seat counting:** Active + On Leave + Inactive count toward seat limit. Terminated does not. Requires `status = Terminated` AND `termination_date` populated to release a seat.

> **Rehire:** When a former employee is rehired, a new `User` record is created. `prev_employee_id` links the new record back to the prior record, preserving employment history continuity.

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

### `EmployeePosition`
Junction table mapping employees to positions. ERD: Employee Positions (FK Employee, FK Position). An employee may hold multiple positions. `position_id` on `User` designates the primary position.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `employee_id` | UUID FK → User | |
| `position_id` | UUID FK → Position | |
| `is_primary` | BooleanField | Mirrors User.position_id — one primary per employee |
| `start_date` | DateField | Nullable |
| `end_date` | DateField | Nullable |
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
| `product_prefix` | CharField | Default: computed via reverse-alphabet year encoding (e.g., `YU` for 2026). See Numbering Service V1 §6.1. |
| `product_start_number` | IntegerField | |
| `employee_prefix` | CharField | Default: E |
| `employee_start_number` | IntegerField | Default: 1 |
| `service_request_prefix` | CharField | Default: SR |
| `service_request_start_number` | IntegerField | |
| `work_group_prefix` | CharField | Default: WG |
| `work_group_start_number` | IntegerField | |
| `po_prefix` | CharField | Default: PO |
| `po_start_number` | IntegerField | |
| `vehicle_prefix` | CharField | Default: VS |
| `vehicle_start_number` | IntegerField | |
| `custom_email_domain` | CharField | Nullable — e.g. acmehvac.com (Pro/Enterprise add-on) |
| `domain_verification_status` | Enum | Pending, Verified, Failed — Nullable |
| `postmark_domain_id` | CharField | Nullable — Postmark's internal reference |
| `mfa_required` | BooleanField | Default: False. When True, all employees in this tenant must complete MFA at every login. Administrator-controlled. UI recommends enabling this. |
| `session_timeout_minutes` | IntegerField | Default: 30. Min: 15, Max: 480 (8 hours). |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `EmployeePreference`
Per-employee settings.

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
| `logout_at` | DateTimeField | Nullable — set on normal logout or session expiry |
| `expiration_at` | DateTimeField | |
| `ip_address` | GenericIPAddressField | |
| `user_agent` | TextField | Raw User-Agent |
| `permission_snapshot` | JSONB | Permissions at login |
| `browser` | CharField | Parsed |
| `os` | CharField | Parsed |
| `device_type` | Enum | Mobile, Desktop |
| `mfa_used` | BooleanField | Default: False — True if MFA was completed for this session |
| `mfa_method` | Enum | Nullable — SMS, Email |
| `force_logout_at` | DateTimeField | Nullable — set when an Administrator force-revokes this session |
| `force_logout_by` | UUID FK → User | Nullable — the Administrator who triggered the revocation |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `LoginAttemptLog`
Immutable record of every login attempt, successful or failed. Written during the login flow after tenant context is resolved from `SubdomainIndex`. Used by Administrators to investigate suspicious access patterns.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Resolved from `SubdomainIndex` at attempt time. Not a FK — must survive tenant deletion for forensic purposes. |
| `user_email` | EmailField | The email submitted. Not a FK — the user may not exist. |
| `ip_address` | GenericIPAddressField | Source IP of the attempt |
| `user_agent` | TextField | Raw User-Agent string |
| `success` | BooleanField | True if login completed fully (including MFA if required) |
| `failure_reason` | Enum | Nullable — `invalid_password`, `account_locked`, `mfa_failed`, `mfa_expired`, `unknown_user` |
| `mfa_attempted` | BooleanField | Default: False — True if the attempt reached the MFA step |
| `attempted_at` | DateTimeField | auto_now_add |

> **Retention:** 18 months rolling, matching `SessionLog`. Records are never updated — only inserted. `UPDATE` and `DELETE` are revoked from `sdta_app` on this table (same hardening as `SystemAudits`).
> **RLS:** Subject to standard tenant RLS. Written after `SET LOCAL app.current_tenant_id` is established in the login flow.

### `SystemAudits`
Immutable history log. Never deleted.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `session_id` | UUID | Plain UUID — **not a FK**. `SessionLog` records are purged after 18 months; the session UUID is retained here for permanent historical correlation even after the `SessionLog` row is gone. |
| `user_id` | UUID FK → User | |
| `event_timestamp` | DateTimeField | |
| `action` | Enum | `Created`, `Updated`, `Deleted`, `Approved`, `Voided`, `StatusChanged`, `Terminated`, `Locked`, `Unlocked` |
| `entity_type` | CharField | e.g. WorkOrder, Invoice |
| `entity_id` | UUIDField | Record identifier |
| `record_number` | CharField | Human-readable (e.g. W26-0042) |
| `details` | JSONField | Contextual change detail |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |


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
| `display_name` | CharField | Optional override for list/header display. Falls back to `company_name`, then `customer_number`. |
| `dba` | CharField | "Doing Business As" — Commercial only |
| `legal_entity_type` | Enum | LLC, Corp, Partnership, SoleProp, NonProfit, Government, Other. Optional. |
| `tax_id` | EncryptedCharField | Encrypted at rest (PyNaCl SecretBox). |
| `ein` | EncryptedCharField | US Employer Identification Number. Encrypted at rest. |
| `vat_number` | EncryptedCharField | International VAT registration. Encrypted at rest. |
| `industry` | CharField | Value list slug = `industry` (NAICS top-level sectors, customizable). |
| `employee_count` | PositiveIntegerField | Optional firmographic. |
| `annual_revenue` | DecimalField | Optional firmographic. |
| `primary_person` | UUID FK → Person | Optional. Direct link for Residential customers (Commercial customers use the `contacts` table). on_delete=PROTECT. |
| `assigned_to` | UUID FK → User | Optional |
| `lead_source` | CharField | Dropdown (customizable) |
| `customer_since` | DateField | Optional. Once set, editable only by users with `is_tenant_admin=True`. |
| `hold_date` | DateTimeField | Nullable — set/cleared by lifecycle service when status enters/leaves Hold. |
| `hold_reason` | TextField | Nullable — set/cleared by lifecycle service when status enters/leaves Hold. |
| `closed_at` | DateTimeField | Nullable — set/cleared by lifecycle service when status enters/leaves Closed. |
| `closed_reason` | TextField | Nullable — set/cleared by lifecycle service when status enters/leaves Closed. See System Status V3 Section 2. |
| `inactive_at` | DateTimeField | Nullable — set/cleared by lifecycle service when status enters/leaves Inactive. |
| `inactive_reason` | TextField | Nullable — set/cleared by lifecycle service when status enters/leaves Inactive. |
| `account_number` | CharField | Required. User-facing customer identifier (distinct from `customer_number` system identifier and from the `Account` billing record). |
| `tags` | ArrayField/JSON | Free-text tags |
| `preferred_contact_method` | Enum | Email, Phone, SMS, Mail, None. Optional. |
| `do_not_contact` | BooleanField | Master DNC flag. Setting True cascades to all granular flags below. |
| `do_not_email` | BooleanField | When False, master is forced False. |
| `do_not_call` | BooleanField | When False, master is forced False. |
| `do_not_sms` | BooleanField | When False, master is forced False. |
| `marketing_opt_in` | BooleanField | Marketing comms opt-in (separate from transactional). |
| `preferred_language` | CharField | ISO 639-1 code. Default: 'en'. |
| `service_route` | CharField | Dispatch routing label. |
| `service_zone` | CharField | Geographic zone. |
| `access_instructions` | TextField | Driver-facing access notes (gate codes, dog warnings, side-door, etc.). |
| `preferred_technician` | UUID FK → User | Optional. on_delete=SET_NULL. |
| `preferred_service_window` | Enum | Morning, Afternoon, Evening, Anytime. Optional. |
| `requires_appointment` | BooleanField | Default: False. |
| `portal_user` | UUID FK → User | Optional, OneToOne. Customer self-service portal login (Plus+/Pro+ feature; field exists in Lite for forward-compat). on_delete=SET_NULL. |
| `external_id` | CharField | ID in an external system (QuickBooks, Xero, etc.) for sync. |
| `source_system` | CharField | Where this customer was imported from. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **DNC sync rules:** `Customer.save()` enforces a bidirectional sync between `do_not_contact` and the granular `do_not_email` / `do_not_call` / `do_not_sms` flags using a snapshot of prior values:
> - `do_not_contact` just promoted to True → all three granular flags forced True.
> - Any granular flag just demoted to False → `do_not_contact` forced False.
> - Setting all three granular flags True via direct assignment does NOT auto-promote `do_not_contact` (intentional — user may have set them individually for unrelated reasons).
>
> **State-context fields** (`hold_*`, `closed_*`, `inactive_*`) are denormalized synced caches of the audit log. Only `lifecycle.services.execute_transition` writes them, via `Customer._apply_lifecycle_transition`. The API serializer marks them read-only. Direct writes via raw `entity.save()` will drift them out of sync — always go through `execute_transition`.
>
> **Billing fields moved:** `account_terms`, `credit_limit`, `credit_status`, `tax_rate`, and `tax_exempt` are now stored on the `Account` model (1:1 with Customer). See `Account` below.

### `Account`
Represents the customer's billing/credit relationship with the tenant. Exactly one Account per Customer (1:1). Auto-created when a Customer is created. `account_number` lives on `Customer` because it is the user-facing customer identifier; everything that describes *how this customer does business with the tenant* (terms, credit, tax) lives here.

**Defaults at auto-create:** `account_terms` and `tax_rate` are seeded from `TenantPreference.default_payment_terms` and `TenantPreference.default_tax_rate` respectively. `credit_limit`, `credit_status`, and `tax_exempt` use the model defaults below.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | OneToOne, unique. on_delete=CASCADE. |
| `account_terms` | CharField | Dropdown (customizable). Seeded from `TenantPreference.default_payment_terms`. |
| `credit_limit` | DecimalField | Default: 0 |
| `credit_status` | Enum | Good, Fair, Poor. Default: Good |
| `tax_rate` | DecimalField | Optional — overrides tenant default. Seeded from `TenantPreference.default_tax_rate`. |
| `tax_exempt` | BooleanField | Default: False |
| `pricing_tier` | CharField | Optional pricing tier label (free-form until a `PriceBook` model is introduced in Plus+/Pro+). |
| `discount_percentage` | DecimalField | Blanket discount applied to all line items. Default: 0. |
| `po_required` | BooleanField | When True, invoices for this customer must reference a PO number. Default: False. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Person`
Permanent human identity. Holds attributes that don't vary by role — role-specific data (title, department, etc.) lives on `Contact`. Used by `Customer.primary_person`, `Vendor.contacts → Contact.person`, `User.person`, etc.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `prefix` | Enum | Mr, Mrs, Ms, Mx, Dr, Prof, Rev, Other. Optional. |
| `first_name` | CharField | Required |
| `middle_name` | CharField | Optional |
| `last_name` | CharField | Required |
| `suffix` | Enum | Jr, Sr, II, III, IV, PhD, MD, Esq, Other. Optional. |
| `preferred_name` | CharField | What the person prefers to be called. Display alternative to `first_name`; legal name preserved. |
| `date_of_birth` | DateField | Optional. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Display rules:** `__str__` returns `"{preferred_name or first_name} {last_name}"`. Use `full_legal_name()` method for formal contexts (contracts, mailing labels): `"{prefix} {first} {middle} {last}, {suffix}"` with empty parts skipped.

### `Contact`
Bridge table linking a `Person` to a `Customer`, `Vendor`, or `Bank`.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `person_id` | UUID FK → Person | Required |
| `customer_id` | UUID FK → Customer | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `role_title` | CharField | Optional |
| `department` | CharField | Optional |
| `is_primary` | BooleanField | One primary per parent entity |
| `status` | Enum | Active, Left |
| `start_date` | DateField | Optional |
| `left_date` | DateField | Nullable |
| `reports_to` | UUID FK → Contact | Self-referential for org hierarchy at the parent company. Nullable. on_delete=SET_NULL. |
| `is_decision_maker` | BooleanField | This contact has buying authority. Default: False. |
| `is_billing_contact` | BooleanField | Receives invoices and billing communications. Default: False. |
| `is_technical_contact` | BooleanField | Receives technical/service communications. Default: False. |
| `is_emergency_contact` | BooleanField | Contacted for emergencies. Default: False. |
| `notes` | TextField | Free-text relationship notes. |
| `last_contacted_at` | DateTimeField | Most recent successful outbound contact. Nullable. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Constraint:** Exactly one of `customer_id`, `vendor_id`, or `bank_id` must be populated (DB CHECK).

### `Address`
Physical or mailing addresses. Shared across entities.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `asset_id` | UUID FK → Asset | Nullable — physical site |
| `user_id` | UUID FK → User | Nullable — employee address |
| `warehouse_id` | UUID FK → Warehouse | Nullable |
| `work_group_id` | UUID FK → WorkGroup | Nullable |
| `address_type` | Enum | Service, Billing, Mailing, Other |
| `is_primary` | BooleanField | |
| `street` | CharField | |
| `street_2` | CharField | Apt/Suite/Floor — second address line. |
| `city` | CharField | |
| `state` | CharField | Full state/region name. |
| `state_code` | CharField | State/region abbreviation (CA, NY, TX). For dispatch routing. |
| `zip` | CharField | |
| `country_code` | CharField | ISO 3166-1 alpha-2 country code (US, GB, CA). |
| `latitude` | DecimalField | Geocoded latitude (±90, 7 decimal places ≈ 1.1cm). Nullable. |
| `longitude` | DecimalField | Geocoded longitude (±180, 7 decimal places). Nullable. |
| `geocoded_at` | DateTimeField | When the address was last geocoded. Nullable. |
| `is_verified` | BooleanField | Address validated against an authoritative source (USPS, etc.). Default: False. |
| `verified_at` | DateTimeField | When the address was last verified. Nullable. |
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
| `bank_id` | UUID FK → Bank | Nullable |
| `user_id` | UUID FK → User | Nullable |
| `warehouse_id` | UUID FK → Warehouse | Nullable |
| `phone_type` | Enum | Mobile, Office, Home, Fax, Other |
| `country_code` | CharField | International dialing code, including '+' (e.g. '+1', '+44'). |
| `number` | CharField | |
| `is_primary` | BooleanField | |
| `extension` | CharField | Optional |
| `sms_capable` | BooleanField | Whether this number can receive SMS. Independent of phone_type. Default: False. |
| `is_verified` | BooleanField | Number has been verified (e.g., SMS code). Default: False. |
| `verified_at` | DateTimeField | When the number was last verified. Nullable. |
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

### `SubAsset`
Links a child asset to a parent asset. ERD: Sub Assets(Assets) (FK Asset, FK Customer). Replaces the former `parent_asset_id` self-FK on `Asset`.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `asset_id` | UUID FK → Asset | The parent asset |
| `sub_asset_id` | UUID FK → Asset | The child / sub asset |
| `customer_id` | UUID FK → Customer | Denormalized from Asset for query performance |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

> **Constraint:** `asset_id` and `sub_asset_id` must not be equal.

### `Product`
Central catalog. Product in specs = Inventory in ERD.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `product_number` | CharField | Auto-generated via reverse-alphabet year encoding (e.g., YU-0001 for 2026). See Numbering Service V1 §6.1. |
| `name` | CharField | Required |
| `status` | Enum | `Active`, `Hold`, `Discontinued`. See System Status Specification V3 Section 19. |
| `type` | Enum | Service, Product - Inventory, Product - Non-Inventory |
| `category` | CharField | Dropdown (customizable) |
| `sku` | CharField | Optional |
| `unit_cost` | DecimalField | Internal cost |
| `unit_price` | DecimalField | Customer price |
| `description` | TextField | |
| `taxable` | BooleanField | Default: True |
| `is_bundle` | BooleanField | |
| `preferred_vendor_id` | UUID FK → Vendor | Nullable (Plus+) |
| `low_stock_threshold` | IntegerField | Nullable. Configurable per product. System sets `is_low_stock = True` when `quantity_on_hand` falls at or below this value. |
| `is_low_stock` | BooleanField | Default: False. System-managed — do not set manually. |
| `is_out_of_stock` | BooleanField | Default: False. System-managed — do not set manually. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Stock flags:** `is_low_stock` and `is_out_of_stock` are system-managed boolean fields. They do not block product usage by default — they serve as triggers for notifications and alerts to purchasing staff. `low_stock_threshold` applies to `Product - Inventory` type products only. See System Status Specification V3 Section 19.1.

### `KitItem`
Items within a Product Kit. ERD: Kit Items (FK MasterInventory, FK Inventory).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `kit_id` | UUID FK → Product | Parent kit product |
| `product_id` | UUID FK → Product | Included item |
| `quantity` | DecimalField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 1.4 Service Request & Service Delivery

### `ServiceRequest`
Entry point for customer service requests. ERD: Service Request (FK Asset, FK Customer) — renamed to ServiceRequest.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `service_request_number` | CharField | Auto-generated (SR26-0001) |
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
| `service_request_id` | UUID FK → ServiceRequest | Nullable — originating request |
| `workflow_id` | UUID FK → WorkFlow | Nullable — operational SOP (Pro/Enterprise) |
| `prev_maint_id` | UUID FK → PreventativeMaintenance | Nullable — originating PM |
| `work_group_id` | UUID FK → WorkGroup | Nullable — dispatch group (Plus+) |
| `wg_division_id` | UUID FK → WGDivision | Nullable |
| `vehicle_id` | UUID FK → Vehicle | Nullable — Fleet add-on |
| `address_id` | UUID FK → Address | Nullable — service location for this work order |
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



### `TaskTime`
ERD: TaskTimes (FK Task, FK Employee). Clock-in/out time entries recorded against a Task.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `task_id` | UUID FK → Task | |
| `employee_id` | UUID FK → User | |
| `clock_in` | DateTimeField | |
| `clock_out` | DateTimeField | Nullable |
| `total_hours` | DecimalField | Calculated |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `TaskToDo`
ERD: TaskToDos (FK Task, FK Employee). Checklist items recorded against a Task.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `task_id` | UUID FK → Task | |
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
| `opportunity_id` | UUID FK → Opportunity | Nullable (Pro+) |
| `converted_to_work_order_id` | UUID FK → WorkOrder | Nullable — backlink |
| `converted_to_invoice_id` | UUID FK → Invoice | Nullable — backlink |
| `work_group_id` | UUID FK → WorkGroup | Nullable (Plus+) |
| `contact_id` | UUID FK → Contact | Nullable |
| `address_id` | UUID FK → Address | Nullable — service location for this quote |
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
| `sent_at` | DateTimeField | Set by lifecycle service when status enters Sent. |
| `accepted_at` | DateTimeField | Set when status enters Accepted. |
| `declined_at` | DateTimeField | Set when status enters Declined. |
| `declined_reason` | TextField | Set from the transition reason when declined. |
| `expired_at` | DateTimeField | Set when status enters Expired. |
| `invoiced_at` | DateTimeField | Set when status enters Invoiced. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Lifecycle:** Forward-only (Draft → Sent → Accepted/Declined/Expired → Invoiced). Lifecycle context fields are set by `Quote._apply_lifecycle_transition` and never cleared (historical milestones). No reasons are required on transitions per the seed.

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
| `is_discount` | BooleanField | Default: False. Forces is_tax_charged = False |
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
| `address_id` | UUID FK → Address | Nullable — service location for this invoice |
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
| `amount_paid` | DecimalField | Denormalized sum of linked Payments. Updated on payment create/void. Default: 0.00 |
| `balance_due` | DecimalField | Calculated: invoice_total − deposit_applied − amount_paid. Updated on line item or payment change. Default: 0.00 |
| `stripe_payment_link_id` | CharField | Nullable |
| `stripe_payment_link_url` | URLField | Nullable |
| `deposit_applied` | DecimalField | From quote deposit |
| `notes` | TextField | Customer-visible |
| `internal_notes` | TextField | |
| `is_recurring` | BooleanField | Plus+ |
| `recurrence_pattern` | JSONField | Nullable |
| `sent_at` | DateTimeField | Set by lifecycle service when status enters Sent. |
| `paid_at` | DateTimeField | Set when status enters Paid. |
| `overdue_at` | DateTimeField | Set when status enters Overdue. |
| `voided_at` | DateTimeField | Set when status enters Voided. |
| `voided_reason` | TextField | Required when status=Voided. Set by lifecycle service from the transition reason. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Lifecycle:** Mostly forward, with reversibility between Sent/Partial/Overdue (a payment after Overdue moves back to Partial or Paid). Lifecycle context fields are set by `Invoice._apply_lifecycle_transition` and never cleared (historical milestones). `voided_reason` is required by `Invoice.save()` when status=Voided.

> **Implementation Note:** The `Issued → Viewed` status transition is triggered when the customer accesses the Stripe-hosted payment link. The transition mechanism should be implemented via Stripe Checkout session tracking (e.g., the `checkout.session.completed` event or a redirect callback from the payment page). See Stripe Webhook Specification V1 for event handling.

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
| `is_surcharge` | BooleanField | Default: False |
| `is_tax_charged` | BooleanField | Default: True |
| `visible_to_customer` | BooleanField | |
| `sort_order` | IntegerField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `WorkOrderInvoice`
Junction table enabling multiple invoices to be created against a single Work Order. ERD: WorkOrder Invoice (FK WorkOrder, FK Invoice, FK Customer). Added in V12.

> **Purpose:** Prior to V12, a Work Order linked to a single Invoice via `Invoice.work_order_id`. `WorkOrderInvoice` extends this by allowing multiple Invoice records to be associated with one Work Order — for example, a deposit invoice followed by a completion invoice, or progress billing across milestones. `Invoice.work_order_id` is retained as the originating/primary backlink; `WorkOrderInvoice` tracks the full set of invoices issued against the work order.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Required, indexed |
| `work_order_id` | UUID FK → WorkOrder | Required |
| `invoice_id` | UUID FK → Invoice | Required |
| `customer_id` | UUID FK → Customer | Denormalized from Invoice for query performance |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

> **Constraint:** `(tenant_id, work_order_id, invoice_id)` unique together — an invoice cannot be linked to the same work order more than once.

---

### `Payments`
Unified payments table covering both customer (AR) and vendor (AP) payments. ERD: Payments (FK Invoice, FK Customer, FK Employee, FK Purchasing, FK Vendor, FK VendorBills, FK Stripe Response).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `payment_number` | CharField | Auto-generated (P26-0001) |
| `payment_type` | Enum | CustomerPayment, VendorPayment |
| `status` | Enum | `Paid`, `Failed`, `Voided`. See System Status Specification V3 Section 5.2. |
| `invoice_id` | UUID FK → Invoice | Nullable — populated for CustomerPayment |
| `customer_id` | UUID FK → Customer | Nullable — populated for CustomerPayment |
| `vendor_id` | UUID FK → Vendor | Nullable — populated for VendorPayment |
| `purchase_order_id` | UUID FK → PurchaseOrder | Nullable — populated for VendorPayment |
| `vendor_bill_id` | UUID FK → VendorBill | Nullable — populated for VendorPayment |
| `employee_id` | UUID FK → User | Who recorded the payment |
| `stripe_response_id` | UUID FK → StripeResponse | Nullable |
| `payment_date` | DateField | |
| `amount` | DecimalField | Amount successfully captured and applied to the invoice balance. |
| `amount_tried` | DecimalField | Amount attempted during the transaction (always positive). May differ from `amount` on failed or partial captures. |
| `payment_method` | Enum | Credit/Debit Card, Cash, Check, Bank Transfer, Other |
| `reference_number` | CharField | |
| `stripe_payment_intent_id` | CharField | Nullable |
| `notes` | TextField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---

## 1.6 General Purpose Tasks

### `Task`
General purpose task. May be standalone or optionally linked to a Work Order, WGDivision, and/or WorkGroup by the user at runtime.

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
| `customer_id` | UUID FK → Customer | Nullable |
| `asset_id` | UUID FK → Asset | Nullable |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `wg_division_id` | UUID FK → WGDivision | Nullable |
| `work_group_id` | UUID FK → WorkGroup | Nullable |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `AssociatedTask`
Self-referential junction linking tasks to one another. ERD: AssociatedTasks (FK TaskParent, FK TaskAssoc). Used to express parent-child or related-task relationships.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `task_parent_id` | UUID FK → Task | The originating or parent task |
| `task_assoc_id` | UUID FK → Task | The linked or child task |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

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
| `service_request_id` | UUID FK | Nullable |
| `prev_maint_id` | UUID FK | Nullable |
| `workflow_id` | UUID FK | Nullable |
| `payment_id` | UUID FK | Nullable |
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
| `original_filename` | CharField | The filename as submitted by the user. Sanitized before storage (see File Upload Specification V1 Section 3.3). |
| `file_key` | CharField | Full S3/Spaces object path. **Internal use only — must never appear in API responses, HTMX fragments, or HTML attributes.** Only `document_uuid` (this record's `id`) is exposed to the frontend. See File Upload Specification V1 Section 5.2. |
| `file_size_bytes` | BigIntegerField | |
| `mime_type` | CharField | Verified via magic-byte sniffing — not trusted from the upload request. |
| `sha256_hash` | CharField | SHA-256 hash of the uploaded file content. Used for integrity verification. |
| `scan_status` | Enum | `Pending`, `Clean`, `Infected`. Set to `Pending` on upload; updated by the ClamAV scanning worker. Only `Clean` documents are accessible via pre-signed URL. |
| *(all parent FKs)* | | Same as Note entity — same exclusive arc |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Implementation Note:** Document has the identical set of nullable parent FKs as Note. For brevity they are not repeated here — refer to the Note model above.

> **Security Note:** The `scan_status` field gates all file access. Documents with `scan_status = Pending` or `scan_status = Infected` must never be served, regardless of the requestor's authentication status. See File Upload Specification V1 Sections 3.3 and 5.2.

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

### `IssuesErrors`
ERD: Issues_Errors (FK Session, FK ErrorCode).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Nullable |
| `user_id` | UUID FK → User | Nullable |
| `error_code_id` | UUID FK → ErrorCode | Nullable — standardized error classification (Pro/Enterprise) |
| `error_type` | CharField | Exception class name — free-text fallback |
| `message` | TextField | |
| `traceback` | TextField | Never exposed to user |
| `occurred_at` | DateTimeField | |
| `request_path` | CharField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---

## 1.10 Stripe Integration

### `StripeConnection`

> **ERD Note:** The Base System V12 ERD shows `Stripe Connections` with `FK Customer` and `FK Stripe ID`. In the SaaS architecture, this is a **per-tenant** record (one Stripe Connect account per tenant business), not per-customer. The `tenant_id` field serves this purpose; there is no `customer_id` FK on this model.
>
> **Spec/code divergence (May 2026):** This table describes the **Stripe Connect** marketplace pattern (platform OAuth flow with per-tenant access tokens). The current code at `infrastructure/models.py:406` instead implements **Stripe Billing** — the tenant pays the platform via Customer/Subscription, with `stripe_customer_id` and `stripe_subscription_id` fields and no access token. The two are different Stripe products. The Billing model is correct for the current Lite/Plus+ "tenant pays SaaS" flow; the Connect fields below remain in the spec for whenever Pro+/Enterprise marketplace features ship. When that happens, `access_token` should be added as an `EncryptedCharField` (PyNaCl SecretBox via `config.fields.EncryptedCharField`).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | Unique |
| `stripe_account_id` | CharField | Connect account ID (`acct_…`). |
| `access_token` | EncryptedCharField | Connect platform OAuth token. Encrypt with `config.fields.EncryptedCharField` when implemented. |
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

> **Note:** The models in this section (`TenantState`, `StorageTracker`, `OnboardingState`, `TenantAddOn`, `TenantSyncLog`) are SDTA-local infrastructure tables. They cache data originally authoritative in SDP and do not carry standard `created_by` / `updated_by` audit fields unless specified. All are excluded from standard multi-tenant RLS — they are either tenant-identity records or operate at a scope above individual tenant rows.

### `TenantState`
Single record per tenant. Caches the tenant's current account status, plan tier, and limits as received from SDP. All enforcement decisions in SDTA (tier-gating, seat limits, storage limits) are made against this table. Updated via the SDTA Internal API.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | **Set to the SDP-assigned `tenant_id` at provisioning.** This record's PK is the tenant UUID — there is no separate `tenant_id` column. |
| `status` | Enum | `Active`, `Suspended`, `Read Only`, `Cancelled (Pending Expiry)`, `Cancelled (Read Only)`, `Cancelled`, `Pending Deletion` |
| `tier` | Enum | `Lite`, `Plus`, `Pro`, `Enterprise` |
| `seat_limit` | IntegerField | Current maximum seat count |
| `storage_limit_bytes` | BigIntegerField | Current maximum storage in bytes |
| `email_points_included` | IntegerField | Email points included in the current plan period. Set at provisioning and updated on plan changes. Lite = 400 (manual only: quotes/invoices — no automated triggers), Plus = 1,600, Pro = 4,000, Enterprise = 12,000. See Pricing & Billing Specification V2 Section 10A.4. |
| `email_period_start` | DateField | Billing anniversary date for email point resets. Set at provisioning; updated if billing date changes. |
| `sms_points_included` | IntegerField | SMS points included in the current plan period. Set at provisioning and updated on plan changes. Lite = 100 (manual only — no automated triggers), Plus = 350, Pro = 750, Enterprise = TBD. See Pricing & Billing Specification V2 Section 10.2. |
| `sms_period_start` | DateField | Billing anniversary date for SMS point resets. |
| `deletion_scheduled_at` | DateTimeField | Nullable. Set to `now() + 60 days` when `status` transitions to `Pending Deletion`. The `purge_deleted_tenant_data` background task uses this field to determine when the 60-day deletion window has elapsed. |
| `onboarding_wizard_completed` | BooleanField | Default: False. Set to True when the Administrator completes the onboarding setup wizard. |
| `updated_on` | DateTimeField | Timestamp of last sync from SDP |

### `StorageTracker`
Tracks current file storage usage per tenant. Updated on every file upload completion and deletion.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Unique — one record per tenant. References `TenantState.id`. |
| `total_bytes_used` | BigIntegerField | Current committed storage in bytes (Clean files only). |
| `pending_bytes` | BigIntegerField | Default: 0. Bytes reserved for files currently in Quarantine (scan pending). Added to `total_bytes_used` for quota enforcement during upload streams. Cleared when a file is promoted (Clean) or deleted (Infected). |
| `updated_on` | DateTimeField | auto_now |

> **Quota enforcement:** Before any upload, the system checks `total_bytes_used + pending_bytes >= storage_limit_bytes` (from `TenantState`). If true, the upload is rejected with a `413 Payload Too Large` error. See File Upload Specification V1 Section 3.1.

### `EmailUsageTracker`
Tracks per-tenant email point consumption within the current billing period. SDTA-local — updated on each confirmed outbound email delivery webhook from Postmark.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Unique — one record per tenant. References `TenantState.id`. |
| `email_points_used` | IntegerField | Default: 0. Incremented on each confirmed outbound send (delivery webhook confirms delivery). Failed/bounced sends do not increment. |
| `email_points_overage` | IntegerField | Default: 0. Accumulates sends beyond `TenantState.email_points_included`. Charged at end of billing period via Stripe. |
| `updated_on` | DateTimeField | auto_now |

> **Reset:** At each tenant's `email_period_start` anniversary, both `email_points_used` and `email_points_overage` are reset to 0 by the `reset_email_usage_counters` background task. See Email Specification V1 Section 7.2.
> **Alerts:** At 80% of `email_points_included` — in-app notification. At 100% — in-app notification + email to Administrator.

### `SMSUsageTracker`
Tracks per-tenant SMS point consumption within the current billing period. SDTA-local — updated on each confirmed SMS delivery via Twilio.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Unique — one record per tenant. References `TenantState.id`. |
| `sms_points_used` | IntegerField | Default: 0. Incremented on each confirmed outbound SMS segment. Failed/undelivered segments do not increment. |
| `sms_points_overage` | IntegerField | Default: 0. Accumulates SMS segments beyond `TenantState.sms_points_included`. Charged at end of billing period via Stripe. |
| `updated_on` | DateTimeField | auto_now |

> **Reset:** At each tenant's `sms_period_start` anniversary, both `sms_points_used` and `sms_points_overage` are reset to 0 by the `reset_sms_usage_counters` background task. See Background Tasks Specification V2 for the `reset_sms_usage_counters` task definition.

### `OnboardingState`
Tracks onboarding checklist completion per tenant. One record per tenant, created during provisioning.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Unique — one record per tenant. |
| `checklist_items` | JSONField | Keys are checklist item identifiers; values are `True` (complete) or `False` (incomplete). All items initialized to `False` at provisioning. |
| `is_completed` | BooleanField | Default: False. Set to True when all required items are `True`. Dashboard widget is hidden when True. |
| `updated_on` | DateTimeField | auto_now |

> See Onboarding Checklist Specification V2 for the full list of items and trigger logic.

### `TenantAddOn`
Records active add-on features for a tenant. Updated by the SDTA Internal API when SDP changes a tenant's add-on entitlements. SDTA enforces feature-gating against this table.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | References `TenantState.id` |
| `add_on_key` | CharField | Identifier for the add-on feature (e.g., `fleet_management`, `custom_email_domain`) |
| `is_active` | BooleanField | |
| `activated_at` | DateTimeField | Nullable |
| `deactivated_at` | DateTimeField | Nullable |
| `updated_on` | DateTimeField | auto_now |

> **Unique constraint:** `(tenant_id, add_on_key)` — one row per feature per tenant.

### `TenantSyncLog`
Immutable audit log recording every Internal API call received from SDP. Never deleted — retained for debugging and auditability of SDP → SDTA sync events.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Plain UUID — not a FK. Survives `TenantState` deletion. |
| `sync_type` | Enum | `ProvisionTenant`, `UpdateStatus`, `UpdateLimits`, `UnlockAdmin`, `ForceSync` |
| `occurred_at` | DateTimeField | auto_now_add |
| `status` | Enum | `Success`, `Failed` |
| `request_payload` | JSONField | Sanitized inbound payload — password hash fields stripped before storage. |
| `response_code` | IntegerField | HTTP status code returned to SDP |
| `details` | TextField | Nullable — error message if `status = Failed` |

---

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

## 2.1 CRM Pipeline (Plus+ / Pro+)

> **Tier note:** `Lead` is a Plus+ feature. `Opportunity` and `OpportunityContacts` are Pro+ features.

### `Lead` (Plus+)

A Lead is the sales-tracking shell around a Customer + Person pair. It holds **only sales-workflow data** (source, status, score, follow-up) and lifecycle history. All operational data (name, phone, email, address, notes) lives on the linked Customer or Person — Lead does NOT duplicate any of it.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `lead_number` | CharField | Auto-generated |
| `customer_id` | UUID FK → Customer | **Required**. on_delete=PROTECT. The Customer record (Residential or Commercial) is the anchor for everything. If the customer isn't already in the system, create one first. |
| `person_id` | UUID FK → Person | **Required**. on_delete=PROTECT. Identifies which human at the customer this lead is about: for Residential, typically `customer.primary_person`; for Commercial, a contact at the company. |
| `source` | Enum | Referral, Website, Advertisement, Trade Show, Cold Call, Other |
| `status` | Enum | New, Contacted, Qualified, Converted, Lost |
| `tags` | ArrayField/JSON | Free-text tags |
| `assigned_to` | UUID FK → User | Sales rep working this lead. |
| `lead_score` | DecimalField | Lead quality score, 0–100. Nullable. |
| `last_contacted_at` | DateTimeField | Most recent outreach. Nullable. |
| `next_followup_at` | DateTimeField | Scheduled next touch. Nullable. |
| `qualified_at` | DateTimeField | Set by lifecycle service when status enters Qualified. |
| `converted_at` | DateTimeField | Set by lifecycle service when status enters Converted. |
| `lost_at` | DateTimeField | Set by lifecycle service when status enters Lost. |
| `lost_reason` | TextField | Required when status=Lost. Set by lifecycle service from the transition reason. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Where data lives** (Lead does NOT duplicate any of these):
> - **Name** → `lead.person.first_name` / `last_name` / `preferred_name` etc.
> - **Phones** → `lead.customer.phones` (Phone bridge, scoped to Customer)
> - **Emails / socials** → `lead.customer.socials` (Social bridge, type='Email' for emails)
> - **Addresses** → `lead.customer.addresses` (Address bridge)
> - **Notes** → `Note` records with `lead` FK (ExclusiveArc pattern)
> - **Account type / company name** → `lead.customer.account_type` / `lead.customer.company_name`
>
> **Lifecycle:** Forward-only (New → Contacted → Qualified → Converted/Lost). The `qualified_at` / `converted_at` / `lost_at` timestamps are set by `Lead._apply_lifecycle_transition` and never cleared. `lost_reason` is required by `Lead.save()` when status=Lost.

### `Opportunity` (Pro+)

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `opportunity_number` | CharField | Auto-generated |
| `customer_id` | UUID FK → Customer | Required |
| `lead_id` | UUID FK → Lead | Nullable |
| `name` | CharField | |
| `status` | Enum | Open, Won, Lost |
| `estimated_value` | DecimalField | Forecast value at creation. Default: 0. |
| `actual_value` | DecimalField | Realized value when Won. Defaults to `estimated_value` if unset at the Won transition. Nullable until Won. |
| `probability` | DecimalField | Conversion likelihood, 0–100. Nullable. |
| `expected_close_date` | DateField | |
| `assigned_to` | UUID FK → User | |
| `next_step` | CharField | The next action to advance this opportunity. |
| `competitor` | CharField | Who else is bidding. |
| `notes` | TextField | |
| `tags` | ArrayField/JSON | Free-text tags |
| `won_at` | DateTimeField | Set by lifecycle service when status enters Won. |
| `lost_at` | DateTimeField | Set by lifecycle service when status enters Lost. |
| `lost_reason` | TextField | Required when status=Lost. Set by lifecycle service from the transition reason. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> **Lifecycle:** Forward-only (Open → Won/Lost, both final). `won_at` / `lost_at` are set by `Opportunity._apply_lifecycle_transition`. On Won, if `actual_value` is None it defaults to `estimated_value`. `lost_reason` is required by `Opportunity.save()` when status=Lost.

### `OpportunityContacts` (Pro+)
ERD: OpportunityContact (FK Opportunity, FK Contact, FK Company).

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
| `status` | Enum | Active, Inactive, Expired, Cancelled, Pending |
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
Three-way junction: Customer + Agreement + Asset. Represents a specific customer's enrollment in an Agreement for a specific Asset. Has its own lifecycle separate from the Agreement template.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Required |
| `agreement_id` | UUID FK → Agreement | Required |
| `asset_id` | UUID FK → Asset | Required |
| `status` | Enum | `Pending`, `Active`, `Expired`, `Cancelled`. See System Status Specification V3 Section 11.3. |
| `start_date` | DateField | Date the agreement coverage begins for this customer/asset |
| `end_date` | DateField | Nullable — null indicates ongoing coverage |
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
| `status` | Enum | `Open`, `In Progress`, `Completed`, `Cancelled`. See System Status Specification V3 Section 24. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `WorkGroupAsset`
Rolled-up view of all assets in a WorkGroup.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `work_group_id` | UUID FK → WorkGroup | |
| `asset_id` | UUID FK → Asset | |

> **Implementation Note:** System-managed junction — records are auto-created when a Work Order with a non-null `asset_id` is added to a WorkGroup, and auto-deleted when the Work Order is removed. Not user-editable via UI or API. See Top-Down Specifications V4 for the full automation rule.

---

## 2.4 Purchasing & Vendors (Plus+)

### `Vendor`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vendor_number` | CharField | Auto-generated (V26-0001) |
| `name` | CharField | Required (was `vendor_name` in earlier spec — code field is `name`). |
| `status` | Enum | `Active`, `Inactive`, `Do Not Use`. See System Status Specification V3 Section 20. |
| `account_number` | CharField | Optional. The tenant's account identifier *with* this vendor (kept on Vendor for fast lookup, mirrors Customer.account_number). |
| `tax_id` | EncryptedCharField | Encrypted at rest (PyNaCl SecretBox). |
| `notes` | TextField | |
| `tags` | ArrayField/JSON | Free-text tags |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

> Contacts, Addresses, Phones via shared Triad tables.
> **Billing fields moved:** `payment_terms` is now stored on the `VendorAccount` model (1:1 with Vendor). See `VendorAccount` below.

### `VendorAccount`
Represents the tenant's billing/credit relationship *with* the vendor. Exactly one VendorAccount per Vendor (1:1). Auto-created when a Vendor is created. Mirrors the Customer/Account split — `account_number` and `tax_id` (vendor identity / our reference to them) live on `Vendor`; everything that describes *how the tenant does business with this vendor* (terms, credit, tax, pricing) lives here.

**Defaults at auto-create:** `payment_terms` and `tax_rate` are seeded from `TenantPreference.default_payment_terms` and `TenantPreference.default_tax_rate` respectively. Other fields use the model defaults below.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `vendor_id` | UUID FK → Vendor | OneToOne, unique. on_delete=CASCADE. |
| `payment_terms` | CharField | When the tenant must pay this vendor (Net 30, etc.). Seeded from `TenantPreference.default_payment_terms`. |
| `credit_limit` | DecimalField | Vendor's credit limit *for the tenant* (how much the tenant may owe before payment is required). Default: 0. |
| `credit_status` | Enum | The tenant's standing with this vendor: Good, Fair, Poor. Default: Good. |
| `tax_rate` | DecimalField | Optional — overrides tenant default if vendor charges a different rate. Seeded from `TenantPreference.default_tax_rate`. |
| `tax_exempt` | BooleanField | Whether the tenant is tax-exempt with this vendor. Default: False. |
| `pricing_tier` | CharField | Optional pricing tier label (volume discount, contract pricing, etc.). |
| `discount_percentage` | DecimalField | Blanket discount the vendor extends to the tenant. Default: 0. |
| `po_required` | BooleanField | When True, this vendor requires a PO from the tenant for every order. Default: False. |
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

### `VendorBill`

> **Design Note:** VendorBill is a single-amount header record — it does not have a separate `VendorBillLine` table. The vendor's bill amount is stored directly on this record. This matches the ERD (Base System V12), which shows `VendorBills` with no child line-item entity.

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

### `Accounting`
ERD: Accounting (FK Customer, FK Bank).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `customer_id` | UUID FK → Customer | Nullable |
| `bank_id` | UUID FK → Bank | Nullable |
| `account_type` | CharField | Receivable, Payable, Revenue, Expense, etc. |
| `balance` | DecimalField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `Ledger`
ERD: Ledger (FK Payments, FK Customer, FK Vendor, FK Purchasing, FK Invoice).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `payment_id` | UUID FK → Payments | Nullable — covers both customer and vendor payments |
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
Administrative or organizational location. Links a department or warehouse to a named physical place. Distinct from `SubLocation`, which represents a specific bin, shelf, or section within a warehouse for inventory placement. ERD: Locations (FK Department, FK Warehouse).

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

### `EmployeePurchase`
Records purchases made by an employee via a corporate credit card. ERD: Purchases (FK Emp_C_Card).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `credit_card_id` | UUID FK → CreditCard | |
| `employee_id` | UUID FK → User | |
| `amount` | DecimalField | |
| `purchase_date` | DateField | |
| `description` | CharField | |
| `category` | CharField | Dropdown — e.g. Fuel, Parts, Tools, Travel, Other |
| `receipt_document_id` | UUID FK → Document | Nullable |
| `status` | Enum | Pending, Approved, Rejected |
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
| `status` | Enum | `Active`, `Inactive`, `Discontinued`. See System Status Specification V3 Section 23. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

---


## 3.5 Project Management (Enterprise)

> **Note:** Portfolio, Sprint, and Milestone models support the ServizDesk Projects product vertical. In the ServizDesk Service context, WorkGroup is the primary grouping mechanism. These models are Enterprise-tier.

### `Portfolio`
Groups multiple Projects (WorkGroups) together for high-level oversight and reporting.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | Required |
| `description` | TextField | |
| `status` | Enum | Active, Archived |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `PortfolioProject`
Junction mapping Projects (WorkGroups) to Portfolios. A WorkGroup may belong to more than one Portfolio.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `portfolio_id` | UUID FK → Portfolio | |
| `project_id` | UUID FK → WorkGroup | Maps WorkGroup as the Project entity |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `PortfolioMember`
Employees assigned to a Portfolio for oversight or reporting access.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `portfolio_id` | UUID FK → Portfolio | |
| `employee_id` | UUID FK → User | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `Sprint`
Time-boxed iteration within a Project (WorkGroup). Used for Agile planning in the Projects vertical.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `project_id` | UUID FK → WorkGroup | |
| `name` | CharField | Required |
| `goal` | TextField | Optional — sprint objective |
| `start_date` | DateField | |
| `end_date` | DateField | |
| `status` | Enum | Planned, Active, Completed, Cancelled |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `SprintMember`
Employees assigned to a Sprint.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `sprint_id` | UUID FK → Sprint | |
| `employee_id` | UUID FK → User | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `SprintTask`
Junction linking Tasks to a Sprint.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `sprint_id` | UUID FK → Sprint | |
| `task_id` | UUID FK → Task | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `Milestone`
A named checkpoint or deliverable within a Project (WorkGroup).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `project_id` | UUID FK → WorkGroup | |
| `name` | CharField | Required |
| `description` | TextField | |
| `due_date` | DateField | |
| `status` | Enum | Pending, In Progress, Completed, Missed |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `MilestoneTask`
Junction linking Tasks to a Milestone.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `milestone_id` | UUID FK → Milestone | |
| `task_id` | UUID FK → Task | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---

## 3.6 Communications & Zones (Enterprise)

### `TerritoryZone`
A defined geographic or operational service zone. `employee_id` identifies the zone manager or owner. Service coverage assignments — which employees cover which zones — are managed via the `EmployeeZone` junction table.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | Required |
| `employee_id` | UUID FK → User | Zone manager / owner — not the same as service coverage assignment |
| `description` | TextField | |
| `status` | Enum | Active, Inactive |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `EmployeeZone`
Junction assigning employees to service coverage zones. An employee may cover multiple zones.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `zone_id` | UUID FK → TerritoryZone | |
| `employee_id` | UUID FK → User | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `CommunicationTrigger`
Defines a system event that can fire automated communications.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `event_name` | CharField | Required — e.g. "Work Order Completed" |
| `description` | TextField | |
| `is_active` | BooleanField | Default: True |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `CommunicationTemplate`
A reusable message template for automated communications.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `name` | CharField | Internal label |
| `subject` | CharField | Used for Email channel |
| `body` | TextField | Supports merge tags |
| `channel` | Enum | Email, SMS, Push |
| `status` | Enum | Active, Inactive, Draft |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `TriggerTemplate`
Junction linking a CommunicationTrigger to one or more CommunicationTemplates.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `trigger_id` | UUID FK → CommunicationTrigger | |
| `template_id` | UUID FK → CommunicationTemplate | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `TriggerLog`
Audit trail recording each time a CommunicationTrigger fires. ERD: TriggerLog (FK Trigger).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `trigger_id` | UUID FK → CommunicationTrigger | |
| `fired_at` | DateTimeField | |
| `recipient` | CharField | Email address or user identifier |
| `channel` | Enum | Email, SMS, Push |
| `status` | Enum | Sent, Failed, Suppressed |
| `error_message` | TextField | Nullable — populated on failure |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---

## 3.7 System Logging (Enterprise)

Enterprise-tier audit trail models derived from the System Logs ERD V1. Records system errors with standardized codes, background process execution, and user navigation history per session.

### `ErrorCode`
Lookup table for standardized system error classification. ERD: Error_Codes (fld Description).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `code` | CharField | Unique per tenant — e.g. ERR-4001 |
| `description` | TextField | Human-readable explanation |
| `severity` | Enum | Info, Warning, Error, Critical |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

### `ProcessTransaction`
Records background system processes tied to a session. ERD: Process_Transactions (FK Session).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `session_id` | UUID | Plain UUID — **not a FK**. Purged together with `SessionLog` in the 18-month rolling retention task. The plain UUID avoids FK conflict during the purge sweep. |
| `process_name` | CharField | e.g. "PM Auto-Generate Work Orders" |
| `entity_type` | CharField | Nullable — entity the process operated on |
| `entity_id` | UUIDField | Nullable |
| `status` | Enum | Started, Completed, Failed |
| `started_at` | DateTimeField | |
| `completed_at` | DateTimeField | Nullable |
| `error_message` | TextField | Nullable |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

### `NavigationAudit`
Records user page navigation per session. ERD: Navigation_Audits (FK Session).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `session_id` | UUID | Plain UUID — **not a FK**. Purged together with `SessionLog` in the 18-month rolling retention task. The plain UUID avoids FK conflict during the purge sweep. |
| `user_id` | UUID FK → User | |
| `path` | CharField | URL path navigated to |
| `previous_path` | CharField | Nullable |
| `navigated_at` | DateTimeField | |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |

---


# PART 4 — FLEET MANAGEMENT ADD-ON (Plus+ Add-On)

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

# PART 6 — ERD RECONCILIATION NOTES

## 6.1 ERD Entities Not Currently Specified in This Document

The following entities appear in the source ERD PDFs but are **not included** in this Data Models specification. They are either deferred Enterprise features or were intentionally replaced by other patterns during V6 development. They are listed here so developers consulting the ERDs understand they are **out of current implementation scope**.

| ERD Entity | ERD Source | Status | Notes |
|---|---|---|---|
| `Customer Triggers` (FK Trigger, FK Customer) | Base System V12 | **Not in scope** | Per-customer automation trigger overrides. Deferred until the Communication/Automation module is fully specified for Enterprise. |
| `Customer Point Base` (FK Customer) | Base System V12 | **Not in scope** | Customer scoring/loyalty points. No current specification references this entity. Deferred. |
| `Customer FK Zone` (on Customers entity) | Base System V12 | **Not in scope** | ERD shows a `zone_id` FK on Customer. This document defines `TerritoryZone` and `EmployeeZone` (Enterprise) but does not assign zones to Customers. If Customer-to-Zone mapping is needed in the future, a `CustomerZone` junction or FK should be added here. |

## 6.2 ERD Relationship Differences (Intentional Divergences)

| Topic | ERD (Base System V12) | This Document (V6) | Rationale |
|---|---|---|---|
| **Payments** | Two separate entity boxes: customer payments (FK Invoice) and vendor payments (FK Purchasing/Vendor) | Single `Payment` model with `payment_type` discriminator (`CustomerPayment` / `VendorPayment`) | Unified table simplifies ledger integration and avoids duplicate schema. |
| **Asset nesting** | Shows both a self-FK (`FK Asset`) on `Assets` **and** a separate `Sub Assets (Assets)` junction | `SubAsset` junction only — replaces the former `parent_asset_id` self-FK on `Asset` | Junction is more flexible for multi-level hierarchies and avoids nullable self-FK complexity. Top-Down V4 mandate #4 updated to match. |

---

*End of ServizDesk Data Models V6*
