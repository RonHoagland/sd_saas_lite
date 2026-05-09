# ServizmaDesk Technical Architecture
**Document Status:** Working Draft
**Document Version:** V2
**Classification:** Internal — Technical Dependency
**Last Updated:** March 2026

---

# 1. Executive Summary

This document defines the complete technical architecture, technology stack, infrastructure, and third-party integrations required to build and deploy the ServizmaDesk software suite. It serves as the foundational engineering blueprint for both the **ServizmaDesk Platform (SDP)** and the **ServizmaDesk Tenant App (SDTA)**.

All technical decisions listed here are aligned with and validated against the following specification documents:

- ServizmaDesk Product Tier Map V2
- ServizmaDesk Lite MVP V4 Specification
- ServizmaDesk Platform (SDP) Specification V2
- ServizmaDesk Pricing & Billing Specification V2
- ServizmaDesk SDTA Data Models V4

This document supersedes the open technical decisions listed in Section 10 of the Product Tier Map V2. Those decisions are now codified herein. This document also supersedes Technical Architecture V1.

---

# 2. Application Architecture Overview

The ServizmaDesk ecosystem consists of two distinct Django applications deployed on shared infrastructure but maintaining completely isolated databases and codebases.

## 2.1 ServizmaDesk Platform (SDP)

SDP is the central control system and back-office for the entire ServizmaDesk product family. It is not a customer-facing product; it is an internal operations platform with a limited self-service surface for signup, billing management, and account recovery.

SDP serves five roles:

- **Gatekeeper** — no tenant account exists in any ServizmaDesk application without SDP provisioning it first
- **Single Source of Truth** — authoritative record for every customer account, plan status, seat counts, storage limits, and security credentials
- **Billing System** — all customer charges flow through SDP via the ServizmaDesk Stripe account
- **Security Authority** — Administrator security credentials (PIN and security questions) are stored exclusively in SDP and never replicated to SDTA
- **Staff Operations Hub** — all account management actions performed by ServizmaDesk staff

SDP runs as two functional surfaces within a single Django application:

- **Customer-facing surface** — self-service signup, billing portal, account management, Administrator account recovery
- **Staff-facing back office** — ServizmaDesk staff tools for account management, support, and operations

## 2.2 ServizmaDesk Tenant App (SDTA)

SDTA is the customer-facing field service management application. It is the product that tenants use daily to manage their service business — customers, assets, quotes, work orders, invoices, and payments.

SDTA is a multi-tenant application. All tenants share the same database schema and application codebase, with data isolation enforced at three distinct layers (see Section 5). SDTA contains three completely distinct UI parts — one for Lite, one for Plus, and one for Pro — routing users to the UI corresponding to their active plan.

## 2.3 Application Boundary Rules

- SDP and SDTA maintain completely separate PostgreSQL databases on the same database server instance
- Neither application may write to the other's database under any circumstances
- All inter-application communication occurs exclusively via the Internal REST API (see Section 7)
- Direct database reads across application boundaries are strictly prohibited

---

# 3. Core Technology Stack

## 3.1 Backend Framework

