# ServizmaDesk SDTA Backend — Development Gap Analysis
**Date:** March 11, 2026
**Scope:** SDTA backend only — excludes UI, API (external), and SDP
**Classification:** Internal — Working Draft

---

## Purpose

This document identifies every gap, contradiction, ambiguity, and missing specification across the current ServizmaDesk document suite that could stop, slow down, or raise questions during SDTA backend development. Items are organized by severity.

**Documents Reviewed:**
- ServizmaDesk Data Models V3
- ServizmaDesk SDTA Data Models V1
- ServizmaDesk Technical Architecture V2
- ServizmaDesk Database Specification V1
- ServizmaDesk Internal API Specification V1
- ServizmaDesk Lite MVP V4 Specification
- ServizmaDesk Top-Down Specifications V1
- ServizmaDesk Product Tier Map V2
- ServizmaDesk Pricing & Billing Specification V2

---

# CATEGORY 1 — DATA MODEL CONTRADICTIONS

These are conflicts between documents that must be resolved before a developer can write the Django model. Each one will result in a "which document is correct?" question that stops work.

---

### 1.1 User Model Is Missing Critical Fields

**Affected Documents:** Data Models V2 (User table) vs. Lite MVP V4 (Section 18.3) vs. Internal API Spec (Section 4.4)

The Data Models V2 `User` table defines: `id`, `tenant_id`, `email`, `password`, `first_name`, `last_name`, `employee_number`, `role`, `status`, `phone`, `created_at`, `updated_at`.

The Lite MVP V4 (Section 18.3) defines additional Employee fields that are **not present** in the Data Models V2 User table:

| Missing Field | Source | Impact |
|---|---|---|
| `hire_date` | Lite MVP 18.3 | Required for employment lifecycle |
| `termination_date` | Lite MVP 18.3, 18.8 | Required to free a seat — seats cannot be released without this |
| `personal_email` | Lite MVP 18.3 | Listed as a separate field from work email |
| `address`, `city`, `state`, `zip` | Lite MVP 18.3 | Employee physical address fields |
| `phone_2` | Lite MVP 18.3 | Second phone number |
| `notes` | Lite MVP 18.3 | Internal admin-only notes |
| `created_by`, `updated_by` | Lite MVP 18.3 | Audit trail fields |
| `failed_login_count` | Internal API Spec 4.4 (step 3: "Clear `failed_login_count` → 0") | Required for login lockout enforcement |
| `is_locked` or equivalent | Lite MVP 4.3 (lockout after 5 failures) | No mechanism to flag an account as locked |
| `force_password_change` | Lite MVP 4.4 (password reset flow) | Required for "Force password change on next login" |

**Decision Required:** Data Models V2 must be updated to include all fields the backend needs to implement authentication, lockout, seat management, and employee lifecycle.

---

### 1.2 Employee Status Enum Mismatch

**Affected Documents:** Data Models V2 vs. Lite MVP V4

- **Data Models V2** defines User `status` as: `Active`, `Inactive`
- **Lite MVP V4** (Section 18.4) defines Employee status as: `Active`, `On Leave`, `Inactive`, `Terminated`

The Lite MVP depends on all four statuses for seat counting logic (Active + On Leave + Inactive count toward the 10-seat limit; Terminated does not). The Data Models V2 enum cannot support this.

**Decision Required:** Which enum is authoritative? The Lite MVP needs all four values.

---

### 1.3 Asset vs. Service Item — Name and Prefix Conflict

**Affected Documents:** Data Models V2 vs. Lite MVP V4

- **Data Models V2** calls the entity `Asset` with auto-generated number prefix `A` (e.g., `A26-0001`)
- **Lite MVP V4** (Section 5.4) calls the entity "Service Item" with prefix `S` (e.g., `S26-0001`)
- **Top-Down Spec** (Section 1.2) defines the entity as `Asset`

The database table name, the record number prefix, and the `SequenceTracker` entity_type string all depend on which name and prefix are canonical.

