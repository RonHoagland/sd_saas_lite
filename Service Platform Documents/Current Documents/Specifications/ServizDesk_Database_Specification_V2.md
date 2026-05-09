# ServizDesk — Database Specification V2
**Document Status:** Working Draft — V2
**Date:** March 2026
**Classification:** Internal — Confidential
**Scope:** ServizDesk Tenant App (SDTA) PostgreSQL Database
**Supersedes:** V1

---

## Document Purpose

This document defines the complete database specification for the ServizDesk Tenant App (SDTA). It covers the database engine requirements, connection configuration, user and role architecture, Row-Level Security (RLS) policy design, indexing strategy, constraint patterns, data retention rules, and operational concerns.

This document is authoritative for all database-level implementation decisions. Application-level decisions (Django ORM, middleware, view logic) are governed by the Technical Architecture V2. Table and field definitions are governed by the Data Models V6.

---

# 1. Database Engine

| Item | Specification |
|---|---|
| Engine | PostgreSQL 16+ |
| Minimum Version | 16.0 (Row-Level Security improvements from PG 15/16 required) |
| Deployment | Managed PostgreSQL on DigitalOcean (preferred) or self-managed on a dedicated Droplet |
| Local Development | PostgreSQL 16+ via Docker Compose — SQLite is **strictly prohibited** in all environments |
| Encoding | UTF-8 |
| Locale | en_US.UTF-8 |
| Timezone | UTC (all timestamps stored in UTC; display conversion handled at the application layer) |

---

# 2. Databases

There are **two completely separate PostgreSQL databases** on the same database server instance. They are architecturally isolated — neither application may read from or write to the other's database.

| Database | Application | Purpose |
|---|---|---|
| `servizdesk_sdp` | ServizDesk Platform (SDP) | Subscription management, billing, provisioning, tenant account records |
| `servizdesk_sdta` | ServizDesk Tenant App (SDTA) | All tenant operational data — customers, assets, work orders, invoices, etc. |

> **Rule:** All inter-application communication between SDP and SDTA occurs exclusively via the Internal REST API. Cross-database queries are strictly prohibited.

---

# 3. Database Users & Roles

Seven PostgreSQL roles are required. Each role has a precisely scoped set of privileges aligned with the principle of least privilege.

## 3.1 Role Summary

| Role | Name | Type | Purpose |
|---|---|---|---|
| 1 | `sdta_app` | Application User | The Django application's runtime database user. Performs all reads and writes on behalf of authenticated tenant sessions. **Subject to RLS.** |
| 2 | `sdta_migration` | Migration User | Used exclusively by Django migrations (`manage.py migrate`). Has DDL privileges (CREATE TABLE, ALTER TABLE, DROP TABLE). Not used at runtime. |
| 3 | `sdta_readonly` | Read-Only User | Reserved for future use (reporting, analytics). Not required for the initial build. When implemented, will need its own DATABASES alias, environment variables, and connection pool. |
| 4 | `sdp_app` | Application User | The SDP Django application's runtime user, scoped exclusively to `servizdesk_sdp`. Cannot access `servizdesk_sdta`. |
| 5 | `sdp_migration` | Migration User | DDL user for SDP migrations only. |
| 6 | `postgres` (superuser) | Superuser | Used only for initial database creation, RLS policy setup, and role provisioning. Credentials locked in a secrets vault after setup. Not used at runtime under any circumstances. |
| 7 | `sdta_support` | Support/Backend User | Used by backend staff and support engineers who need direct database access for investigation and data correction. Has DML privileges only (no DDL). **BYPASS RLS = TRUE** — can read all tenant rows. Credentials are stored in a secrets vault (e.g., HashiCorp Vault) and are rotated after each support incident. A support engineer checks out credentials for the duration of the incident and they are rotated upon check-in. |

## 3.2 Role Privilege Matrix

| Privilege | `sdta_app` | `sdta_migration` | `sdta_readonly` | `sdta_support` |
|---|:---:|:---:|:---:|:---:|
| `SELECT` | ✓ (RLS-filtered) | ✓ | ✓ | ✓ (all tenants) |
| `INSERT` | ✓ (RLS-filtered) | ✓ | — | ✓ (all tenants) |
| `UPDATE` | ✓ (RLS-filtered) | ✓ | — | ✓ (all tenants) |
| `DELETE` | ✓ (RLS-filtered) | ✓ | — | ✓ (all tenants) |
| `CREATE TABLE` | — | ✓ | — | — |
| `ALTER TABLE` | — | ✓ | — | — |
| `DROP TABLE` | — | ✓ | — | — |
| `CREATE INDEX` | — | ✓ | — | — |
| `BYPASS RLS` | — | ✓ | — | ✓ |
| Access to `servizdesk_sdp` | — | — | — | — |

> **Critical:** `sdta_app` has `BYPASS RLS = FALSE`. It can never bypass the Row-Level Security policies regardless of the query it executes.
> `sdta_migration` has `BYPASS RLS = TRUE` — required so that Django's migration runner can perform DDL operations against all rows without tenant scoping.
> `sdta_support` has `BYPASS RLS = TRUE` and DML-only privileges — granted to backend staff for investigation and manual data correction. No DDL privileges. Credentials are vault-locked and issued only when needed.

## 3.3 Role Creation Scripts (Reference)