| Component | Selection |
|-----------|-----------|
| Language | Python 3.12+ |
| Framework | Django 5.x |
| Application Philosophy | Fat Models, Thin Views — business logic resides in the model layer or dedicated service classes, never directly in views |
| Password Hashing | bcrypt or Argon2 (Django's PBKDF2 default is acceptable minimum) — plaintext storage is strictly prohibited across SDP and SDTA |

## 3.2 Frontend Stack

| Component | Selection |
|-----------|-----------|
| Rendering Architecture | Server-Side Rendered (SSR) HTML via Django Templates |
| Dynamic Interactions | HTMX v2.x — Alpine.js and Hyperscript are explicitly ruled out to keep the frontend bundle minimal and strictly driven by Django templates |
| Styling Engine | Tailwind CSS (via Tailwind CLI/PostCSS) — vanilla CSS is not to be used as a replacement; permitted only for extreme edge cases |
| Icons | SVG icons (Heroicons or equivalent SVG icon library) |
| PDF Output (Lite) | CSS Print Media Queries — developers must write robust `@media print` CSS rules so that browser-printed invoices and quotes produce clean, stripped-down 8.5x11 output without UI chrome, navigation, or buttons |
| PDF Generation (Plus/Pro) | WeasyPrint (Python library) — the designated server-side PDF engine when automated PDF generation is introduced in Plus/Pro tiers; the codebase must use WeasyPrint exclusively for this purpose |

## 3.3 Database Layer

| Component | Selection |
|-----------|-----------|
| Database Engine | PostgreSQL 16+ |
| Primary Keys | UUIDv4 is mandatory for all primary and foreign keys globally — auto-incrementing integers are strictly prohibited to support future offline-mobile syncing |
| Tenant Isolation Field | `tenant_id` (UUID) — non-nullable on every tenant-scoped table in SDTA |
| Row-Level Security | PostgreSQL RLS is enabled on all SDTA tables as the final enforcement layer |
| ORM | Django ORM with a custom model manager that automatically injects `tenant_id` scoping on all querysets |
| SQLite Usage | Strictly prohibited in all environments including local development — SQLite does not support PostgreSQL RLS and breaks the required isolation architecture |
| Generic Foreign Keys (GFKs) | Prohibited — Django's content-types framework is not used; RLS enforcement requires explicit foreign keys |

---

# 4. Infrastructure & Hosting

## 4.1 Cloud Provider & Compute

| Component | Selection |
|-----------|-----------|
| Cloud Provider | DigitalOcean (recommended for bootstrapped scaling; migration to AWS deferred until scale warrants it) |
| Compute | DigitalOcean Droplets (Ubuntu 22.04 LTS+) or DigitalOcean App Platform |
| Web Server | Nginx — acts as reverse proxy and static file server |
| Application Server (WSGI) | Gunicorn — WSGI HTTP server serving the Django application |
| Redis | Managed Redis instance on DigitalOcean (preferred) or a dedicated standard Droplet — running Redis on the same Droplet as the web server is prohibited |
| Domains | ServizmaDesk.com (primary), Servizma.com (redirects to ServizmaDesk.com) |

## 4.2 Environment Strategy

Three environments are required and must be maintained concurrently:

| Environment | Purpose and Configuration |
|-------------|--------------------------|
| Local Development | Docker/Docker Compose workflow spinning up Django, PostgreSQL 16+, and Redis together. SQLite is banned. Stripe Test Mode. Local filesystem for media storage (`MEDIA_ROOT` via `FileSystemStorage`) to avoid object storage friction and unnecessary API costs during development. Both SDP and SDTA run locally. |
| Staging | Dedicated exact replica of production architecture on a separate subdomain (e.g., `staging.servizmadesk.com`). Connected to Stripe Test Mode for all pre-deployment validation. Both SDP and SDTA must maintain mirrored staging instances. |
| Production | Full production environment. Stripe Live Mode. DigitalOcean Spaces for object storage. Managed Redis. Fully hardened configuration. |

## 4.3 Configuration Management

All secrets and environment-specific configuration must be injected as environment variables. The `python-decouple` library (or equivalent) must be used for all settings. Hardcoded secrets in `settings.py` are strictly prohibited in all environments.

## 4.4 Infrastructure Scaling Plan

| Stage | Tenant Volume | Estimated Monthly Infrastructure Cost |
|-------|---------------|---------------------------------------|
| Pre-Launch | 0 (dev + staging) | ~$100/month |
| Stage 2 | 10–30 tenants | ~$250–$350/month |
| Stage 3 | 50+ tenants | ~$500–$800/month |
| Stage 4 | 100+ tenants | ~$1,000–$1,500/month |

---

# 5. Multi-Tenancy Architecture (SDTA)

ServizmaDesk uses a **Shared Database, Shared Schema** multi-tenant architecture. All tenants share the same tables. Data isolation is the responsibility of the application and database layers, not schema separation.

## 5.1 Three-Layer Isolation Model

Tenant isolation is enforced at three distinct and independent layers. All three layers must be present and functioning simultaneously. No single layer is sufficient on its own.

| Layer | Mechanism | Description |
|-------|-----------|-------------|
| Layer 1 | Database Field Constraint | Every table in SDTA contains a non-nullable `tenant_id` (UUID) foreign key. This is an absolute architectural mandate — no table may be created without this field. |
| Layer 2 | Django Application Middleware | A custom Django middleware extracts the `tenant_id` from the authenticated user's session and automatically scopes all ORM queries to that specific tenant using a custom model manager. For implementation details, see **[Multi-Tenancy Technical Specification](file:///Users/ronhoagland/.gemini/antigravity/brain/63427f0e-2cdd-4ddf-91be-5443c157608b/multi_tenancy_spec_v1.md)**. |
| Layer 3 | PostgreSQL Row-Level Security (RLS) | RLS is enabled on all tables in the PostgreSQL database. This is the final failsafe. Even if a developer accidentally writes a raw SQL query that bypasses the Django ORM, the database user itself is scoped to the current tenant. It is physically impossible for tenant A to query tenant B's data. |

## 5.2 Tier-Gating Implementation

Feature access is gated at two layers to prevent unauthorized access to higher-tier capabilities:

- **Backend Enforcement (Primary Shield):** A custom `@tier_required('plus')` decorator is applied to Django view functions. If a Lite-tier user attempts to access a Plus view via direct URL manipulation, the system raises a `TierUpgradeRequired` exception. This is the enforcement layer that cannot be bypassed.
- **Frontend UI (Secondary Shield):** Django Template Conditionals (`{% if request.tenant.tier == 'plus' %}`) are used to conditionally render, gray out, or hide UI elements. This guides user behavior and prevents exposure of broken application states, but is not the primary security mechanism.

The SDTA database schema is designed upfront to contain all tables required for all tiers. Tables for Plus and Pro features (such as Locations, Purchase Orders, Leads, and Opportunities) exist in the database from day one, even though the Lite UI does not expose them. Upgrading a tenant changes which UI part is served and which controllers permit writes — it does not require a database migration.

## 5.3 Distinct UI Parts Per Tier

There are three completely distinct UI parts built for SDTA — one for Lite, one for Plus, and one for Pro. The application routes the user to the UI part corresponding to their active plan. Backend controllers explicitly reject any write request to a higher-tier feature if the tenant's current plan does not allow it.

## 5.4 Tenant State Synchronization

SDTA maintains local `TenantState` and `TenantAddOn` tables that cache the tenant's current tier, seat limit, account status, and active features/add-ons. This local cache eliminates the need to call the SDP API on every page load. The cache is updated via webhooks or background workers when SDP changes a tenant's account state. All enforcement decisions in SDTA (tier-gating, seat limits, storage limits, add-on feature gating) are made against this local cache.

---

# 6. Third-Party Integrations & Services

## 6.1 Payment Processing — Stripe

Stripe is the exclusive payment processing platform for ServizmaDesk. Two distinct Stripe integration patterns are used depending on the payment context.

| Context | Integration Type | Purpose |
|---------|-----------------|---------|
| ServizmaDesk Corporate Billing (SDP) | Stripe Billing + Stripe Checkout | Used to charge tenants their monthly or annual subscription fees, seat additions, and storage add-ons. Stripe Checkout is used for all card collection — custom card entry forms that post card data to SDP servers are strictly prohibited. Maintains SAQ A PCI compliance. |
| Tenant Payment Processing (SDTA) | Stripe Connect (Standard Integration) | Tenants securely link their own Stripe accounts via OAuth in Plus and above. SDTA generates Stripe Payment Links via the Stripe API for tenant invoices. No embedded card forms are used in Lite. |

- **SDK:** Official Stripe Python SDK (`stripe>=11.0.0`)
- **PCI Compliance:** ServizmaDesk operates as an SAQ A merchant. Raw card data never touches ServizmaDesk servers at any layer. SDP stores only Stripe-provided tokenized references: Customer ID, Subscription ID, Payment Method ID, last 4 digits, card brand, expiry month/year.
- **What is Never Stored:** Full card number (PAN), CVV/CVC, raw card data of any kind, magnetic stripe data.
- **Webhook Security:** All incoming Stripe webhooks must verify the cryptographic signature using `STRIPE_WEBHOOK_SECRET` before parsing the payload. All webhook endpoints must be fully idempotent — safe to process the same event twice.
- **Proration:** Stripe manages all proration calculations for mid-cycle seat changes and storage add-on changes. ServizmaDesk does not perform independent proration calculations.

## 6.2 Transactional Email — Postmark

Postmark is the exclusive transactional email provider for all ServizmaDesk system-generated emails.

| Scope | Details |
|-------|---------|
| Managed Emails | Welcome email on account creation; password reset links for employees; provisioning success/failure notifications; payment failure alerts; account suspension warnings; data deletion warnings (14-day pre-deletion notice); critical system alerts to ServizmaDesk staff |
| Lite Tier Scope | SDTA does not send emails on behalf of tenants in the Lite tier. Tenant-to-customer communication in Lite is handled by tenants from their own email clients. |
| Plus/Pro/Enterprise Tenant Email | Point-based system. 1 point = 1 outbound email. Default mode sends from ServizmaDesk's platform domain via Postmark. Custom Domain authentication (emails from tenant's own domain via DNS-verified Postmark) is a paid add-on on Pro and Enterprise. BYOS (Bring Your Own SMTP) is not supported. See Pricing & Billing Specification V2 Section 10A and 11.4, and Email Specification V1. |
| Delivery Logging | All platform emails are tracked in the `EmailDeliveryLog` table capturing delivery status and hard bounces. |