**Decision Required:** Is the table named `Asset` with prefix `A`, or `ServiceItem` with prefix `S`? The Lite MVP V4 and Data Models V2 must align.

---

### 1.4 Deletion Rules — Line Items: Block vs. Cascade

**Affected Documents:** Lite MVP V4 (Section 6.2) vs. Data Models V2 (Section 5.3) vs. Database Specification V1 (Section 6.6)

This is a direct contradiction:

- **Lite MVP V4** (Section 6.2): Quotes, Work Orders, and Invoices are **blocked from deletion** when they have linked line items. "The line items must be removed first."
- **Data Models V2** (Section 5.3): Line items (QuoteLine, WorkOrderLine, InvoiceLine) **cascade-delete** with their parent. Block conditions for these entities are: Work Order blocked by Invoices/Payments; Quote blocked by conversion to Invoice; Invoice blocked by Payments.
- **Database Specification V1** (Section 6.6): `work_order_line → work_order` = CASCADE. `quote_line → quote` = CASCADE. `invoice_line → invoice` = CASCADE.

These cannot both be true. If lines CASCADE, they auto-delete with the parent and don't block. If lines block, the FK behavior must be RESTRICT, not CASCADE.

**Decision Required:** Do line items block parent deletion (Lite MVP), or cascade-delete with the parent (Data Models V2 / Database Spec)?

**Resolution:** [ServizmaDesk Data Models V3](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Data_Models_V3.md) Section 5 explicitly defines the rule: top-level entities (Quote, Work Order, Invoice) are **blocked from deletion** if non-note/non-document child records exist. Delete policy is now standardized and the contradiction is resolved.

---

### 1.5 Note Table Missing `type` Field

**Affected Documents:** Data Models V2 vs. Lite MVP V4

The Lite MVP V4 (Section 12.11) defines Note Types: Internal Note, Call, Email, Site Visit, Customer Comment, Reminder.

The Data Models V2 `Note` table contains only: `id`, `tenant_id`, `body`, `created_by`, `created_at`, and the exclusive arc FK columns. **There is no `type` or `note_type` field.**

**Decision Required:** Add a `note_type` enum field to the Note model. Confirm the enum values match the Lite MVP list.

**Resolution:** Added `note_type` enum field to the Note model in both `ServizmaDesk_Data_Models_V3.md` and `ServizmaDesk_SDTA_Data_Models_V1.md` (Section 2.6). Enum values match the Lite MVP list.

---

### 1.6 Social Table — Missing Customer FK [RESOLVED]

**Resolution:** Added `customer_id` and `vendor_id` FK fields to the `Social` model in [ServizmaDesk Data Models V3](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Data_Models_V3.md). This aligns the Social table with Phone and Address, supporting business-level social profiles.

---

### 1.7 TenantState Missing `add_ons` Field [RESOLVED]

**Affected Documents:** Data Models V2 vs. Internal API Specification V1

The Internal API Spec sends `add_ons` as part of `POST /update-limits/` (Section 4.3) and `POST /sync-tenant-state/` (Section 4.5).

The Data Models V2 `TenantState` table had no `add_ons` field.

**Resolution:** Instead of a single `JSONField` on `TenantState`, a dedicated relational table **`TenantAddOn`** has been added to the Data Models (V1 and V3). This allows for better scalability, reporting, and integrity as the number of available add-ons grows. The Internal API Specification V1 has been updated to reflect the structured payload for these add-ons.

---

### 1.8 Invoice — No Field for Stripe Payment Link URL

**Affected Documents:** Lite MVP V4 (Section 7.4) vs. Data Models V2

The Lite MVP V4 states: "Only one active Payment Link per Invoice is tracked in SDTA at a time — generating a new link replaces the previous link reference."

The Data Models V2 `Invoice` table has no `stripe_payment_link_url` or `stripe_payment_link_id` field. The backend has no place to store the generated link.

**Decision Required:** Add `stripe_payment_link_id` and `stripe_payment_link_url` to the Invoice model.