```sql
-- Runtime application user (SDTA)
CREATE ROLE sdta_app WITH LOGIN PASSWORD '<secrets-vault-value>' NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE;

-- Migration user (SDTA)
CREATE ROLE sdta_migration WITH LOGIN PASSWORD '<secrets-vault-value>' NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS;

-- Read-only reporting user (SDTA)
CREATE ROLE sdta_readonly WITH LOGIN PASSWORD '<secrets-vault-value>' NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE;

-- Support / backend staff user (SDTA) — DML only, BYPASS RLS
CREATE ROLE sdta_support WITH LOGIN PASSWORD '<secrets-vault-value>' NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS;

-- Grant schema-level access
GRANT CONNECT ON DATABASE servizdesk_sdta TO sdta_app, sdta_migration, sdta_readonly, sdta_support;
GRANT USAGE ON SCHEMA public TO sdta_app, sdta_migration, sdta_readonly, sdta_support;

-- Runtime privileges (DML only)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sdta_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sdta_readonly;

-- Migration privileges (full DDL)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdta_migration;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdta_migration;
GRANT CREATE ON SCHEMA public TO sdta_migration;

-- Support staff privileges (DML only, no DDL)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sdta_support;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO sdta_support;

-- Ensure future tables also inherit these grants
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sdta_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sdta_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sdta_migration;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sdta_support;
```

---

# 4. Connection Configuration

## 4.1 Connection String Format

```
postgresql://sdta_app:<password>@<host>:<port>/servizdesk_sdta?sslmode=require
```

All connection parameters are injected via environment variables. Hardcoded credentials in `settings.py` are strictly prohibited.

## 4.2 Django `DATABASES` Settings

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('SDTA_DB_NAME'),        # servizdesk_sdta
        'USER': env('SDTA_DB_USER'),        # sdta_app
        'PASSWORD': env('SDTA_DB_PASSWORD'),
        'HOST': env('SDTA_DB_HOST'),
        'PORT': env('SDTA_DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',           # Required in staging and production
        },
        'CONN_MAX_AGE': 60,                 # Persistent connections (seconds)
    },
    'worker': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('SDTA_DB_NAME'),        # servizdesk_sdta
        'USER': env('SDTA_WORKER_DB_USER'),  # sdta_migration — BYPASSRLS role
        'PASSWORD': env('SDTA_WORKER_DB_PASSWORD'),
        'HOST': env('SDTA_DB_HOST'),
        'PORT': env('SDTA_DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',           # Required in staging and production
        },
        'CONN_MAX_AGE': 60,                 # Persistent connections (seconds)
    }
}
```

> **`'worker'` Alias:** Connects to the same database (`servizdesk_sdta`) but authenticates as the `sdta_migration` role, which has `BYPASSRLS`. Application code accesses this alias via `Model.all_objects.using('worker')`. A `DATABASE_ROUTERS` configuration is not required — the alias is selected explicitly in code.

> In local development, `sslmode` may be set to `disable` via an environment variable override. It must be `require` in staging and production.

## 4.3 Connection Pooling

| Item | Configuration |
|---|---|
| Pooler | PgBouncer (recommended) — deployed between the application server and the PostgreSQL instance |
| Pooling Mode | **Transaction mode** — compatible with Django's connection handling and PostgreSQL RLS (session-level `SET` variables must be re-applied per transaction — see Section 5.3) |
| Pool Size | Start at 20 connections to PostgreSQL; tune based on observed load |
| Application `CONN_MAX_AGE` | 60 seconds (Django persistent connections) |

> **Important:** If PgBouncer transaction mode is used, the `SET LOCAL` command must be used instead of `SET` when applying the `app.current_tenant_id` session variable (see Section 5.3). `SET LOCAL` scopes the variable to the current transaction only, which is compatible with connection pooling.

---

# 5. Multi-Tenancy & Row-Level Security (RLS)

This is the most critical section of this specification. Tenant data isolation is enforced at three independent layers. The database layer (RLS) is the final failsafe.

## 5.1 Three-Layer Isolation Model

| Layer | Where | Mechanism |
|---|---|---|
| **Layer 1 — Field Constraint** | Database | Every SDTA table has a non-nullable `tenant_id UUID` column. A row without a `tenant_id` cannot exist. |
| **Layer 2 — Django ORM** | Application | A custom Django model manager automatically appends `.filter(tenant_id=current_tenant_id)` to every queryset. A custom middleware injects `current_tenant_id` from the authenticated session at the start of every request. |
| **Layer 3 — PostgreSQL RLS** | Database | RLS policies on every table restrict `sdta_app` to rows where `tenant_id = current_setting('app.current_tenant_id')::uuid`. Even if all application-layer filtering is bypassed, the database physically cannot return another tenant's rows. |

## 5.2 RLS Policy Design

RLS is enabled on every table in the `servizdesk_sdta` database. The policy is uniform across all tables.

### Enabling RLS on a Table

```sql
-- Enable RLS (blocks all access until policies are defined)
ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;

-- Force RLS even for the table owner (sdta_migration bypasses via BYPASSRLS attribute)
ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;
```

### Standard Tenant Isolation Policy

Applied to every table. One policy covers all operations (SELECT, INSERT, UPDATE, DELETE).

```sql
CREATE POLICY tenant_isolation_policy ON <table_name>
    AS PERMISSIVE
    FOR ALL
    TO sdta_app
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);
```

**`USING`** — filters rows for SELECT, UPDATE, DELETE.
**`WITH CHECK`** — validates tenant_id on INSERT and UPDATE.
**`TRUE` flag on `current_setting`** — returns NULL instead of raising an error if the setting is not set (e.g., during migrations). A NULL `tenant_id` match fails safely.

### Tables Exempt from Tenant RLS

Certain system-level tables do not carry a `tenant_id` and are exempt from tenant RLS. These tables are accessed only by `sdta_migration` or indirectly via application code that does not require tenancy scoping.

| Table | Reason |
|---|---|
| `django_migrations` | System table — migration tracking |
| `django_content_type` | System table — not used for GFKs; present for Django admin |
| `django_session` | Session storage |
| `auth_*` tables | Django's built-in auth tables (if used) |
| `subdomain_index` | Pre-authentication lookup table. Maps `subdomain → tenant_id` so the login and password-reset flows can resolve the correct tenant before any user is authenticated. Has no `tenant_id` column; RLS cannot apply. Read by `sdta_app`; written only by the SDP provisioning flow via `sdta_migration` or the Internal API. |

These tables should grant explicit DML to `sdta_app` without RLS enabled.

## 5.3 Setting the Tenant Context

Before executing any query in a user session, the Django middleware must set the PostgreSQL session-level variable that drives RLS.

### Django Middleware Pattern

The TenantMiddleware sets BOTH the Python-level context (used by `TenantManager` at the ORM layer) and the PostgreSQL-level context (used by the RLS policy) for every authenticated request. The `SET LOCAL` call **must be inside a `transaction.atomic()` block** — `SET LOCAL` in PostgreSQL is transaction-scoped and has no effect outside a transaction.

```python
from django.db import connection, transaction
from .tenant_context import set_current_tenant_id, clear_current_tenant_id

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Step 1: Set Python-level context so TenantManager filters correctly
        set_current_tenant_id(request.user.tenant_id)
        try:
            # Step 2: Wrap the entire request in one transaction so SET LOCAL
            # persists for all ORM calls within the view.
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # SET LOCAL is transaction-scoped — MUST be inside atomic()
                    cursor.execute(
                        "SET LOCAL app.current_tenant_id = %s",
                        [str(request.user.tenant_id)]
                    )
                response = self.get_response(request)
        finally:
            # CRITICAL: Always clear context to prevent leak to the next request
            # on this worker thread/connection.
            clear_current_tenant_id()

        return response