## 6.3 SMS / Telephony — Deferred

SMS messaging is explicitly out of scope for the Lite tier.

| Item | Status |
|------|--------|
| Lite Tier SMS | Out of scope — not implemented in Lite. |
| Plus/Pro SMS | Point-based system. 1 point = 1 outbound SMS segment. Plus includes 350 points/month; Pro includes 750 points/month; Lite includes 100 points/month (manual only). Overage charged at $0.035/point. Point packages available post-launch after usage patterns are confirmed. See Pricing & Billing Specification V2 Section 10. |
| Provider Selection | Twilio (A2P 10DLC). ServizmaDesk registers as the ISV brand; each tenant registered as a campaign under the ServizmaDesk A2P umbrella. |
| International SMS | Pricing and point multipliers deferred to Plus specification. |

## 6.4 File & Attachment Storage — DigitalOcean Spaces

| Item | Details |
|------|---------|
| Production Provider | DigitalOcean Spaces (S3-compatible object storage). AWS S3 is an acceptable alternative if migration is warranted. |
| Django Integration | `django-storages` with the `boto3` backend. All `FileField` and `ImageField` uploads are routed automatically to the object storage bucket in production. |
| Local Development | Standard local filesystem (`MEDIA_ROOT` via `FileSystemStorage`) to avoid friction and unnecessary API costs during development. |
| Prohibited Pattern | Storing tenant attachments on the production server's local filesystem is strictly prohibited. It prevents horizontal scaling and risks filling the server disk. |
| Storage Tracking | A `StorageTracker` table maintains a running tally of total bytes consumed per tenant. This eliminates the need to query object storage on every page load to enforce tier storage caps. |
| Lite Storage Cap | 3 GB included. Warnings at 70% and 85% usage. Uploads blocked at 100%. Add-ons: +5 GB ($10/month), +10 GB ($15/month). Maximum: 10 GB. |
| Plus Storage Cap | 10 GB included. Maximum 75 GB. Add-ons: +25 GB, +50 GB, +75 GB. |
| Pro Storage Cap | 25 GB included. Unlimited maximum. Add-ons: +50 GB, +75 GB, Unlimited ($100/month). |