**Resolution:** Added as nullable fields to the `Invoice` model in [ServizmaDesk Data Models V3](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Data_Models_V3.md). This satisfies Gap 1.8.

---

### 1.9 Product Type Enum Inconsistency [RESOLVED]

**Resolution:** Standardized the `item_type` enum as **`Part, Service, Consumable, Kit`** across all specifications (**[ServizmaDesk Data Models V3](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Data_Models_V3.md)** and **[Lite MVP V4](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Lite_MVP_V4_Specification.md)**). This preserves the Lite-tier requirement (Part/Service) while providing the structural depth for higher tiers (Consumable/Kit).

---

### 1.10 TenantPreference Numbering Fields vs. SequenceTracker Overlap [RESOLVED]

**Affected Documents:** Data Models V3, Technical Architecture V2

`TenantPreference` contains `*_prefix` and `*_start_number` fields for every entity type. Separately, `SequenceTracker` manages the actual running counter per entity type.

**Resolution:** The coordination contract between these tables is defined in [ServizmaDesk Technical Architecture V2](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Technical_Architecture_V2.md) Section 9.2. It establishes a **"Forward-Only" constraint** on user-configured start numbers, ensuring that users can only increase the sequence to avoid duplicates. The system displays the "Next Number" to the user based on the current tracker state.

---

# CATEGORY 2 — MISSING BUSINESS LOGIC SPECIFICATIONS

These are behaviors the backend must implement but which are not specified in enough detail. A developer will have to stop and ask "how should this work?" for each one.

---

### 2.1 Status Transition Rules (State Machine)

**Affected Entities:** Quote, Work Order, Invoice

The Lite MVP defines status flows:
- **Quote:** Draft → Sent → Accepted → Rejected → Expired → Converted
- **Work Order:** Draft → Scheduled → In Progress → On Hold → Completed → Closed / Cancelled
- **Invoice:** Draft → Issued → Partially Paid → Paid → Overdue → Void → Written Off

But there is no state machine specification defining which transitions are **valid**. Can a Work Order go from Completed back to In Progress? Can a Voided invoice go to Draft? The deletion rules (Section 6.4) say terminal statuses must be "reopened" before deletion — but which target status is permitted for each reopen action?

**What's Needed:** A formal transition matrix per entity. For each status, list which outbound transitions are allowed and which are blocked.

**Resolution:** See [ServizmaDesk System Status Specification V1](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_System_Status_Specification_V1.md) for full state machine and audit log rules.

---

### 2.2 Quote → Work Order Conversion Logic [RESOLVED]

**Resolution:** See Section 9.3 in [ServizmaDesk Technical Architecture V2](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Technical_Architecture_V2.md) for the conversion field mapping, cloning rules, and status transition logic.

---

### 2.3 Quote → Invoice Conversion Logic [RESOLVED]

**Resolution:** See Section 9.3 in [ServizmaDesk Technical Architecture V2](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Technical_Architecture_V2.md) for the field mapping and line item cloning rules.

---

### 2.4 Work Order → Invoice Conversion Logic [RESOLVED]

**Resolution:** See Section 9.3 in [ServizmaDesk Technical Architecture V2](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Technical_Architecture_V2.md) for the field mapping and labor-rolling logic.

---

### 2.5 Invoice Calculation Logic — Order of Operations

The Invoice model has: line items (quantity × unit_price), `discount_type` + `discount_value`, `surcharge_label` + `surcharge_value`, `tax_rate`, and `deposit_applied`.