```

### Critical Rules
1. The `SET LOCAL app.current_tenant_id` statement **must be inside `transaction.atomic()`** or it is silently ignored by PostgreSQL (SET LOCAL only applies within the current transaction).
2. The middleware must run before any Django view or model access.
3. `clear_current_tenant_id()` must always be in a `finally` block.
4. This middleware covers the Python ORM layer (Layer 2) AND the PostgreSQL RLS layer (Layer 3) simultaneously. See Multi-Tenancy Specification V1 for the full three-layer isolation model.

### Unauthenticated Requests
For unauthenticated endpoints (login page, health check), `app.current_tenant_id` is not set. The `TRUE` fallback in the RLS policy returns NULL, causing all RLS checks to fail safely — no data is accessible.

## 5.4 Verifying RLS in Development

A test query to confirm RLS is working correctly:

```sql
-- As sdta_app with tenant_id set:
SET app.current_tenant_id = '<some-tenant-uuid>';
SELECT COUNT(*) FROM customer;  -- Must return only that tenant's rows

-- Without setting tenant_id:
RESET app.current_tenant_id;
SELECT COUNT(*) FROM customer;  -- Must return 0 rows
```

---

# 6. Database Constraints

## 6.1 Primary Key Convention

All tables use a UUID primary key. The default is generated at the application layer (Python `uuid4()`), not by the database, to support future offline-mobile sync.

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
```

> `gen_random_uuid()` is available as a fallback for database-level inserts (e.g., migrations, seed data). Application code must always supply the UUID.

## 6.2 Exclusive Arc Constraints (Notes & Documents)

The `note` and `document` tables use the Exclusive Arc pattern — exactly one foreign key column must be populated per row. This is enforced at the database level with a `CHECK` constraint.

```sql
-- Example for the note table (same pattern applies to document)
ALTER TABLE note ADD CONSTRAINT note_exclusive_arc CHECK (
    (
        (customer_id IS NOT NULL)::int +
        (contact_id IS NOT NULL)::int +
        (lead_id IS NOT NULL)::int +
        (opportunity_id IS NOT NULL)::int +
        (asset_id IS NOT NULL)::int +
        (quote_id IS NOT NULL)::int +
        (work_order_id IS NOT NULL)::int +
        (invoice_id IS NOT NULL)::int +
        (service_request_id IS NOT NULL)::int +
        (prev_maint_id IS NOT NULL)::int +
        (workflow_id IS NOT NULL)::int +
        (payment_id IS NOT NULL)::int +
        (user_id IS NOT NULL)::int +
        (vendor_id IS NOT NULL)::int +
        (purchase_order_id IS NOT NULL)::int +
        (vendor_bill_id IS NOT NULL)::int +
        (requisition_id IS NOT NULL)::int +
        (rma_id IS NOT NULL)::int +
        (task_id IS NOT NULL)::int +
        (vehicle_id IS NOT NULL)::int +
        (warehouse_id IS NOT NULL)::int +
        (ledger_id IS NOT NULL)::int +
        (equipment_id IS NOT NULL)::int +
        (safety_form_id IS NOT NULL)::int
    ) = 1
);
```

## 6.3 Contact Exclusive Arc Constraint

A `contact` must belong to exactly one of `customer`, `vendor`, or `bank`.

```sql
ALTER TABLE contact ADD CONSTRAINT contact_exclusive_arc CHECK (
    (
        (customer_id IS NOT NULL)::int +
        (vendor_id IS NOT NULL)::int +
        (bank_id IS NOT NULL)::int
    ) = 1
);
```

## 6.4 Address / Phone Exclusive Arc Constraint

Address and Phone rows must belong to exactly one parent entity.

```sql
-- address table
ALTER TABLE address ADD CONSTRAINT address_exclusive_arc CHECK (
    (
        (customer_id IS NOT NULL)::int +
        (contact_id IS NOT NULL)::int +
        (vendor_id IS NOT NULL)::int +
        (bank_id IS NOT NULL)::int +
        (asset_id IS NOT NULL)::int +
        (user_id IS NOT NULL)::int +
        (warehouse_id IS NOT NULL)::int +
        (work_group_id IS NOT NULL)::int
    ) = 1
);

-- phone table
ALTER TABLE phone ADD CONSTRAINT phone_exclusive_arc CHECK (
    (
        (customer_id IS NOT NULL)::int +
        (contact_id IS NOT NULL)::int +
        (vendor_id IS NOT NULL)::int +
        (bank_id IS NOT NULL)::int +
        (user_id IS NOT NULL)::int +
        (warehouse_id IS NOT NULL)::int
    ) = 1
);
```