## 6.5 Asynchronous Workers — Celery + Redis

Tasks that must not block the web response cycle are handled by Celery workers consuming from a Redis message broker.

| Component | Details |
|-----------|---------|
| Message Broker | Redis — Managed Redis instance on DigitalOcean in production. Running Redis on the same Droplet as the web server is prohibited. |
| Task Queue | Celery |
| Primary Use Cases | 60-day background data deletion worker after account cancellation; heavy CSV exports; Stripe webhook processing; storage usage reconciliation; TenantState cache synchronization between SDP and SDTA; scheduled data deletion warning emails (14-day pre-deletion) |

---

# 7. SDP / SDTA Internal Communication

Communication between SDP and SDTA occurs exclusively via an **Internal REST API**. Direct database reads across applications are strictly prohibited at all times.

## 7.1 API Architecture

SDP exposes a private, internal-only REST API accessible only over the private server network or localhost. SDTA authenticates its requests to this API using a secure Internal API Key (or JWT shared secret). No external traffic reaches this API.

| Direction | Method | Examples |
|-----------|--------|---------|
| SDTA → SDP | Internal REST API | Request current plan status; request seat limit; request storage allocation; notify SDP of new seat added; notify SDP of seat terminated; notify SDP of storage usage update |
| SDP → SDTA | Internal REST API | Provision new tenant; update account status (suspend, reactivate, cancel); push plan change notification; push storage limit change |