The calculation order is unspecified:
1. Subtotal = sum of (line quantity × line unit_price)?
2. Is the discount applied before or after tax?
3. Is the surcharge applied before or after tax?
4. Is the surcharge taxable?
5. Is tax calculated per-line (respecting each line's `taxable` flag) or on the post-discount subtotal?
6. Where is the total stored? There's no `total` or `subtotal` field on the Invoice model.
7. Where is the `amount_due` (total minus payments) tracked? Is it calculated on the fly or stored?

**What's Needed:** A formula specification: Subtotal → Discount → Taxable Subtotal → Tax → Surcharge → Grand Total → Minus Deposit → Amount Due. Each step defined explicitly.

**Resolution:** See [ServizmaDesk Invoice Calculation Specification V1](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Invoice_Calculation_Specification_V1.md) for the detailed math, order of operations, and stored field requirements.

---

### 2.6 LedgerEntry Creation Triggers [RESOLVED]

**Resolution:** See Section 9.4 in [ServizmaDesk Technical Architecture V2](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Technical_Architecture_V2.md) for the Unified Ledger (AR/AP) trigger logic, immutability rules, and balance calculation.

---

### 2.7 Storage Tracking — Cascade Delete Handling [RESOLVED]

**Resolution:** Documents are strictly governed by a **`RESTRICT`** constraint (see [Database Specification V1](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Database_Specification_V1.md)). A parent entity (Customer, Asset, etc.) cannot be deleted if associated Documents exist. This prevents database-level cascade deletes that would bypass Django's `post_delete` signals. 

To ensure absolute integrity against manual SQL deletions, a **PostgreSQL Trigger** is implemented on the `document` table to automatically update `StorageTracker.total_bytes_used`.

---

### 2.8 Dashboard Counter Definitions [RESOLVED]

**Resolution:** See **[Dashboard Counter Specification](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Dashboard_Counter_Specification_V1.md)** for the exact query filters and logic for all five dashboard widgets.

---

### 2.9 Onboarding Checklist Completion Detection [RESOLVED]

**Resolution:** See **[Onboarding Triggers Specification](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Onboarding_Triggers_Specification_V1.md)** for the specific database conditions (TenantPreference fields, record existence) that trigger checklist completion.

---

### 2.10 CSV Export Column Specification [RESOLVED]

**Resolution:** Standardized via the **[CSV Export Specification (Top-Down)](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_CSV_Export_Specification_V1.md)**. These exports are designed as a "Full Data Dump" for administrators, covering 16+ entities from the Enterprise ERD to ensure absolute data portability.

---

# CATEGORY 3 — MISSING TECHNICAL SPECIFICATIONS

These are implementation-level decisions that are not covered by any document. Each one will force a developer to make an architectural choice without guidance.

---

### 3.1 Django App Structure [RESOLVED]

**Resolution:** The project follows a **Top-Down Domain-Driven Architecture**. The structure is split into twelve specialized applications to support Enterprise-scale complexity from the start.

**Domain Map (Defined in [Technical Architecture V2 Section 10](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Technical_Architecture_V2.md)):**
- `users/`: Identity, Auth, RBAC.
- `crm/`: Customer/Person/Contact Triad.
- `inventory/`: Items, Serial/Lot tracking.
- `warehouse/`: Warehouses and subdivision Locations (Bins/Areas).
- `procurement/`: Vendors, POs, and **Receiving**.
- `service/`: Quotes, Work Orders, Invoices, Unified Ledger (AR).
- `maintenance/`: Assets, PM Plans, and Warranties.
- `tasks/`: Tasks, Todos, and Time Entry.
- `scheduling/`: Dispatch and Availability.
- `pricing/`: Pricebooks and Contract-specific rates.
- `automation/`: Workflow logic engine.
- `infrastructure/`: Logging, Numbering, and Storage tracking.

---

### 3.2 Tenant Model Manager Specification [RESOLVED]

**Resolution:** See **[Multi-Tenancy Technical Specification](file:///Users/ronhoagland/.gemini/antigravity/brain/63427f0e-2cdd-4ddf-91be-5443c157608b/multi_tenancy_spec_v1.md)** for the complete architecture of the `TenantManager`, `TenantModel`, and `asgiref.local`-based context Store.

---

### 3.3 Celery Task Inventory and Schedule [RESOLVED]

**Resolution:** See **[Background Task Specification](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Background_Tasks_Specification_V1.md)** for the complete inventory, tenant-local schedules, and the notification strategy for system failures.

---

### 3.4 Stripe Webhook Tenant Resolution [RESOLVED]

**Resolution:** See **[Stripe Webhook Technical Specification](file:///Users/ronhoagland/.gemini/antigravity/brain/63427f0e-2cdd-4ddf-91be-5443c157608b/stripe_webhook_spec_v1.md)** for the implementation of multi-tenant lookup via `Stripe-Account` headers, UUID metadata matching for perfect record identification, and the 12-month log retention policy.

---

### 3.5 File Upload Constraints [RESOLVED]

**Resolution:** Defined in the **[File Upload Specification (Top-Down)](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_File_Upload_Specification_V1.md)**. This establishes a 100MB standard size limit, broad professional mime-type support, and mandatory quarantine/scanning procedures for all enterprise data.

---

### 3.6 Search and Filtering Implementation [RESOLVED]

**Resolution:** Standardized via the **[Universal Query Specification](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Universal_Query_Specification_V1.md)**. This defines a unified JSON-based API contract for Global Search, dynamic Filtering (with logic operators), and Multi-Level Sorting across all system entities.

---

### 3.7 List View Pagination [RESOLVED]

**Resolution:** Standardized via the **[Universal Query Specification](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Universal_Query_Specification_V1.md)**. ServizmaDesk mandates **Cursor-based Pagination** for all list views to ensure enterprise-grade performance, with a default page size of 25 and a maximum of 100.

---

### 3.8 Permission Enforcement Pattern [RESOLVED]

**Resolution:** See **[Permission Enforcement Specification](file:///Users/ronhoagland/.gemini/antigravity/brain/63427f0e-2cdd-4ddf-91be-5443c157608b/permission_spec_v1.md)**. This architecture uses a "Double Guard" (Tier Lock + CRUD Matrix), implements an "Additive Union" for multiple roles per user, and mandates a "Resource Isolation Rule" to prevent cross-module permission bleed.

---

### 3.9 Tenant Provisioning Seed Data [RESOLVED]

**Resolution:** See **[Tenant Provisioning Seed Data Specification](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Tenant_Provisioning_Seed_Data_Specification_V1.md)** for the exact records (Role, Preferences, SequenceTrackers) initialized during provisioning. Includes the use of 4-digit thousands placeholders (e.g., `0001`) for all default entity counters.

---

### 3.10 Background Worker Environment Variables [RESOLVED]

**Resolution:** Updated the **[Environment Variables Reference](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Database_Specification_V1.md#L542)** to include `SDTA_WORKER_DB_USER`, `SDTA_WORKER_DB_PASSWORD`, and other system-critical keys (Stripe, Celery, Django).

---

### 3.11 Lite MVP References V1 Documents [RESOLVED]

**Resolution:** Updated **[ServizmaDesk Lite MVP V4 Specification](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Lite_MVP_V4_Specification.md#L74)** to point to the current V2/V3 versions of the Technical Architecture and Platform Specification documents.

---

# CATEGORY 4 — ITEMS THAT WON'T BLOCK BUT SHOULD BE DECIDED BEFORE DEVELOPMENT STARTS

These are decisions that can be made quickly but will result in inconsistent implementations if left to individual developer judgment.

---

### 4.1 `updated_at` Field — Auto vs. Manual [RESOLVED]

**Resolution:** Mandatory use of Django's `auto_now=True` for all `updated_on` fields to ensure reliable auditing (as per Data Models Mandate 8).

### 4.2 Soft Delete vs. Hard Delete — Contacts [RESOLVED]

**Resolution:** Following the Top-Down Design and ignoring legacy Lite spec constraints, **Soft Delete** is applied to Contacts (via `status = Left`). The human `Person` record is immutable and never deleted.

### 4.3 Quote Status — "Converted" Added [RESOLVED]

**Resolution:** Quote status enum standardized to include `Converted` as the terminal state after successful conversion to a Work Order or Invoice.

### 4.4 Work Order Status — Standardized [RESOLVED]

**Resolution:** Work Order status enum expanded and standardized to: `Draft, Scheduled, In Progress, On Hold, Completed, Closed, Cancelled`.

### 4.5 LedgerEntry Exclusive Arc Pattern [RESOLVED]

**Resolution:** The `LedgerEntry` model has been updated to use an **Exclusive Arc** (Customer, Vendor, or Employee) with nullable FKs and a database-level `CHECK` constraint. This replaces the string-based `reference_type` pattern, ensuring PostgreSQL RLS compliance and referential integrity without using generic foreign keys.

### 4.6 `created_at` / `updated_at` — Timezone Handling [RESOLVED]

**Resolution:** All timestamps are strictly `TIMESTAMPTZ` stored in **UTC**. Conversion to tenant-local time happens only at the display/representation layer via `TenantPreference.timezone`.

### 4.7 BundleItem — Inclusion Verified [RESOLVED]

**Resolution:** Product bundles remain in-scope for the Top-Down build as they are essential for Enterprise and Plus tiers.

### 4.8 Checklist Template — Scope Verified [RESOLVED]

**Resolution:** Checklist Templates are definitively in scope for the foundational build as per Data Models V3 Section 1.5.

---

# SUMMARY — PRIORITIZED ACTION LIST

## Must Resolve Before Any Code Is Written (Blockers)

1. **[COMPLETE]** **1.1** — User model missing fields (lockout, hire/term dates, force password change)
2. **[COMPLETE]** **1.2** — Employee status enum (2 values vs. 4 values)
3. **[COMPLETE]** **1.3** — Asset vs. Service Item name/prefix
4. **[COMPLETE]** **1.4** — Line Item Deletion: block vs cascade (Final Alignment)
5. **[COMPLETE]** **2.1** — Status Transition Matrices for Quote, WO, Invoice (Final Alignment)
6. **[COMPLETE]** **2.5** — Invoice calculation order of operations
7. **[COMPLETE]** **1.8** — Invoice Stripe fields (Final Alignment)


## Must Resolve Before Feature Development Starts (Slowdowns)

8. **[COMPLETE]** **1.5** — Note type field missing
9. **[COMPLETE]** **1.7** — TenantState missing add_ons field
10. **[COMPLETE]** **1.10** — TenantPreference ↔ SequenceTracker interaction
11. **[COMPLETE]** **2.2–2.4** — Conversion logic (Quote→WO, Quote→Invoice, WO→Invoice)
12. **[COMPLETE]** **2.6** — LedgerEntry creation triggers
13. **[COMPLETE]** **2.7** — StorageTracker cascade delete handling
14. **[COMPLETE]** **3.1** — Django app structure
15. **[COMPLETE]** **3.2** — Tenant model manager specification
16. **[COMPLETE]** **3.4** — Stripe webhook tenant resolution
17. **[COMPLETE]** **3.8** — Permission enforcement pattern
18. **[COMPLETE]** **3.9** — Provisioning seed data specification
19. **[COMPLETE]** **1.6** — Social table missing customer_id

## Should Resolve Before Beta/QA (Questions That Will Arise)

19. **[COMPLETE]** **1.6** — Social table missing customer_id
20. **[COMPLETE]** **1.9** — Product type enum inconsistency
21. **[COMPLETE]** **2.8** — Dashboard counter query definitions
22. **[COMPLETE]** **2.9** — Onboarding checklist completion triggers
23. **[COMPLETE]** **2.10** — CSV export column specification
24. **[COMPLETE]** **3.3** — Celery task inventory and schedules
25. **[COMPLETE]** **3.5** — File upload constraints
26. **[COMPLETE]** **3.6** — Search/filter field specification
27. **[COMPLETE]** **3.7** — Pagination specification
28. **[COMPLETE]** **3.10** — Missing environment variables
29. **[COMPLETE]** **3.11** — Stale V1 document references in Lite MVP
30. **[COMPLETE]** **4.1–4.8** — Category 4 items (All Resolved)

---

*End of SDTA Backend Gap Analysis*