## 6.5 Social Minimum Arc Constraint

Social rows must belong to at least one of `contact`, `person`, or `user`.

```sql
ALTER TABLE social ADD CONSTRAINT social_minimum_arc CHECK (
    contact_id IS NOT NULL OR person_id IS NOT NULL OR user_id IS NOT NULL
);
```

## 6.6 Foreign Key ON DELETE Behavior

| Relationship | ON DELETE Behavior | Rationale |
|---|---|---|
| Most child → parent FKs | `RESTRICT` | Enforces application-level delete rules; database acts as final safeguard |
| `note` → any parent | `CASCADE` | Notes cascade-delete when parent deletes |
| `document` → any parent | `RESTRICT` | Documents block parent deletion to ensure storage tracking integrity |
| `work_order_line` → `work_order` | `RESTRICT` | Line items block parent deletion |
| `quote_line` → `quote` | `RESTRICT` | Same |
| `invoice_line` → `invoice` | `RESTRICT` | Same |
| `purchase_order_line` → `purchase_order` | `RESTRICT` | Same |
| `requisition_line` → `requisition` | `RESTRICT` | Same |
| `work_order_subtask` → `work_order` | `CASCADE` | Subtasks owned by WO |
| `task_time` → `work_order_subtask` | `CASCADE` | Time records owned by subtask |
| `task_todo` → `work_order_subtask` | `CASCADE` | ToDos owned by subtask |
| `time_entry` → `work_order` | `CASCADE` | Time entries owned by WO |
| `work_order_team` → `work_order` | `CASCADE` | Team assignments owned by WO |
| `work_order_invoice` → `work_order` | `CASCADE` | Junction rows cascade-delete when WO is deleted |
| `work_order_invoice` → `invoice` | `CASCADE` | Junction rows cascade-delete when Invoice is deleted |
| `wo_sf_answer` → `work_order` | `RESTRICT` | Safety form answers block WO deletion (compliance record) |
| `wf_step` → `workflow` | `CASCADE` | Steps owned by WorkFlow |
| `wf_step_todo` → `wf_step` | `CASCADE` | ToDos owned by step |
| `wf_tool` → `workflow` | `CASCADE` | Tool requirements owned by WorkFlow |
| `wf_inventory` → `workflow` | `CASCADE` | Inventory requirements owned by WorkFlow |
| `customer_agreement` → `agreement` | `RESTRICT` | Agreements with active customer links cannot be deleted |
| `customer_agreement` → `customer` | `RESTRICT` | Customers with agreements cannot be deleted |
| `customer_agreement` → `asset` | `RESTRICT` | Assets under agreement cannot be deleted |
| `preventative_maintenance` → `customer_agreement` | `RESTRICT` | PMs block agreement deletion |
| `work_group_team` → `work_group` | `CASCADE` | Team assignments owned by WorkGroup |
| `work_group_asset` → `work_group` | `CASCADE` | Asset assignments owned by WorkGroup |
| `wg_division` → `work_group` | `CASCADE` | Divisions owned by WorkGroup |
| `check_in_out` → `equipment` | `RESTRICT` | Custody records block equipment deletion |
| `employee_skill` → `user` | `CASCADE` | Skills owned by employee |
| `employee_role` → `user` | `CASCADE` | Role assignments owned by employee |
| `kit_item` → `product` (kit) | `CASCADE` | Kit components owned by parent kit |
| `kit_item` → `product` (item) | `RESTRICT` | Products in kits cannot be deleted |
| `receiving` → `purchase_order_line` | `RESTRICT` | Received lines block PO line deletion |
| `lot_info` → `purchase_order_line` | `RESTRICT` | Lot records block PO line deletion |
| `vehicle_maintenance` → `vehicle` | `RESTRICT` | Maintenance history blocks vehicle deletion |
| `mileage_log` → `vehicle` | `CASCADE` | Mileage entries owned by vehicle |
| `vehicle_inventory` → `vehicle` | `CASCADE` | Inventory assignments owned by vehicle |
| `opportunity_contacts` → `opportunity` | `CASCADE` | Contact assignments owned by opportunity |
| `system_audits` → any parent | `SET NULL` or no FK | Audit events never deleted; reference but don't depend on parents |
| `session_log` → `user` | `SET NULL` | Session history preserved even if user deactivated |

---

# 7. Indexing Strategy

## 7.1 Mandatory Indexes (All Tables)

Every table in SDTA must carry these indexes as a baseline:

| Index | Column(s) | Type | Reason |
|---|---|---|---|
| Primary Key | `id` | UNIQUE B-Tree | UUID primary key |
| Tenant Scope | `tenant_id` | B-Tree | Every query filters by tenant first |
| Tenant + PK | `(tenant_id, id)` | B-Tree | Composite — most common lookup pattern |

## 7.2 Entity-Specific Indexes

### Core Entities