## 7.2 Provisioning Flow

New tenant provisioning is fully atomic. A successful signup results in a complete, fully initialized tenant account in both SDP and SDTA with no manual intervention required. If provisioning fails at any step, no partial records remain in SDP or SDTA and ServizmaDesk staff are alerted immediately.

The provisioning sequence follows a **verify-first, bill-second** model:

1. Customer completes Stripe Checkout (payment authorized but not yet captured)
2. SDP generates Tenant UUID
3. SDP calls SDTA Internal API to initialize the tenant (Tenant record, Administrator Employee record, default Preferences, required system lookup data)
4. On successful SDTA initialization, SDP captures the Stripe payment
5. Welcome email dispatched via Postmark
6. Customer redirected to SDTA login page

> **Rule:** A customer is never charged for a failed provisioning. If SDTA initialization fails, the Stripe payment authorization is released and the customer receives an error notification.

---

# 8. Security & Compliance

## 8.1 Authentication

| Item | Implementation |
|------|---------------|
| SDTA Authentication | Standard Django session-backed authentication. Username (work email) and password. |
| SDP Customer Authentication | Separate session from SDTA. Customers log into SDP with their billing email and SDP password. Logging into SDP does not log the customer into SDTA. |
| Password Hashing | bcrypt or Argon2 preferred (Django's PBKDF2 default is acceptable minimum). Plaintext passwords are strictly prohibited in all databases. |
| Password Rules | Minimum 8 characters. Must include uppercase, lowercase, number, and special character. |
| Session Timeout | Configurable by Administrator. Minimum 15 minutes, maximum 8 hours, default 30 minutes. On timeout, user is logged out and returned to the login page. |
| Failed Login Lockout | 5 consecutive failed attempts locks the employee account. Locked accounts require Administrator intervention (or SDP recovery for locked Administrators). |
| Administrator Recovery | Locked Administrator accounts are recovered through SDP using Security PIN and security questions established at signup. Billing verification available as fallback. All recovery actions logged in SDP. |
| Security Credentials | Administrator Security PIN and security question answers are stored exclusively in SDP. They are never transmitted to or stored in the SDTA database. |

## 8.2 PCI DSS Compliance

ServizmaDesk operates as an **SAQ A merchant** — the lowest and simplest PCI compliance tier. This is maintained by ensuring raw card data never touches ServizmaDesk servers at any point.

- All card collection uses Stripe Checkout (for ServizmaDesk billing) or Stripe Connect (for tenant payment processing in Plus/Pro)
- Custom card entry forms that post card data to ServizmaDesk servers are strictly prohibited and would immediately invalidate SAQ A status
- SDP stores only Stripe-provided tokenized references — never raw card data, PAN, CVV, or magnetic stripe data

## 8.3 Data Retention

| Data Type | Retention Rule |
|-----------|---------------|
| Active tenant data (SDTA) | Retained indefinitely while account is active |
| Cancelled/expired tenant data (SDTA) | 60-day grace period. Data accessible in read-only mode during grace period. After 60 days, Celery workers permanently hard-delete all data for that Tenant UUID. |
| SDP audit log | 36 months rolling |
| SDTA audit log | 18 months rolling |
| SDP account records (post-cancellation) | 36 months rolling |
| Stripe transaction records | Indefinite (managed by Stripe) |
| Staff login attempts (SDP) | 36 months rolling |
| Trial account data (unconverted) | Day 15: read-only mode. Day 45: flagged for cleanup (60-day grace begins). Day 105: permanent deletion. |

Soft-delete is generally prohibited unless explicitly specified by a status lifecycle. Records are hard-deleted unless blocked by relational integrity constraints (e.g., a Customer with attached Invoices cannot be deleted). Permanent deletion is irreversible — there is no backup or restore capability exposed in the SaaS product.

## 8.4 Stripe Webhook Security

- All incoming webhooks from Stripe must verify the cryptographic signature using `STRIPE_WEBHOOK_SECRET` before parsing the payload
- Webhook endpoints must be fully idempotent — processing the same Stripe event twice must produce no adverse effects
- Incoming event IDs are stored in the `WebhookLog` table to prevent duplicate payment processing

## 8.5 Audit Logging

Both SDP and SDTA maintain comprehensive audit logs. Audit events are immutable once written.

| System | Scope |
|--------|-------|
| SDTA `AuditEvent` table | Records who did what and when for all significant tenant-side actions: record creation, deletion, status changes, financial-impact actions (invoices issued/voided, payments applied). Event-level logging — not field-level diff logging. |
| SDP audit log | Records all staff actions, account management events, provisioning actions, recovery actions, and plan changes. |
| `SessionLog` (SDTA) | Tracks active authenticated sessions with login time, IP address, user-agent, and expiration. 18-month rolling retention. |

---

# 9. Development Practices & Standards

## 9.1 Architecture Patterns

- **Fat Models, Thin Views** — business logic lives in model methods or dedicated service classes, never in view functions
- **No Generic Foreign Keys (GFKs)** — use explicit foreign keys on all tables to maintain PostgreSQL RLS enforcement compatibility
- **Exclusive Arc Pattern for Notes and Documents** — a single `Note` table and single `Document` table each contain nullable foreign keys pointing to every possible parent entity (Customer, Asset, Quote, Work Order, Invoice, etc.). A database constraint ensures exactly one FK is populated per row.
- **Isolated Line Items** — Quotes, Work Orders, and Invoices each have their own dedicated line item table (`QuoteLine`, `WorkOrderLine`, `InvoiceLine`). No shared generic line item table.
- **Universal Deletion Policy (The "Notes Only" Rule)** — No top-level record can be deleted if related child records exist. This is enforced via database-level `RESTRICT` constraints on all children except **Notes**, which remain the only entity allowed to `CASCADE` delete with a parent.

## 9.2 Record Numbering

Human-readable record numbers (e.g., `Q26-0001` for quotes, `W26-0001` for work orders) are generated using a `SequenceTracker` table that manages tenant-scoped auto-incrementing counters. This guarantees collision-free, per-tenant sequential numbering without relying on database auto-increment sequences, which are not per-tenant.

#### 9.2.1 Coordination Contract (The "Forward-Only" Rule)

To ensure data integrity and prevent duplicate record numbers when users modify their numbering settings, the following contract governs the interaction between `TenantPreference` (User Settings) and `SequenceTracker` (System Counter):

1.  **Initial Seeding**: At tenant provisioning, `SequenceTracker` rows are initialized for all entity types. The `last_value` is set to `[start_number] - 1` (default start is 1, so internal counter begins at 0).
2.  **Number Generation Workflow**: When a new record is created:
    *   The system performs an atomic increment on the `SequenceTracker` for the corresponding `entity_type` and `tenant_id` (and `year` if annual reset applies).
    *   The `last_value` is retrieved from the tracker.
    *   The prefix is retrieved from `TenantPreference`.
    *   The final record number is formatted: `[Prefix][Year_Code]-[Atomic_Sequence]` (e.g., `W26-1025`).
    *   The resulting string is permanently saved to the record's number field.
3.  **User Updates (Forward-Only)**: Users may modify their `*_start_number` in `TenantPreference` at any time, but the update is subject to a **Forward-Only Constraint**:
    *   The new `start_number` must be **greater than** the current `SequenceTracker.last_value`.
    *   Attempting to set a `start_number` lower than or equal to the current counter must be rejected by the validation layer.
    *   Setting a higher `start_number` immediately updates the `SequenceTracker.last_value` to `[new_start_number] - 1`.
4.  **Visibility**: The "Next Number" to be used for each sequence is displayed to the user in the Preference section, derived from `SequenceTracker.last_value + 1`.
5.  **Immutability**: Once generated and saved, a record number can never be changed. Modifications to prefixes or start numbers in `TenantPreference` apply only to records created after the change.

## 9.3 Record Conversion Logic

The ServizmaDesk Lite MVP supports the transformation of records across the service lifecycle (Quote → Work Order → Invoice). To maintain historical integrity while allowing operational flexibility, the following rules apply:

### 9.3.1 Conversion Pattern: "Clone & Link"
1.  **Immutability of Source**: The source record (e.g., Quote) is never deleted. It is marked with a terminal status (e.g., `Converted`).
2.  **Deep Copy logic**: Line items are **cloned** (deep copy) from the source table to the target table. Once converted, the new line items can be modified (quantities adjusted, parts added) without affecting the original source record.
3.  **Backlink Traceability**: The newly created record MUST store the ID of its parent in the corresponding backlink field (e.g., `Invoice.work_order_id`, `WorkOrder.quote_id`).

### 9.3.2 Specific Mapping Rules

| Conversion Type | Field Mapping | Line Item Mapping | Post-Conversion Status Change |
| :--- | :--- | :--- | :--- |
| **Quote → Work Order** | Customer, Project, Contact, Assigned To | All QuoteLines → WorkOrderLines | Quote: `Converted` |
| **Quote → Invoice** | Customer, Project, Contact, Assigned To, Notes, Internal Notes, Tax Rate | All QuoteLines → InvoiceLines | Quote: `Converted` |
| **Work Order → Invoice** | Customer, Project, Assigned To, Internal Notes | All WorkOrderLines → InvoiceLines | Work Order: `Completed` or `Closed` |

### 9.3.3 Labor Rolling (Work Order → Invoice)
At the time of Work Order to Invoice conversion, the system provides an option to "Roll Labor to Invoice". If selected, the system iterates through all `TimeEntry` records for the Work Order and generates a new `InvoiceLine` for each unique Employee/Date combination, using the Work Order's labor rate.

## 9.4 Unified Ledger Logic

To ensure financial integrity and top-down architectural scaling, the ledger system follows a unified AR/AP engine approach.

### 9.4.1 Transactional Immutability
Ledger entries are strictly **immutable**. Once written, an entry cannot be edited or deleted. Financial corrections (Voiding an invoice, reversal of a payment) must be performed by creating a new **Reversing Entry**.

### 9.4.2 Entry Triggers
Financial events in the platform automatically generate ledger entries:
- **Invoices**: Triggered when status moves from `Draft` → `Issued`. Creates a **Debit** for the Customer.
- **Payments**: Triggered upon creation of a successful `Payment` record. Creates a **Credit** for the Customer.
- **Voids**: Triggered when an `Issued` invoice is moved to `Void`. Creates a **Credit** adjustment for the Customer.
- **Vendor Bills (Plus+)**: Triggered on Bill issuance. Creates a **Credit** for the Vendor.
- **Vendor Payments (Plus+)**: Triggered on Payment execution. Creates a **Debit** for the Vendor.

### 9.4.3 Running Balance (Net Position)
The `running_balance` field is calculated at **write-time** (insertion) to optimize read performance for customer/vendor statements.
- **Customer Balance**: Total Debits minus Total Credits (Positive = Money Owed To Us).
- **Vendor Balance**: Total Credits minus Total Debits (Positive = Money We Owe Them).

# 10. Domain-Driven Django App Structure (Top-Down)

To ensure the SDTA project scales from Lite to Enterprise without architectural debt, the project is organized into domain-specific applications. All business logic must reside within the `services.py` layer of these apps.

| App Name | Domain Description | Core Entities |
|---|---|---|
| `users/` | Multi-Tenant Auth, RBAC, Skills, and Positions. See **[Permission Specification](file:///Users/ronhoagland/.gemini/antigravity/brain/63427f0e-2cdd-4ddf-91be-5443c157608b/permission_spec_v1.md)**. | User, Role, PermissionMatrix, Skill, Position |
| `crm/` | Customer/Person/Contact triad and Site/Location logic. | Customer, Person, Contact, Address, Site, Location |
| `inventory/` | Item management, Kits, Pricebooks, and **Equipment (Tools)**. | InventoryItem, StockLevel, Serial/Lot, Kit, Pricebook, Equipment |
| `warehouse/` | Physical/Mobile Warehouses, Bins, and **Inventory Transfers**. | Warehouse, StorageLocation (Bins/Areas), InventoryTransfer |
| `procurement/` | Purchasing, Receiving, **Vendor Bills**, and **RMAs**. | Vendor, PurchaseOrder, Receiving, VendorBill, RMA |
| `service/` | Quotes, **TroubleCalls**, WorkOrders, Invoices, and Ledger. | Quote, TroubleCall, WorkOrder, Invoice, LedgerEntry |
| `maintenance/` | Asset Lifecycle | Asset, MaintenancePlan, Warranty |
| `tasks/` | SOP-instantiated check-lists and labor tracking. | Task, TaskTodo, TaskTimeEntry, SOP |
| `scheduling/` | Resource Timing | Schedule, TechnicianAvailability, Appointment |
| `pricing/` | Financial Rules | Pricebook, MultiCurrency, TaxJurisdiction |
| `automation/` | **SOP Workflows**, Steps, and resource requirements. | Workflow, EventTrigger, Condition, Action, SOPWorkflow, SOPStep |
| `workforce/` | **WorkGroups**, **WGDivisions**, and Crew teams. | WorkGroup, WGDivision, Crew |
| `fleet/` | **Vechicle** maintenance, mileage, and mobile stock. | Vehicle, VehicleMaintenance, VehicleMileage, MobileStock |
| `infrastructure/`| Audit events, Sequences, and the 25-entity Note/Document Arc. | AuditEvent, SequenceTracker, StorageTracker, Note, Document |

## 11. Key Libraries & Packages
| Library / Package | Purpose |
|-------------------|---------|
| `django-storages` + `boto3` | Routes all `FileField` and `ImageField` uploads to DigitalOcean Spaces (S3-compatible) in production |
| `stripe>=11.0.0` | Official Stripe Python SDK for all Stripe API interactions (Billing, Checkout, Connect, Webhooks) |
| `celery` | Asynchronous task queue for background jobs |
| `redis` (via redis-py) | Celery message broker; also used for Django caching if needed |
| `python-decouple` | Environment variable management; all secrets and environment-specific config injected via environment variables, never hardcoded |
| `WeasyPrint` | Server-side PDF generation for Plus/Pro tier (not used in Lite) |
| Postmark Python SDK | Transactional email dispatch via Postmark |

## 9.4 Prohibited Patterns

| Prohibited Pattern | Reason |
|--------------------|--------|
| SQLite in any environment | Does not support PostgreSQL RLS; breaks tenant isolation architecture |
| Auto-incrementing integer primary keys | Breaks future offline-mobile sync capability; UUIDv4 required everywhere |
| Hardcoded secrets in `settings.py` | Security risk; all secrets must be injected as environment variables |
| Generic Foreign Keys (GFKs) | Incompatible with PostgreSQL RLS enforcement |
| Direct database reads between SDP and SDTA | All inter-application data exchange must use the Internal REST API |
| Custom card entry forms posting to ServizmaDesk servers | Violates SAQ A PCI compliance; all card collection must use Stripe Checkout or Stripe Connect |
| Storing tenant attachments on production server filesystem | Prevents horizontal scaling; all file storage must use object storage in production |
| Running Redis on the same Droplet as the web server | Resource contention risk; Redis must run on a dedicated instance |
| Soft-delete by default | Hard-delete is the standard unless explicitly required by a status lifecycle specification |
| Vanilla CSS as primary styling mechanism | Tailwind CSS is the standard; vanilla CSS permitted only for extreme edge cases |
| Alpine.js or Hyperscript | Ruled out to keep frontend bundle minimal; HTMX v2.x is the only approved dynamic interaction library |
| Cross-Module Permission Bleed | Access must be checked against the specific Resource Key (e.g., Invoice), regardless of the current UI context (e.g., Customer Page). |

---

# 10. Sales Tax Compliance

| Item | Details |
|------|---------|
| Minnesota | SaaS is taxable in Minnesota. Must register with MN Department of Revenue. File monthly or quarterly depending on volume. |
| Other States | Economic nexus generally triggered at $100,000 revenue or 200 transactions. Monitor thresholds annually. |
| Recommended Tool | Stripe Tax (~0.5% of taxable revenue) — integrates directly with Stripe Billing to automate tax calculation, collection, and reporting. |

---

# 11. Document Relationships

| Relationship | Document |
|--------------|----------|
| Supersedes | ServizmaDesk Technical Architecture V1 |
| Supersedes | Open Technical Decisions in Section 10 of ServizmaDesk Product Tier Map V2 |
| Depends On / Validates Against | ServizmaDesk Product Tier Map V2 |
| Depends On / Validates Against | ServizmaDesk Lite MVP V4 Specification |
| Depends On / Validates Against | ServizmaDesk Platform (SDP) Specification V2 |
| Depends On / Validates Against | ServizmaDesk Pricing & Billing Specification V2 |
| Depends On / Validates Against | ServizmaDesk SDTA Data Models V4 |
| Defers To | Plus Specification (future) — SMS provider international pricing, Stripe Connect application fee decision |
| Defers To | Pro Specification (future) — REST API rate limits, advanced PDF generation scope |
| Precedes / Governs | Any repository README.md or code-level technical implementation document built during Phase 1 |

---

**End of Document**
