# ServizDesk Pre-Code Audit & Implementation Plan

**Date:** March 2026
**Scope:** Comprehensive audit of all existing code against design specifications
**Purpose:** Identify what to reuse, what patterns to keep, what to rebuild, and what to do next

---

## 1. Executive Summary

This document audits all code in the `Code to Review` folder — four codebases plus reference files — against the 30 design specification documents. The goal is to determine what is reusable, what patterns to carry forward, where service03 diverged from the specs, and what the implementation roadmap should be.

### Codebases Audited

| Codebase | Location | Role | Size |
|---|---|---|---|
| **service03** | `Code to Review/service03/` | Last implementation attempt (Django 6.0) | 12 apps, ~90 models, ~14.6K LOC |
| **Desktop Version** | `Code to Review/Desktop Version/` | Original desktop app being migrated to SaaS | 18 apps, numbering + lifecycle systems |
| **Django-CRM-master** | `Code to Review/Django-CRM-master/` | Reference: multi-tenant CRM with RLS | REST API + SvelteKit frontend |
| **koalixcrm-master** | `Code to Review/koalixcrm-master/` | Reference: CRM/ERP with accounting | Invoicing, quoting, GL integration |
| **files/** | `Code to Review/files/` | Architecture reference templates | Settings, middleware, base models |

### Bottom Line

Service03 is a solid foundation with correct multi-tenancy architecture, but it has significant sync issues with the specifications. The Desktop Version contains the authoritative implementations of the Numbering Service and Lifecycle Framework that service03 is missing entirely. The reference codebases (Django-CRM, KoalixCRM) contributed useful patterns that are already partially absorbed into the architecture.

---

## 2. What Service03 Gets Right (Keep As-Is)

These components in service03 are correctly implemented and aligned with specifications. They should be carried forward without major changes.

### 2.1 Multi-Tenancy Architecture (Aligned with Multi-Tenancy Spec V1 + Database Spec V2)

- **TenantModel base class** (`config/base_models.py`): UUID PK, tenant_id, created_by/on, updated_by/on — matches Data Models V6 mandate
- **TenantManager**: Auto-filters by current tenant context — correct
- **`all_objects` manager**: Unfiltered access for background tasks — correct per spec
- **Cross-tenant write protection**: `save()` raises ValueError — correct
- **Thread-safe tenant context** (`config/tenant_context.py`): Uses `asgiref.local.Local()` — correct for PgBouncer transaction mode

### 2.2 Database Configuration (Aligned with Database Spec V2)

- **Dual database aliases**: `default` (sdta_app, RLS-bound) + `worker` (sdta_migration, BYPASSRLS) — correct
- **PostgreSQL-only enforcement**: No SQLite fallback — correct
- **RLS via `SET LOCAL`**: Transaction-scoped, PgBouncer-safe — correct
- **Setup scripts**: `setup_postgres.sql` + `setup_rls.sql` — correct role creation
- **Connection pooling**: `CONN_MAX_AGE = 60` on default — correct

### 2.3 Authentication Architecture (Aligned with Security Features Spec + Technical Architecture V2)

- **Dual user model**: StaffUser (global, non-tenant) + User (tenant-scoped, AbstractBaseUser) — correct
- **StaffUserBackend**: Custom auth backend for /admin/ — correct
- **Backend ordering**: StaffUserBackend → ModelBackend → AxesStandaloneBackend — correct
- **Worker alias for admin**: TenantModelAdmin routes to `worker` DB — correct per Database Spec V2
- **Group-based staff permissions**: support/ops/engineering with view/write/delete — correct

### 2.4 Middleware Stack (Aligned with Technical Architecture V2)

- **Correct ordering**: SecurityMiddleware → Session → CSRF → Auth → AdminBypass → TenantMiddleware → InternalAPIKey → CSP → Axes
- **TenantMiddleware**: Sets both Python context and PostgreSQL `SET LOCAL` — correct dual-layer
- **AdminBypassMiddleware**: No-op; admin uses worker alias via TenantModelAdmin — correct
- **InternalAPIKeyMiddleware**: Bearer token with `secrets.compare_digest()` — correct

### 2.5 Security Hardening (Aligned with Security Features Spec)

- **django-axes**: 5 failure limit, 30-min cooldown, reset on success — matches spec
- **django-csp**: Nonce-based, Stripe whitelisted — correct
- **Cookie security**: Secure, HttpOnly, SameSite=Lax — correct
- **HSTS**: 31536000 seconds — correct
- **Password policy**: 10-char minimum, complexity checks — correct
- **Password reset timeout**: 24 hours — correct

### 2.6 Testing Infrastructure

- **Real PostgreSQL** (not SQLite) — correct per Technical Architecture V2
- **SDTATestCase base class**: Automatic tenant context setup/teardown — good pattern
- **Factory helpers**: make_person(), make_customer(), make_user(), etc. — reusable
- **17 test files** covering all apps — good coverage foundation

### 2.7 Infrastructure Models (Aligned with Multiple Specs)

- **TenantState**: Non-tenant, correct fields (subdomain, tier, status, trial dates) — matches Seed Data V2
- **TenantAddOn**: Correct add-on tracking — matches Product Tier Map V2
- **SubdomainIndex**: Fast subdomain → tenant lookup — matches Multi-Tenancy Spec V1
- **SystemAudits**: Immutable audit trail with before/after snapshots — correct
- **SequenceTracker**: Present (will be replaced by Numbering Service) — correct legacy
- **ProcessTransaction**: Idempotency keys for background tasks — correct per Background Tasks V2
- **All usage trackers**: Storage, Email, SMS — correct per Pricing & Billing V3
- **Stripe integration models**: Connection, Response, Log, APIRequestLog — correct

---

## 3. What Service03 Gets Wrong or Is Missing (Sync Issues)

These are the gaps where service03 diverges from the specifications or is missing required implementations.

### 3.1 MISSING: Numbering Service (Numbering Service Spec V1)

**Severity: HIGH — Core Service Not Implemented**

Service03 has only the legacy `SequenceTracker` model (single counter per entity type). The specifications require a three-model replacement:

| Required (Spec) | Service03 Status |
|---|---|
| `NumberingRule` model | **MISSING** |
| `NumberSequence` model | **MISSING** |
| `AssignedNumber` model (immutable) | **MISSING** |
| `generate_number()` service function | **MISSING** |
| `assign_number()` service function | **MISSING** |
| `get_next_sequence_value()` with SELECT FOR UPDATE | **MISSING** |
| `check_reset_needed()` (yearly/monthly reset) | **MISSING** |
| `format_number()` with configurable formatting | **MISSING** |
| `NumberingMixin` for entity models | **MISSING** |
| Reverse-alphabet year encoding for InventoryItem | **MISSING** |

**Source to pull from:** Desktop Version (`Code to Review/Desktop Version/numbering/`) has a working implementation with NumberingRule, NumberSequence, AssignedNumber, and all service functions. This should be the primary source for the new implementation.

### 3.2 MISSING: Lifecycle Framework (Lifecycle Framework Spec V1)

**Severity: HIGH — Core Service Not Implemented**

Service03 has no lifecycle/state machine system. Status fields exist on models (e.g., WorkOrder.status has choices) but there is no enforcement layer.

| Required (Spec) | Service03 Status |
|---|---|
| `LifecycleStateDef` model | **MISSING** |
| `LifecycleTransitionRule` model | **MISSING** |
| `LifecycleTransitionAudit` model (immutable) | **MISSING** |
| `execute_transition()` service function | **MISSING** |
| `get_available_transitions()` | **MISSING** |
| `get_transition_history()` | **MISSING** |
| Deny-by-default transition enforcement | **MISSING** |
| Role-based transition gating | **MISSING** |
| Final/locked state types | **MISSING** |
| Admin override path | **MISSING** |

**Source to pull from:** Desktop Version (`Code to Review/Desktop Version/lifecycle/`) has a working implementation. This should be the primary source.

### 3.3 MISSING: Note & Document Models (Note & Document Spec V1)

**Severity: HIGH — Core Feature Not Implemented**

Service03 has no Note or Document models at all. The Desktop Version has both.

| Required (Spec) | Service03 Status |
|---|---|
| `Note` model with 25 parent FKs | **MISSING** |
| `Document` model with 25 parent FKs | **MISSING** |
| Exclusive arc CHECK constraint | **MISSING** |
| `clean()` validation (exactly one parent FK non-null) | **MISSING** |
| Partial indexes per parent FK | **MISSING** |
| `scan_status` enum on Document (Pending/Clean/Infected) | **MISSING** |

**Source to pull from:** Desktop Version (`Code to Review/Desktop Version/notes/` and `Code to Review/Desktop Version/documents/`).

### 3.4 MISSING: File Upload System (File Upload Spec V1)

**Severity: MEDIUM — Required for Document model**

| Required (Spec) | Service03 Status |
|---|---|
| S3/Spaces file storage backend | **MISSING** |
| Pre-signed URL generation | **MISSING** |
| File scan/quarantine workflow | **MISSING** |
| `FileUploadLog` model | **MISSING** |
| `FileDownloadLog` model | **MISSING** |
| Deterministic path generation | **MISSING** |

**Source to pull from:** Desktop Version (`Code to Review/Desktop Version/files/`) has the path generation pattern.

### 3.5 Model Field Mismatches vs. Data Models V6

Several service03 models have field differences from the authoritative Data Models V6:

#### Customer Model (service03 `crm/models.py` vs. Data Models V6)
- **Missing fields**: `hold_date`, `hold_reason`, `closed_at`, `closed_reason` — required by System Status V3 for Hold/Closed status transitions
- **Naming**: service03 uses `status` choices as Python strings; spec requires these to align with LifecycleStateDef entries

#### Product/InventoryItem Model (service03 `inventory/models.py` vs. Data Models V6)
- **Model name**: service03 calls it `Product` — the internal Django model name should be `InventoryItem` per Data Models V6 (Product is the Lite UI label only)
- **Missing**: Reverse-alphabet year encoding for product_number prefix
- **Field name**: service03 uses `product_number` — should be fine as the display field, but spec says internal entity_type key is `inventory_item`

#### Vendor Model (service03 `procurement/models.py` vs. Data Models V6)
- **Missing fields**: `tax_id` is present but `payment_terms` naming may differ
- **Status values**: service03 has Active/Inactive; spec requires Active/Inactive/Do Not Use (System Status V3 Section 20)

#### WorkOrder Model (service03 `service/models.py` vs. Data Models V6)
- **Missing fields**: `hold_date`, `hold_reason` — required for On Hold status
- **Missing**: `customer_facing_notes` (Plus+ tier)
- **Missing**: `recurrence_pattern` (JSONField for recurring work orders)

#### Invoice Model
- **Missing**: `stripe_payment_link_url` — required for online payment integration
- **Missing**: `deposit_applied`, `deposit_type`, `deposit_amount` — required for quote-to-invoice deposit flow
- **Missing**: `is_recurring`, `recurrence_pattern` — Plus+ recurring billing

#### User Model
- **Present and correct**: Most fields align (email, employee_number, status, MFA fields, failed_login_count)
- **Check**: `person` FK relationship — service03 has it correctly

### 3.6 MISSING: Background Tasks (Background Tasks Spec V2)

**Severity: MEDIUM — Celery configured but no tasks defined**

Service03 has Celery installed and configured, but no actual task implementations. The spec defines 12+ background tasks:

| Required Task | Status |
|---|---|
| `update_overdue_invoices` | **MISSING** |
| `update_overdue_vendor_bills` | **MISSING** |
| `process_agreement_expirations` | **MISSING** |
| `check_vehicle_maintenance_due` | **MISSING** |
| `check_employee_certification_expiry` | **MISSING** |
| `update_stock_levels` | **MISSING** |
| `process_communication_triggers` | **MISSING** |
| `generate_usage_snapshots` | **MISSING** |
| `cleanup_expired_sessions` | **MISSING** |
| `process_scheduled_reports` | **MISSING** |
| `check_trial_expirations` | **MISSING** |
| `rotate_audit_logs` | **MISSING** |

**Note**: All tasks that change entity statuses must use `execute_transition()` per Lifecycle Framework mandate.

### 3.7 MISSING: Internal REST API (Internal API Spec V1)

**Severity: MEDIUM — Routing exists but empty**

Service03 has the URL routing (`/internal/api/v1/`) and key authentication middleware, but no endpoints are implemented. This is intentional per the stabilization scope, but will be needed for SDP ↔ SDTA communication.

### 3.8 MISSING: Email Specification (Email Spec)

**Severity: LOW (for initial launch) — Template system needed**

Service03 has `EmailDeliveryLog` but no email template rendering, sending service, or provider integration.

### 3.9 MISSING: Dashboard Counters (Dashboard Counters Spec)

**Severity: LOW — UX feature, not core**

No dashboard counter queries or views implemented.

### 3.10 MISSING: Value Lists / Custom Fields

Service03 has no value list or custom field infrastructure. The Desktop Version has a `value_lists` app with ValueList and ValueListItem models.

---

## 4. Desktop Version — Components to Pull Over

The Desktop Version is the original codebase being migrated to SaaS. These components should be adapted (not copied verbatim) for service03:

### 4.1 Numbering System (CRITICAL — Pull and Adapt)

**Location:** `Desktop Version/numbering/`

**Models to adapt:**
- `NumberingRule` — Defines formatting per entity type (prefix, year, delimiter, reset)
- `NumberSequence` — Atomic counter with `SELECT FOR UPDATE`
- `AssignedNumber` — Immutable audit record (save/delete raise ValidationError)

**Service functions to adapt:**
- `generate_number(tenant_id, entity_type, user_display)` — Format a new number
- `assign_number(tenant_id, entity_type, entity_id, user_display)` — Assign and record
- `get_next_sequence_value(rule)` — Atomic increment
- `check_reset_needed(sequence)` — Yearly/monthly reset logic
- `format_number(rule, sequence_value)` — Configurable formatting

**Adaptation needed:**
- Ensure models extend TenantModel (NumberingRule, AssignedNumber) or use FK scoping (NumberSequence)
- Add RLS policies for NumberingRule and AssignedNumber
- Implement reverse-alphabet year encoding for InventoryItem prefix (Z=1, Y=2, X=3, W=4, V=5, U=6, T=7, S=8, R=9, Q=0)
- Wire into entity model `save()` methods via NumberingMixin
- Replace all SequenceTracker references

### 4.2 Lifecycle Framework (CRITICAL — Pull and Adapt)

**Location:** `Desktop Version/lifecycle/`

**Models to adapt:**
- `LifecycleStateDef` — Registers allowed states (normal/locked/final types)
- `LifecycleTransitionRule` — Defines allowed transitions with role gating
- `LifecycleTransitionAudit` — Immutable transition log

**Service functions to adapt:**
- `execute_transition(entity, to_state, user, reason, ip_address)` — THE central function for all status changes
- `get_available_transitions(entity, user)` — Role-aware next states
- `get_transition_history(entity_type, entity_id, tenant_id)` — Audit query

**Adaptation needed:**
- Ensure models extend TenantModel
- Add RLS policies
- Wire into all entity models that have status fields (31 entity types per System Status V3)
- Seed states and transitions during provisioning (per Seed Data V2 Section 5a)
- Update all background tasks to use `execute_transition()` instead of direct status writes

### 4.3 Notes & Documents (CRITICAL — Pull and Adapt)

**Location:** `Desktop Version/notes/` and `Desktop Version/documents/`

**Models to adapt:**
- `Note` — 25 nullable parent FKs, exclusive arc, note_type enum
- `Document` — 25 nullable parent FKs, exclusive arc, scan_status enum

**Adaptation needed:**
- Ensure models extend TenantModel
- Add exclusive arc CHECK constraints at database level
- Add partial indexes per parent FK
- Integrate with File Upload system for Document

### 4.4 Core Base Model (REVIEW — Compare Patterns)

**Location:** `Desktop Version/core/`

The Desktop Version's `BaseModel` includes:
- UUID PK, timestamps (immutable created_at, mutable updated_at), user attribution
- Soft-delete via `is_active` flag

**Decision needed:** Service03's TenantModel does NOT have `is_active` (soft delete). The specs do not mandate soft delete globally. Some entities have status fields that serve a similar purpose (e.g., Customer status = Closed). Recommend: Do NOT add global soft delete unless specs change — it adds query complexity.

### 4.5 Audit System (COMPARE — Desktop Version has signal-based capture)

The Desktop Version uses Django signals to auto-capture model changes into UserTransaction records. Service03 has SystemAudits but captures them manually in TenantModelAdmin.

**Recommendation:** The signal-based approach from Desktop Version is more comprehensive (catches all saves, not just admin actions). Consider adopting for service03, but validate against the specs — the specs don't mandate signal-based capture.

### 4.6 File Storage (Pull pattern)

**Location:** `Desktop Version/files/`

Deterministic path generation: `{entity_type}/{entity_id}/{file_id}` — matches File Upload Spec V1.

### 4.7 Value Lists (Pull and Adapt)

**Location:** `Desktop Version/value_lists/`

ValueList and ValueListItem models for customizable dropdowns. Service03 is missing this entirely. Multiple specs reference "customizable dropdown" fields (asset categories, lead sources, etc.) that need this infrastructure.

---

## 5. Reference Codebase Patterns to Adopt

### 5.1 From Django-CRM-master

| Pattern | What It Is | Adopt? |
|---|---|---|
| OrgScopedModel/Manager/QuerySet | Base model with auto-filtering | Already in service03 as TenantModel/TenantManager |
| User/Profile separation | User has multiple org profiles | Not needed — SDTA is single-tenant-per-user |
| Generic Comment system | ContentType-based polymorphic comments | **NO** — SDTA uses exclusive arc pattern instead (Note model with 25 FKs) |
| Generic Attachment system | ContentType-based file attachments | **NO** — SDTA uses exclusive arc pattern (Document model with 25 FKs) |
| Activity audit trail | Track all entity events | **REVIEW** — SystemAudits covers this; may want Activity model for user-facing timeline |
| JWT + API Key auth | REST API authentication | **FUTURE** — When REST API is built for tenant users (currently admin-only) |
| RLS middleware pattern | SET LOCAL org context | Already in service03 — very similar implementation |

### 5.2 From KoalixCRM-master

| Pattern | What It Is | Adopt? |
|---|---|---|
| Document hierarchy (SalesDocument → Invoice, Quote, PO) | Shared base for financial docs | **NO** — SDTA keeps these as separate models per Data Models V6 |
| GL accounting integration (Booking model) | Journal entries from business docs | **FUTURE** — Pro/Enterprise tier accounting (Ledger model exists in service03) |
| Product + Unit + UnitTransform | UOM conversions | **NO** — SDTA products don't need UOM conversion in current specs |
| Line item system (SalesDocumentPosition) | Shared line item base | **REVIEW** — SDTA has separate line item models (QuoteLine, InvoiceLine, etc.) per spec |
| Customer billing cycles | Recurring billing support | **FUTURE** — Agreement/CustomerAgreement models handle this |

### 5.3 From files/ Reference Templates

| Pattern | What It Is | Adopt? |
|---|---|---|
| StaffUser + Worker DB alias | Non-tenant admin access | **Already in service03** — directly adopted |
| TenantModel abstract base | Auto-populates tenant_id on save | **Already in service03** — directly adopted |
| TenantManager auto-filtering | Per-request query scoping | **Already in service03** — directly adopted |
| Middleware pipeline order | AdminBypass before TenantMiddleware | **Already in service03** — directly adopted |
| Thread-local tenant context | async-safe per-request isolation | **Already in service03** — directly adopted |
| StaffUserBackend | Separate auth for staff | **Already in service03** — directly adopted |

**Conclusion:** The `files/` templates were the architectural foundation for service03. They are fully adopted.

---

## 6. Patterns to Keep in Service03

These architectural patterns are correct and should be preserved through all future work:

1. **TenantModel + TenantManager** — The base for every tenant-scoped model
2. **Dual DB aliases** (default + worker) — RLS isolation for app, bypass for admin/migrations
3. **Dual user model** (StaffUser + User) — Clean separation of platform ops vs. tenant employees
4. **Middleware ordering** — AdminBypass before TenantMiddleware is critical
5. **`SET LOCAL app.current_tenant_id`** — Transaction-scoped, PgBouncer-safe
6. **UUIDv4 primary keys** on all models — matches spec mandate
7. **`all_objects` manager** — Unfiltered access for background tasks/admin
8. **SDTATestCase base class** — Real PostgreSQL testing with tenant context
9. **Factory helpers** (make_person, make_customer, etc.) — Extend as new models are added
10. **Immutable audit models** (SystemAudits, future AssignedNumber, LifecycleTransitionAudit) — save/delete raise ValidationError

---

## 7. Implementation Task List

Ordered by dependency and priority. Each task references the relevant specification.

### Phase 1: Core Frameworks (Must Complete First — Everything Depends on These)

#### Task 1.1: Implement Numbering Service
**Spec:** Numbering Service Specification V1
**Source:** Desktop Version `numbering/` app
**Steps:**
1. Create `numbering` Django app in service03
2. Implement `NumberingRule` model (extends TenantModel)
3. Implement `NumberSequence` model (FK to NumberingRule, NOT TenantModel)
4. Implement `AssignedNumber` model (extends TenantModel, immutable — save/delete raise ValidationError)
5. Implement service functions: `generate_number()`, `assign_number()`, `get_next_sequence_value()`, `check_reset_needed()`, `format_number()`
6. Implement `NumberingMixin` for entity models
7. Implement reverse-alphabet year encoding for InventoryItem prefix
8. Write RLS policies for NumberingRule and AssignedNumber
9. Write migrations
10. Write tests (collision-free concurrency, reset behavior, immutability, encoding)
11. Remove/deprecate SequenceTracker from infrastructure app

#### Task 1.2: Implement Lifecycle Framework
**Spec:** Lifecycle Framework Specification V1 + System Status Specification V3
**Source:** Desktop Version `lifecycle/` app
**Steps:**
1. Create `lifecycle` Django app in service03
2. Implement `LifecycleStateDef` model (extends TenantModel)
3. Implement `LifecycleTransitionRule` model (extends TenantModel)
4. Implement `LifecycleTransitionAudit` model (extends TenantModel, immutable)
5. Implement service functions: `execute_transition()`, `get_available_transitions()`, `get_transition_history()`
6. Implement exceptions: TransitionDeniedError, PermissionDeniedError, ReasonRequiredError, FinalStateError
7. Write RLS policies
8. Write migrations
9. Write tests (deny-by-default, role gating, final states, audit immutability)

#### Task 1.3: Implement Note & Document Models
**Spec:** Note & Document Implementation Specification V1
**Source:** Desktop Version `notes/` and `documents/` apps
**Steps:**
1. Create `notes` Django app in service03 (or add to existing app)
2. Implement `Note` model with 25 parent FKs, exclusive arc CHECK constraint
3. Implement `Document` model with 25 parent FKs, exclusive arc CHECK constraint, scan_status
4. Add `clean()` validation for exclusive arc
5. Add partial indexes per parent FK
6. Write RLS policies
7. Write migrations
8. Write tests (exclusive arc enforcement, scan status transitions)

### Phase 2: Model Alignment (Fix Service03 Models to Match Specs)

#### Task 2.1: Rename Product to InventoryItem
**Spec:** Data Models V6
**Steps:**
1. Rename `inventory/models.py` `Product` class to `InventoryItem`
2. Update `db_table` meta if needed (or let Django handle)
3. Update all FK references across all apps (WorkOrderLine, QuoteLine, InvoiceLine, etc.)
4. Update all admin registrations
5. Update all test files and factory helpers
6. Update numbering entity_type key from `product` to `inventory_item`
7. Verify all imports and string references

#### Task 2.2: Add Missing Model Fields
**Spec:** Data Models V6 + System Status V3
**Steps:**
1. **Customer**: Add `hold_date`, `hold_reason`, `closed_at`, `closed_reason`
2. **WorkOrder**: Add `hold_date`, `hold_reason`, `customer_facing_notes`, `recurrence_pattern`
3. **Invoice**: Add `stripe_payment_link_url`, `deposit_applied`, `deposit_type`, `deposit_amount`, `is_recurring`, `recurrence_pattern`
4. **Vendor**: Add `Do Not Use` to status choices
5. **Quote**: Add `deposit_required`, `deposit_type`, `deposit_amount` (Plus+)
6. **All entities with status**: Ensure status choices align exactly with System Status V3 enum values
7. Write migrations for all field additions

#### Task 2.3: Add Missing Status Values
**Spec:** System Status Specification V3
**Steps:**
1. Audit every model's status choices against the corresponding System Status V3 section
2. Update choices tuples to match exactly
3. Ensure LifecycleStateDef seeds will match these values

#### Task 2.4: Wire Numbering into Entity Models
**Spec:** Numbering Service V1 Section 5
**Steps:**
1. Add `NumberingMixin` to all numbered entity models (21 entity types)
2. Set `numbering_entity_type` on each model
3. Update `save()` or creation logic to call `assign_number()` on first save
4. Verify entity number fields match spec naming (e.g., `wo_number`, `invoice_number`, `customer_number`)

#### Task 2.5: Wire Lifecycle into Entity Models
**Spec:** Lifecycle Framework V1 + System Status V3
**Steps:**
1. Replace all direct `status = 'new_value'` assignments with `execute_transition()` calls
2. Add lifecycle entity_type constant to each entity model
3. Update views/admin to use `get_available_transitions()` for status dropdowns
4. Verify all 31 entity types have corresponding System Status V3 lifecycles seeded

### Phase 3: Provisioning & Seed Data

#### Task 3.1: Update Tenant Provisioning
**Spec:** Tenant Provisioning Seed Data V2
**Steps:**
1. Update provisioning flow to create NumberingRule + NumberSequence records (Section 5)
2. Update provisioning flow to create LifecycleStateDef + LifecycleTransitionRule records (Section 5a)
3. Implement reverse-alphabet year encoding for InventoryItem prefix at provisioning time
4. Ensure all 21 numbered entity types get NumberingRule seeds
5. Ensure all 31 lifecycle entity types get state/transition seeds from System Status V3
6. Seed the 3 immutable system roles: Read-Only, Worker, Administrator (Section 3)
7. Seed OnboardingState steps (Section 6)
8. Write tests for provisioning flow

#### Task 3.2: Implement Value Lists
**Spec:** Top-Down Specifications V4 (customizable dropdowns)
**Source:** Desktop Version `value_lists/` app
**Steps:**
1. Create `value_lists` Django app
2. Implement `ValueList` model (name, entity_type, is_system)
3. Implement `ValueListItem` model (FK to ValueList, label, value, sort_order, is_active)
4. Seed default value list items during provisioning
5. Wire into models that reference "customizable dropdown" fields

### Phase 4: File Storage & Integration

#### Task 4.1: Implement File Upload System
**Spec:** File Upload Specification V1
**Steps:**
1. Configure Django storage backend for S3/DigitalOcean Spaces
2. Implement deterministic path generation: `{entity_type}/{entity_id}/{file_id}`
3. Implement pre-signed URL generation for uploads and downloads
4. Implement `FileUploadLog` and `FileDownloadLog` models
5. Implement file scan/quarantine workflow (scan_status: Pending → Clean/Infected)
6. Wire into Document model

#### Task 4.2: Implement Background Tasks
**Spec:** Background Tasks Specification V2
**Steps:**
1. Implement all 12+ Celery tasks defined in spec
2. Ensure ALL status-changing tasks use `execute_transition()` — not direct writes
3. Configure Celery beat schedules per spec
4. Write tests for each task

#### Task 4.3: Implement Internal REST API
**Spec:** Internal API Specification V1
**Steps:**
1. Define endpoint contracts for SDP ↔ SDTA communication
2. Implement serializers
3. Implement views with InternalAPIKeyMiddleware protection
4. Write tests

### Phase 5: Polish & Verification

#### Task 5.1: RLS Policy Audit
**Steps:**
1. Verify every new model (NumberingRule, AssignedNumber, LifecycleStateDef, etc.) has RLS policies
2. Update `setup_rls.sql` with all new tables
3. Run manual RLS verification per Production Parity Checklist

#### Task 5.2: Cross-Spec Consistency Verification
**Steps:**
1. Run the same cross-spec audit methodology used on the design docs
2. Verify every entity_type key is consistent across Numbering, Lifecycle, Provisioning, and Models
3. Verify every status enum value is consistent across System Status V3, LifecycleStateDef seeds, and model choices
4. Verify every prefix is consistent across Numbering, Seed Data, and TenantPreference

#### Task 5.3: Test Coverage Expansion
**Steps:**
1. Add tests for Numbering Service (concurrency, reset, immutability, encoding)
2. Add tests for Lifecycle Framework (deny-by-default, role gating, final states, audit)
3. Add tests for Note/Document exclusive arc
4. Add tests for provisioning flow
5. Add integration tests for status change → lifecycle audit → numbering assignment flow

---

## 8. Migration Strategy from SequenceTracker

The Numbering Service replaces SequenceTracker. The migration must be handled carefully:

1. **New tenants**: Provisioning creates NumberingRule + NumberSequence directly (no SequenceTracker)
2. **Existing tenants** (if any exist in service03): Data migration script to:
   - Create NumberingRule from SequenceTracker.prefix + TenantPreference settings
   - Create NumberSequence with `current_value = SequenceTracker.last_value`
   - Backfill AssignedNumber records from existing entity number fields (optional — for audit completeness)
3. **SequenceTracker model**: Keep in codebase temporarily with deprecation note; remove after migration verified
4. **Tests**: Update test_infrastructure.py to test NumberingService instead of SequenceTracker

---

## 9. File-Level Impact Map

Which service03 files need changes, organized by type of change:

### New Files to Create

| File | App | Purpose |
|---|---|---|
| `numbering/models.py` | numbering (new) | NumberingRule, NumberSequence, AssignedNumber |
| `numbering/services.py` | numbering (new) | generate_number, assign_number, format_number, etc. |
| `numbering/admin.py` | numbering (new) | Admin registration |
| `numbering/apps.py` | numbering (new) | App config |
| `numbering/mixins.py` | numbering (new) | NumberingMixin |
| `lifecycle/models.py` | lifecycle (new) | LifecycleStateDef, LifecycleTransitionRule, LifecycleTransitionAudit |
| `lifecycle/services.py` | lifecycle (new) | execute_transition, get_available_transitions, etc. |
| `lifecycle/admin.py` | lifecycle (new) | Admin registration |
| `lifecycle/apps.py` | lifecycle (new) | App config |
| `lifecycle/exceptions.py` | lifecycle (new) | TransitionDeniedError, etc. |
| `notes/models.py` | notes (new) | Note model with 25 FKs |
| `documents/models.py` | documents (new) | Document model with 25 FKs |
| `value_lists/models.py` | value_lists (new) | ValueList, ValueListItem |
| `files/models.py` | files (new) | FileUploadLog, FileDownloadLog |
| `files/services.py` | files (new) | S3 upload, pre-signed URL generation |

### Files to Modify

| File | Change |
|---|---|
| `config/settings.py` | Add new apps to INSTALLED_APPS |
| `inventory/models.py` | Rename Product → InventoryItem, add NumberingMixin |
| `crm/models.py` | Add missing fields (hold_date, hold_reason, closed_at, closed_reason on Customer), add NumberingMixin |
| `service/models.py` | Add missing fields on WorkOrder and Invoice, add NumberingMixin to all |
| `procurement/models.py` | Add Do Not Use status to Vendor, add NumberingMixin |
| `maintenance/models.py` | Add NumberingMixin to Asset |
| `tasks/models.py` | Add NumberingMixin to Task |
| `workforce/models.py` | Add NumberingMixin to WorkGroup |
| `fleet/models.py` | Add NumberingMixin to Vehicle |
| `infrastructure/models.py` | Deprecate SequenceTracker |
| `scripts/setup_rls.sql` | Add RLS policies for all new tables |
| `tests/base.py` | Add factory helpers for new models |
| All `tests/test_*.py` | Update for renamed models, new lifecycle/numbering behavior |

---

## 10. Cross-Reference: Spec → Code Mapping

| Specification | Primary Service03 App(s) | Status |
|---|---|---|
| Data Models V6 | All apps | Partial — field mismatches, missing Note/Document |
| Technical Architecture V2 | config/ | Complete |
| Database Specification V2 | config/, scripts/ | Complete |
| Multi-Tenancy Spec V1 | config/base_models.py, config/middleware.py | Complete |
| Lifecycle Framework V1 | **MISSING** → lifecycle/ (new) | Not started |
| Numbering Service V1 | **MISSING** → numbering/ (new) | Not started |
| Note & Document V1 | **MISSING** → notes/, documents/ (new) | Not started |
| File Upload V1 | **MISSING** → files/ (new) | Not started |
| System Status V3 | All entity apps (status fields) | Partial — values exist but no enforcement |
| Background Tasks V2 | **MISSING** → automation/ or tasks/ (new) | Celery configured, no tasks |
| Internal API V1 | infrastructure/internal_urls.py | Routing exists, no endpoints |
| Security Features Spec | config/, staff/ | Complete |
| Permission Management Spec | users/ (RolePermission) | Model exists, enforcement not wired |
| Seed Data V2 | infrastructure/ (provisioning) | Partial — SequenceTracker seeding exists |
| Product Tier Map V2 | infrastructure/ (TenantAddOn) | Model exists |
| Top-Down Specifications V4 | All apps | Reference only — implementation varies |
| Pricing & Billing V3 | infrastructure/ (usage trackers) | Models exist |
| Email Specification | infrastructure/ (EmailDeliveryLog) | Model exists, no sending service |
| Dashboard Counters Spec | **MISSING** | Not started |
| Stripe Webhooks Spec | infrastructure/ (Stripe models) | Models exist, no webhook processing |
| Universal Query Spec | **MISSING** | Not started |
| Invoice Calculations Spec | service/ (Invoice) | Partial — basic calculations |
| Onboarding Triggers Spec | infrastructure/ (OnboardingState) | Model exists |
| Lite MVP V4 | All apps | Guides feature scope |
| SaaS Operational Plan | infrastructure/ | Architecture reference |

---

## 11. Estimated Effort

| Phase | Tasks | Estimated Effort |
|---|---|---|
| Phase 1: Core Frameworks | Numbering, Lifecycle, Notes/Docs | High — foundational, must be right |
| Phase 2: Model Alignment | Rename, add fields, wire mixins | Medium — mostly mechanical |
| Phase 3: Provisioning | Seed data, value lists | Medium — depends on Phase 1 |
| Phase 4: Integration | File storage, background tasks, API | High — many moving parts |
| Phase 5: Verification | RLS, cross-spec audit, tests | Medium — quality assurance |

**Critical path:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

Phases 1.1, 1.2, and 1.3 can be developed in parallel since they are independent Django apps. Phase 2 depends on Phase 1 (numbering and lifecycle must exist before wiring into models). Phase 3 depends on Phases 1 and 2. Phase 4 depends on Phase 3 (background tasks need lifecycle to be in place). Phase 5 runs last.

---

*Generated from comprehensive audit of all codebases in Code to Review/ against 30 design specification documents in Design Information/Design Documents/*