| Table | Index Column(s) | Reason |
|---|---|---|
| `customer` | `(tenant_id, status)` | List filtering by status |
| `customer` | `(tenant_id, assigned_to_id)` | Filter by assigned employee |
| `asset` | `(tenant_id, customer_id)` | Asset list per customer |
| `asset` | `(tenant_id, status)` | Filter active/inactive assets |
| `service_request` | `(tenant_id, customer_id)` | Service Requests per customer |
| `service_request` | `(tenant_id, status)` | Status filtering |
| `service_request` | `(tenant_id, asset_id)` | Service Requests per asset |
| `work_order` | `(tenant_id, customer_id)` | WO list per customer |
| `work_order` | `(tenant_id, asset_id)` | WO list per asset (service history) |
| `work_order` | `(tenant_id, status)` | Dashboard / list filtering |
| `work_order` | `(tenant_id, assigned_to_id)` | Filter by assigned technician |
| `work_order` | `(tenant_id, scheduled_date)` | Calendar and scheduling queries |
| `work_order` | `(tenant_id, work_group_id)` | WOs per WorkGroup |
| `work_order` | `(tenant_id, prev_maint_id)` | WOs generated by a PM |
| `work_order` | `(tenant_id, service_request_id)` | WOs from a Service Request |
| `quote` | `(tenant_id, customer_id)` | Quote list per customer |
| `quote` | `(tenant_id, status)` | Status filtering |
| `quote` | `(tenant_id, opportunity_id)` | Quotes per opportunity |
| `invoice` | `(tenant_id, customer_id)` | Invoice list per customer |
| `invoice` | `(tenant_id, status)` | Status filtering (overdue, outstanding) |
| `invoice` | `(tenant_id, due_date)` | Aging report queries |
| `work_order_invoice` | `(tenant_id, work_order_id)` | All invoices for a given Work Order |
| `work_order_invoice` | `(tenant_id, invoice_id)` | Reverse lookup — all WOs linked to an Invoice |
| `payments` | `(tenant_id, invoice_id)` | Payment lookup per invoice |
| `payments` | `(tenant_id, customer_id)` | Payment history per customer |
| `task` | `(tenant_id, status)` | Task filtering |
| `task` | `(tenant_id, assigned_to_id)` | Tasks per employee |

### CRM Pipeline (Plus+)

| Table | Index Column(s) | Reason |
|---|---|---|
| `lead` | `(tenant_id, status)` | Pipeline stage filtering |
| `lead` | `(tenant_id, customer_id)` | Leads per customer |
| `opportunity` | `(tenant_id, customer_id)` | Opportunities per customer |
| `opportunity` | `(tenant_id, status)` | Pipeline filtering |
| `opportunity` | `(tenant_id, lead_id)` | Opportunities from lead |

### Agreements & PM (Plus+)

| Table | Index Column(s) | Reason |
|---|---|---|
| `agreement` | `(tenant_id, status)` | Active agreement filtering |
| `customer_agreement` | `(tenant_id, customer_id)` | Agreements per customer |
| `customer_agreement` | `(tenant_id, agreement_id)` | Customers per agreement |
| `customer_agreement` | `(tenant_id, asset_id)` | Agreements per asset |
| `preventative_maintenance` | `(tenant_id, customer_agreement_id)` | PMs per agreement |
| `preventative_maintenance` | `(tenant_id, asset_id)` | PMs per asset |
| `preventative_maintenance` | `(tenant_id, status)` | Active PM filtering |

### WorkGroups (Plus+)

| Table | Index Column(s) | Reason |
|---|---|---|
| `work_group` | `(tenant_id, customer_id)` | WorkGroups per customer |
| `work_group` | `(tenant_id, status)` | Status filtering |
| `work_group_asset` | `(tenant_id, work_group_id)` | Assets in a WorkGroup |
| `work_group_asset` | `(tenant_id, asset_id)` | WorkGroups containing an asset |

### Purchasing & Vendors (Plus+)

| Table | Index Column(s) | Reason |
|---|---|---|
| `purchase_order` | `(tenant_id, vendor_id)` | POs per vendor |
| `purchase_order` | `(tenant_id, status)` | Status filtering |
| `vendor_bill` | `(tenant_id, vendor_id)` | Bills per vendor |
| `vendor_bill` | `(tenant_id, status)` | AP status filtering |
| `payments` | `(tenant_id, vendor_id)` | Vendor payments lookup |
| `requisition` | `(tenant_id, employee_id)` | Requisitions per requestor |
| `requisition` | `(tenant_id, status)` | Status filtering |
| `rma` | `(tenant_id, vendor_id)` | RMAs per vendor |
| `rma` | `(tenant_id, status)` | Status filtering |
| `receiving` | `(tenant_id, po_line_id)` | Receiving per PO line |

### Inventory (Plus+)

| Table | Index Column(s) | Reason |
|---|---|---|
| `location_assigned_inventory` | `(tenant_id, sub_location_id)` | Stock per location |
| `location_assigned_inventory` | `(tenant_id, product_id)` | Locations per product |
| `inventory_transfer` | `(tenant_id, product_id)` | Transfers per product |
| `inventory_transfer` | `(tenant_id, status)` | Pending transfer filtering |
| `inventory_count` | `(tenant_id, product_id)` | Counts per product |

### WorkFlow & Safety (Pro+)

| Table | Index Column(s) | Reason |
|---|---|---|
| `workflow` | `(tenant_id, status)` | Active workflow filtering |
| `wf_step` | `(tenant_id, workflow_id)` | Steps per workflow |
| `safety_form` | `(tenant_id, status)` | Active form filtering |
| `wo_sf_answer` | `(tenant_id, work_order_id)` | Safety answers per WO |
| `wo_sf_answer` | `(tenant_id, employee_id)` | Safety answers per employee |

### HR & Equipment (Pro+)

| Table | Index Column(s) | Reason |
|---|---|---|
| `employee_skill` | `(tenant_id, employee_id)` | Skills per employee |
| `employee_skill` | `(tenant_id, skill_id)` | Employees per skill |
| `employee_skill` | `(tenant_id, expiration_date)` | Expiring certification queries |
| `equipment` | `(tenant_id, status)` | Available equipment filtering |
| `check_in_out` | `(tenant_id, equipment_id)` | Custody history per tool |
| `check_in_out` | `(tenant_id, employee_id)` | Tools per employee |
| `credit_card` | `(tenant_id, employee_id)` | Cards per employee |

### Fleet (Add-On)

| Table | Index Column(s) | Reason |
|---|---|---|
| `vehicle` | `(tenant_id, status)` | Active vehicle filtering |
| `vehicle` | `(tenant_id, assigned_user_id)` | Vehicles per driver |
| `vehicle_maintenance` | `(tenant_id, vehicle_id)` | Maintenance per vehicle |
| `vehicle_maintenance` | `(tenant_id, status)` | Overdue/scheduled filtering |
| `mileage_log` | `(tenant_id, vehicle_id)` | Mileage per vehicle |
| `mileage_log` | `(tenant_id, user_id)` | Mileage per driver |
| `vehicle_inventory` | `(tenant_id, vehicle_id)` | Inventory per vehicle |

### System & Audit

| Table | Index Column(s) | Reason |
|---|---|---|
| `note` | `(tenant_id, customer_id)` | Notes per entity (repeat per FK column as needed) |
| `note` | `(tenant_id, work_order_id)` | Notes per entity |
| `document` | `(tenant_id, customer_id)` | Docs per entity (repeat per FK column as needed) |
| `session_log` | `(tenant_id, user_id)` | Session history per user |
| `system_audits` | `(tenant_id, entity_type, entity_id)` | Audit trail lookup per record |
| `system_audits` | `(tenant_id, event_timestamp)` | Time-ordered audit queries |
| `webhook_log` | `stripe_event_id` | UNIQUE — idempotency enforcement |
| `sequence_tracker` | `(tenant_id, entity_type, year)` | UNIQUE — collision-free counter |

## 7.3 Full-Text Search (Future)

For the Lite MVP, search is implemented via `ILIKE` queries on indexed text columns (customer name, asset serial number, etc.). A dedicated full-text search index strategy (using PostgreSQL `tsvector` / `GIN` indexes) is deferred to a post-MVP performance optimization pass.

---

# 8. Data Types Reference

| Use Case | PostgreSQL Type | Notes |
|---|---|---|
| Primary Keys | `UUID` | Generated via `uuid4()` at application layer |
| Foreign Keys | `UUID` | Always matches the PK type of the referenced table |
| Tenant ID | `UUID NOT NULL` | Non-nullable on every SDTA table |
| Monetary values | `NUMERIC(12, 2)` | Fixed precision; never use FLOAT for money |
| Percentages / rates | `NUMERIC(7, 4)` | e.g., 8.25% stored as 8.2500 |
| Text (short) | `VARCHAR(255)` | Names, labels, prefixes |
| Text (long) | `TEXT` | Notes, descriptions, JSON blobs stored as text |
| Structured config | `JSONB` | Recurrence patterns, onboarding checklist flags, audit details |
| Timestamps | `TIMESTAMPTZ` | All timestamps include timezone; stored as UTC |
| Dates (no time) | `DATE` | Warranty dates, due dates, service dates |
| Boolean flags | `BOOLEAN NOT NULL DEFAULT FALSE` | Explicit default required on all boolean fields |
| File sizes | `BIGINT` | Bytes — supports files up to 9 exabytes |
| IP addresses | `INET` | `GenericIPAddressField` in Django |
| Counters | `INTEGER` | Sequence tracker values, sort orders |

---

# 9. Sequence & Record Numbering

Human-readable record numbers (e.g., `W26-0001`, `Q26-0001`) are generated using the `sequence_tracker` table, not PostgreSQL sequences. PostgreSQL sequences are global and cannot be scoped per tenant.

## 9.1 `sequence_tracker` Table Behavior

```sql
CREATE TABLE sequence_tracker (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- e.g., 'WorkOrder', 'Invoice', 'Customer'
    year INTEGER,                       -- NULL if reset_period = 'Never'
    last_value INTEGER NOT NULL DEFAULT 0,
    UNIQUE (tenant_id, entity_type, year)
);
```

## 9.2 Atomic Increment Pattern

The counter increment **must be atomic** to prevent duplicate record numbers under concurrent requests.

```sql
-- Atomic increment via UPDATE ... RETURNING (no race condition)
UPDATE sequence_tracker
SET last_value = last_value + 1
WHERE tenant_id = %s AND entity_type = %s AND year = %s
RETURNING last_value;
```

## 9.3 Coordination Contract (Forward-Only)

To prevent duplicate record numbers when users modify seed values, the interaction between `tenant_preference` (source of settings) and `sequence_tracker` (source of truth counter) follows these rules:

1.  **Initial Seeding**: At provisioning, `sequence_tracker` rows are initialized. The `last_value` is set to `[start_number] - 1` from the default `tenant_preference` values.
2.  **Forward-Only Constraint**: If a user updates a `*_start_number` in `tenant_preference`, the application layer must verify that the new value is **greater than** the current `last_value` in `sequence_tracker`.
3.  **Counter Update**: Upon validation of an increased start number, the `sequence_tracker.last_value` must be updated to `[new_start_number] - 1`.
4.  **Immutability**: Once a record's human-readable number is generated and stored, it is immutable. Changes to `tenant_preference` or `sequence_tracker` do not trigger updates to existing records.

---

# 10. Data Retention & Deletion

## 10.1 Retention Rules

| Data Category | Retention Rule |
|---|---|
| Active tenant data | Retained indefinitely while account is active |
| Cancelled / expired tenant data | 30-day `Cancelled (Read Only)` window (all users can log in; no writes), then 60-day `Cancelled` data retention period (SDTA access revoked). After the 60-day retention countdown expires, a Celery background worker permanently hard-deletes all data for that `tenant_id`. Total: 90 days from billing period end. See Pricing & Billing Specification V2, Section 8. |
| Trial account (unconverted) | Day 15: read-only. Day 45: 60-day grace begins. Day 105: permanent deletion |
| `system_audits` table | 18-month rolling. Records older than 18 months are purged by a scheduled Celery task |
| `session_log` table | 18-month rolling. Same Celery purge schedule as audit events |
| `issues_errors` table | 90-day rolling |
| `stripe_api_request_log` | 90-day rolling |
| `login_attempt_log` | 18-month rolling. Purged by the same Celery maintenance task as `session_log` |
| `webhook_log` | 12-month rolling (after which idempotency window is moot) |
| `email_delivery_log` | 12-month rolling |

## 10.2 Tenant Hard-Delete Process

The 60-day data deletion is performed by a Celery background worker using the following sequence:

1. Confirm `TenantState.status = 'Pending Deletion'` and deletion date has passed
2. **Delete all S3 objects for the tenant first** — enumerate all `Document` records for the tenant, call the S3/Spaces API to delete each object. If any S3 deletion fails, abort the entire process, alert via Notification + Sentry, and do not proceed to database deletion. See Background Tasks Specification V2 for the full S3 cleanup ordering rule.
3. Delete all child database records in dependency order (leaf tables first, parent tables last)
4. Delete the `TenantState` record last
5. Log the deletion completion in SDP via the Internal REST API

> **Ordering rule:** S3 objects must be deleted BEFORE their corresponding database records. Deleting the database record first makes the S3 object permanently orphaned — unreachable and unbillable. If S3 deletion fails, the database record serves as the audit reference needed to retry cleanup.

**Deletion order (high-level, leaf tables first):**

1. **Audit & Logs:** SystemAudits → NavigationAudit → ProcessTransaction → TriggerLog → SessionLog → IssuesErrors → StripeAPIRequestLog → WebhookLog → EmailDeliveryLog → StripeLog → DataExportLog → TenantSyncLog

> **`LoginAttemptLog` is intentionally excluded from tenant hard-delete.** Its `tenant_id` column is a plain UUID, not a FK, specifically so that forensic login history survives tenant deletion. Even after a tenant's workspace is permanently deleted, the login attempt records remain accessible to ServizDesk staff for security investigation. These records are cleaned up by the 18-month rolling `purge_login_attempt_logs` task regardless of tenant status.
2. **Notes & Documents:** Note → Document
3. **Fleet (if active):** MileageLog → VehicleInventory → VehicleMaintenance → Vehicle
4. **Safety & Equipment:** WOSFAnswer → CheckInOut → WFTool → WFInventory → WFStepToDo → WFStep → WFSafetyForm → WorkFlow → SafetyForm → Equipment → EmployeeSkill → Skill → EmployeePurchase → CreditCard
5. **Advanced Pricing (Pro/Enterprise):** PricebookEntry → Pricebook
6. **Communications & Zones (Enterprise):** TriggerTemplate → CommunicationTrigger → CommunicationTemplate → EmployeeZone → TerritoryZone → ErrorCode
7. **Work Order Detail:** TaskToDo → TaskTime → TimeEntry → WorkOrderTeam → WorkOrderLine → WorkOrder
8. **WorkGroups (incl. Enterprise Project Mgmt):** MilestoneTask → SprintTask → SprintMember → Sprint → Milestone → PortfolioProject → PortfolioMember → Portfolio → WorkGroupAsset → WorkGroupTeam → WGDivision → WorkGroup → WGTRole
9. **PM & Agreements:** PreventativeMaintenance → CustomerAgreement → Agreement
10. **Financials:** LedgerEntry → Payments → InvoiceLine → InvoiceAsset → WorkOrderInvoice → Invoice → QuoteLine → QuoteAsset → Quote → StripeResponse → StripeConnection → StripeConnectionLog
11. **Procurement:** RMA → LotInfo → Receiving → RequisitionLine → Requisition → PurchaseOrderLine → PurchaseOrder → VendorBill → Vendor
12. **Inventory:** Location → InventoryCount → InventoryTransfer → LocationAssignedInventory → SubLocation → Warehouse → InvPriceHistory → KitItem → InventoryItem
13. **CRM Pipeline:** OpportunityContacts → Opportunity → Lead
14. **CRM Core:** AssociatedTask → Task → ServiceRequest → SubAsset → Asset → Contact → Social → Phone → Address → Person → Customer
15. **Identity:** EmployeePreference → EmployeeRole → EmployeePosition → User → RolePermission → Role → Position → Department
16. **Accounting:** Accounting → Bank
17. **Tenant Infrastructure:** Notification → OnboardingState → EmailUsageTracker → SMSUsageTracker → StorageTracker → TenantAddOn → SequenceTracker → TenantPreference → TenantState → SubdomainIndex

> **SubdomainIndex cleanup is mandatory.** After `TenantState` is deleted, the `SubdomainIndex` row for this tenant's subdomain must be deleted. Failure to do so permanently claims the subdomain — a future tenant cannot provision with the same subdomain name, and the dead row will cause `resolve_tenant_from_subdomain()` to resolve a tenant that no longer exists.

## 10.3 Audit Event Immutability

`system_audits` rows are **never updated or deleted by the application**. The only permitted deletion is the rolling 18-month purge by the Celery maintenance task, and for full tenant hard-delete. Application code must not issue `UPDATE` or `DELETE` statements against `system_audits`.

```sql
-- Enforce at DB level: revoke DELETE and UPDATE on system_audits from sdta_app
REVOKE DELETE, UPDATE ON system_audits FROM sdta_app;
```

---

# 11. Backup & Recovery

| Item | Specification |
|---|---|
| Backup Method | DigitalOcean Managed Database automated daily backups (if using managed PostgreSQL) |
| Backup Frequency | Daily automated snapshots |
| Backup Retention | 7 days of daily backups |
| Point-in-Time Recovery | Enabled via WAL archiving on DigitalOcean Managed PostgreSQL |
| Recovery Objective (RPO) | ≤ 24 hours (daily backup cadence) |
| Recovery Objective (RTO) | ≤ 4 hours (restore from snapshot) |
| Cross-Region Backup | Deferred until tenant count warrants the cost |
| Restore Scope | Database-level restore only. Per-tenant selective restore is not offered as a product feature — tenants are informed that deletion is permanent. |
| Dev/Staging | No automated backups required. Staging data is disposable. |

> **Product Note:** ServizDesk does not expose any backup or restore capability to tenants. Permanent deletion is permanent. This is communicated in the delete confirmation dialog (per Data Models V6, Part 5).

---

# 12. Database Monitoring & Health

| Item | Tool / Approach |
|---|---|
| Query performance | `pg_stat_statements` extension — enabled in all environments to track slow queries |
| Long-running queries | Alert if any query exceeds 30 seconds (configurable threshold) |
| Connection count | Alert at 80% of `max_connections` |
| Replication lag | Monitor if read replicas are introduced |
| Disk usage | Alert at 70% and 85% of allocated disk |
| Lock monitoring | `pg_locks` view — alert on lock wait time exceeding 10 seconds |
| Managed DB dashboards | DigitalOcean Managed Database metrics dashboard (if using managed PostgreSQL) |

## 12.1 `pg_stat_statements` Setup

```sql
-- Enable the extension (run as superuser)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

Add to `postgresql.conf`:
```
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
```

---

# 13. Environment Variables Reference

All database credentials and configuration are injected via environment variables. These must be stored in a secrets vault (e.g., DigitalOcean Secrets, HashiCorp Vault, or `.env` file excluded from version control in local development).

| Variable | Description | Example |
|---|---|---|
| `SDTA_DB_NAME` | SDTA database name | `servizdesk_sdta` |
| `SDTA_DB_USER` | SDTA app DB username | `sdta_app` |
| `SDTA_DB_PASSWORD` | SDTA app DB password | `<strong-random-password>` |
| `SDTA_DB_HOST` | PostgreSQL host | `db-servizma.b.db.ondigitalocean.com` |
| `SDTA_DB_PORT` | PostgreSQL port | `5432` |
| `SDTA_DB_SSLMODE` | SSL mode | `require` (staging/prod) / `disable` (local) |
| `SDTA_MIGRATION_DB_USER` | Migration user | `sdta_migration` |
| `SDTA_MIGRATION_DB_PASSWORD` | Migration user password | `<strong-random-password>` |
| `SDTA_WORKER_DB_USER` | Background worker DB user (uses `sdta_migration` role — BYPASSRLS for cross-tenant reads) | `sdta_migration` |
| `SDTA_WORKER_DB_PASSWORD` | Background worker DB password | `<strong-random-password>` |
| `SDP_DB_NAME` | SDP database name | `servizdesk_sdp` |
| `SDP_DB_USER` | SDP app DB username | `sdp_app` |
| `SDP_DB_PASSWORD` | SDP app DB password | `<strong-random-password>` |
| `SDP_DB_HOST` | SDP PostgreSQL host | Same server as SDTA or separate |
| `SDP_DB_PORT` | SDP PostgreSQL port | `5432` |
| `CELERY_BROKER_URL` | Redis connection for Celery (TLS required in production) | `rediss://:pass@internal-host:6379/0` |
| `REDIS_PASSWORD` | Redis AUTH password | `<strong-random-password>` |
| `STRIPE_SECRET_KEY` | Stripe API Secret | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook verify key | `whsec_...` |
| `DJANGO_SECRET_KEY` | Application signing key | `<strong-random-key>` |

---

# 14. Security Hardening Checklist

| Item | Required |
|---|---|
| `postgres` superuser disabled or password locked in vault after initial setup | ✓ |
| `sdta_app` has no DDL privileges (no CREATE, ALTER, DROP) | ✓ |
| `sdta_migration` is not used as the runtime application user | ✓ |
| All connections require SSL (`sslmode=require`) in staging and production | ✓ |
| `system_audits` table has UPDATE and DELETE revoked from `sdta_app` | ✓ |
| RLS enabled and forced on all tenant-scoped tables | ✓ |
| `BYPASSRLS` granted only to `sdta_migration` (DDL/migrations) and `sdta_support` (backend staff — DML only, no DDL) | ✓ |
| `sdta_support` credentials stored in vault; not distributed in environment configs; issued only when needed | ✓ |
| No hardcoded passwords in `settings.py` or source code | ✓ |
| Django `SECRET_KEY` stored as environment variable — never hardcoded or committed to source control | ✓ |
| Redis accessible on internal private network only — not publicly exposed; `requirepass` set; TLS enabled | ✓ |
| Database port not exposed publicly (internal network only) | ✓ |
| `pg_stat_statements` enabled for query monitoring | ✓ |
| Automated daily backups enabled in production | ✓ |
| Stripe webhook secret verified on all incoming webhooks | ✓ |
| HTTP security headers: `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy` set in Nginx. `Content-Security-Policy` set by Django middleware (`django-csp`) — NOT Nginx — because CSP requires per-request nonce generation | ✓ |
| HTTP security headers verified post-deployment (curl or securityheaders.com) | ✓ |
| `login_attempt_log` and `system_audits` tables have UPDATE and DELETE revoked from `sdta_app` | ✓ |

---

# 15. Document Relationships

| Relationship | Document |
|---|---|
| Governed by (application stack) | ServizDesk Technical Architecture V2 |
| Governed by (table/field definitions) | ServizDesk Data Models V6 |
| Governed by (delete rules) | ServizDesk Data Models V6, Part 5 |
| Governed by (tier feature access) | ServizDesk Product Tier Map V2 |
| Governed by (calculations) | ServizDesk Invoice Calculation Specification V1 |
| Governed by (data retention / cancellation) | ServizDesk Platform (SDP) Specification V2 |

---

# 16. Invoice Calculation Stored Fields

The following fields on the `Invoice` table are **stored** and must be updated by the application layer upon any change to the related `InvoiceLine` records.

| Field | Purpose | Requirement |
| :--- | :--- | :--- |
| `line_item_total` | Pre-tax subtotal | Sum of all (quantity * price) - Sum of all (quantity * discount_price) |
| `line_item_tax_total` | Total tax | Calculated using the frozen `tax_rate` on the header against taxable lines |
| `invoice_total` | Grand total | `line_item_total` + `line_item_tax_total` |

---

*End of ServizDesk Database Specification V2*
