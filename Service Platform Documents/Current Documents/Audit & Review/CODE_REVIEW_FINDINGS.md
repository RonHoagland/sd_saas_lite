# Code to Review — Deep Dive Findings & ServizDesk Reusability Assessment

**Date:** March 28, 2026
**Purpose:** Evaluate 7 legacy projects for code, patterns, and ideas reusable in the ServizDesk build (SDP + SDTA).

---

# Executive Summary

Seven projects were reviewed. They represent an evolution from a single-tenant desktop prototype through several multi-tenant iterations to the current SDTA architecture. The two most valuable projects are **service03** (latest SDTA iteration — 80+ models, full test suite, production-grade multi-tenancy) and **Desktop Version** (mature single-tenant app with reusable infrastructure patterns). Two third-party open-source projects (Django-CRM-master, koalixcrm-master) offer reference patterns worth studying but contain no directly portable code.

**Bottom line:** service03 is your current SDTA codebase. The files/service02 pair are its infrastructure backbone. service01 is an earlier iteration that service03 supersedes. Desktop Version contains standalone utility modules (numbering, lifecycle, backup, audit) that could be adapted. The two open-source CRMs are reference material only.

---

# Project Inventory

| Project | Type | Stack | Models | Multi-Tenant | ServizDesk Relevance |
|---------|------|-------|--------|-------------|---------------------|
| **service03** | SDTA (latest) | Django 6.x, PostgreSQL, Celery | 80+ | Yes (RLS + TenantModel) | **PRIMARY — This IS the current SDTA** |
| **files** | SDTA infrastructure | Django, PostgreSQL | 1 (StaffUser) | Yes (RLS core) | **HIGH — Core multi-tenancy layer** |
| **service02** | SDTA infrastructure (older) | Django, PostgreSQL | 1 (StaffUser) | Yes (RLS core) | **DUPLICATE of files** (different DB defaults) |
| **service01** | SDTA (early iteration) | Django 5.x, PostgreSQL | 17 | Yes (contextvars) | **SUPERSEDED by service03** |
| **Desktop Version** | Single-tenant prototype | Django, PostgreSQL | 20+ | No | **MEDIUM — Utility modules reusable** |
| **Django-CRM-master** | Open-source CRM (BottleCRM) | Django 5.x + SvelteKit | 30+ | Yes (RLS) | **REFERENCE ONLY — Different domain** |
| **koalixcrm-master** | Open-source CRM | Django, XSL-T/FOP | 70+ | No | **REFERENCE ONLY — Invoicing patterns** |

---

# Section 1: service03 — The Current SDTA Codebase

## Status: THIS IS YOUR PRODUCTION CODEBASE

service03 is not "old code to review" — it is the most current implementation of the SDTA specification. It maps directly to **Data Models V6**, **Multi-Tenancy V1**, **Database Spec V2**, **Security V1**, and **Technical Architecture V2**.

### Spec Coverage Assessment

| ServizDesk Spec Area | service03 Coverage | Status |
|---------------------|-------------------|--------|
| **CRM (Customer, Person, Contact, Address, Phone, Social)** | Full Lite tier models present | COMPLETE |
| **Assets & SubAssets** | Asset + SubAsset models present | COMPLETE |
| **Service Requests** | Full model with status lifecycle | COMPLETE |
| **Work Orders + Team + Lines** | Full model with team/line children | COMPLETE |
| **Quotes & QuoteLines** | Full model with asset junction | COMPLETE |
| **Invoices & InvoiceLines** | Full model with asset junction + WO junction | COMPLETE |
| **Payments & Banking** | Payment, Bank, Accounting, Ledger models | COMPLETE |
| **Tasks & Time Entries** | Task, AssociatedTask, TaskTime, TaskToDo, TimeEntry | COMPLETE |
| **Products & KitItems** | Full catalog with price history, pricebooks | COMPLETE |
| **Vendors & Procurement** | Vendor, PO, PO Lines, Receiving, LotInfo, VendorBill, Requisition | COMPLETE |
| **Warehouses & Inventory** | Warehouse, SubLocation, LocationAssignedInventory, Count, Transfer | COMPLETE |
| **Workforce (WorkGroups)** | WGDivision, WorkGroup, WGTRole, WorkGroupTeam, WorkGroupAsset | COMPLETE |
| **Fleet / Vehicles** | Vehicle, VehicleMaintenance, MileageLog, VehicleInventory | COMPLETE |
| **Automation** | CommunicationTrigger, CommunicationTemplate, TriggerTemplate, TriggerLog | COMPLETE |
| **Users & Roles** | User, Department, Position, Role, EmployeeRole, RolePermission | COMPLETE |
| **Tenant Preferences** | TenantPreference with all numbering prefixes | COMPLETE |
| **Leads (Plus+)** | Lead model with status lifecycle | COMPLETE |
| **Opportunities (Pro+)** | Opportunity + OpportunityContacts | COMPLETE |
| **Multi-Tenancy** | TenantModel + TenantManager + TenantMiddleware + RLS | COMPLETE |
| **Dual DB Roles** | default (sdta_app/RLS) + worker (sdta_migration/BYPASSRLS) | COMPLETE |
| **Staff Admin** | StaffUser + StaffUserBackend + TenantModelAdmin | COMPLETE |
| **Audit Trail** | SystemAudits + SessionLog + LoginAttemptLog + NavigationAudit | COMPLETE |
| **Infrastructure** | TenantState, TenantAddOn, SubdomainIndex, SequenceTracker | COMPLETE |
| **Stripe Integration** | StripeConnection, StripeResponse, StripeLog + webhook/API logs | COMPLETE |
| **Notifications** | Notification model | COMPLETE |
| **Onboarding** | OnboardingState model | COMPLETE |
| **Usage Tracking** | StorageTracker, EmailUsageTracker, SMSUsageTracker | COMPLETE |

### What's Missing from service03 (vs. full spec suite)

| Spec Area | Gap | Spec Reference |
|-----------|-----|----------------|
| **Agreements & PM** | Models exist but limited coverage | Top-Down V4 Section 2 |
| **WorkFlow / SOP** | Not yet implemented (Pro/Enterprise) | Top-Down V4 Section 1.19 |
| **Equipment Entity** | Not yet implemented (Pro/Enterprise) | Top-Down V4 Section 1.22 |
| **SafetyForm Entity** | Not yet implemented (Pro/Enterprise) | Top-Down V4 Section 1.23 |
| **Note/Document Attachments** | Not visible in service03 models | Data Models V6 Section 1.8 |
| **Universal Query** | Not yet implemented | Universal Query V1 |
| **Email Spec** | EmailDeliveryLog exists but no full email flow | Email Spec V1 |
| **Background Tasks** | Celery configured but task functions empty | Background Tasks V2 |
| **API Views / Serializers** | Admin only — no DRF endpoints yet | Tech Architecture V2 |
| **HTMX Frontend** | Not started | Tech Architecture V2 |

### Recommendation

service03 is the starting point for the SDTA build. It has the data layer and multi-tenancy infrastructure. The next development phases are:

1. **API/View layer** — Django views with HTMX (per Tech Architecture V2)
2. **Background tasks** — Celery task implementations (per Background Tasks V2)
3. **Note/Document models** — Exclusive arc attachment pattern (per Data Models V6 Section 1.8)
4. **Pro/Enterprise entities** — WorkFlow, Equipment, SafetyForm
5. **Frontend** — Tailwind + HTMX templates

---

# Section 2: files / service02 — SDTA Infrastructure Core

## Status: BACKBONE OF service03

These two projects contain the identical multi-tenancy infrastructure that service03 builds on. They are **not separate projects** — they are the core infrastructure layer (tenant_context.py, base_models.py, middleware.py, backends.py, admin.py, settings.py, celery.py) extracted or duplicated.

### Key Difference Between the Two

| Setting | files (newer) | service02 (older) |
|---------|--------------|-------------------|
| DB name default | `servizdesk_sdta` | `serviz_db` |
| App DB user | `sdta_app` | `djangouser` |
| Worker DB user | `sdta_migration` | `djangouser` |

**files** uses the correct role separation per **Database Spec V2** (sdta_app for RLS, sdta_migration for BYPASSRLS). service02 uses the same user for both, which defeats the purpose of the worker alias.

### Reusable Patterns (Already In Use)

These patterns from files/service02 are already incorporated into service03:

- **TenantModel abstract base** — UUID PK, tenant_id, audit fields, TenantManager
- **TenantManager** — Auto-filters querysets by current tenant context
- **TenantMiddleware** — Sets Python context + PostgreSQL `SET LOCAL app.current_tenant_id`
- **AdminBypassMiddleware** — Placeholder for admin path handling
- **InternalAPIKeyMiddleware** — Bearer token validation for `/internal/api/` paths
- **StaffUserBackend** — Separate authentication path for Django admin staff
- **TenantModelAdmin** — Admin base class using 'worker' DB alias (BYPASSRLS)
- **Dual DATABASES config** — default (RLS) + worker (BYPASSRLS)

### Recommendation

These can be archived. Their code lives in service03. Keep **files** as the canonical reference if you need to trace the infrastructure design decisions.

---

# Section 3: service01 — Early SDTA Prototype

## Status: SUPERSEDED BY service03

service01 was an earlier iteration with 5 apps (crm, inventory, service, users, infrastructure). service03 expanded this to 12 apps with 80+ models. Everything useful from service01 has been carried forward.

### What service01 Had That service03 Improved

| Feature | service01 | service03 |
|---------|-----------|-----------|
| Tenant context | `contextvars.ContextVar` | `asgiref.local.Local()` (async-safe) |
| Asset hierarchy | `parent_asset` self-FK | SubAsset junction table |
| Apps | 5 (crm, inventory, service, users, infrastructure) | 12+ full coverage |
| Tests | Infrastructure isolation only | 14 test files, 150+ model tests |
| Admin | Basic ModelAdmin | TenantModelAdmin with audit + group permissions |
| Management commands | `create_tenant_admin` | Same + stabilization tooling |

### One Notable Pattern from service01

**TroubleCall model** — service01 had a dedicated `TroubleCall` entity as the intake/triage step before a WorkOrder. In service03, this became `ServiceRequest`. The TroubleCall concept (source, urgency, triage_notes, conversion to WO) maps well to the ServiceRequest spec in Top-Down V4 Section 1.3.

### Recommendation

Archive. service03 supersedes everything here. The `contextvars` approach in service01 was replaced with the superior `asgiref.local.Local()` in service03 for async safety.

---

# Section 4: Desktop Version — Single-Tenant Prototype

## Status: UTILITY MODULES WORTH ADAPTING

The Desktop Version is a mature single-tenant Django application with 23 apps. It has no multi-tenancy, but contains several well-built infrastructure modules that could be adapted for SDTA.

### Directly Reusable Modules

#### 4.1 Numbering Service (HIGH VALUE)

**Source:** `numbering/models.py`, `numbering/utils.py`
**ServizDesk Spec:** Data Models V6 — SequenceTracker

The Desktop Version has a sophisticated numbering system that is MORE feature-rich than service03's SequenceTracker:

| Feature | Desktop Version | service03 (SequenceTracker) |
|---------|----------------|---------------------------|
| Configurable prefix | Yes | Yes |
| Year/month inclusion | Yes (YYYY or YY + optional month) | Manual via prefix |
| Reset behavior | None / yearly / monthly | Not implemented |
| Sequence padding | Configurable length | pad_length field |
| Atomic generation | SELECT FOR UPDATE | Not shown |
| Assignment tracking | AssignedNumber model (immutable audit) | Not present |
| NumberingMixin | Model convenience methods | Not present |
| Custom format | `custom_format` field | Not present |
| Delimiter | Configurable | Not present |

**Recommendation:** Adapt the Desktop Version's NumberingRule + NumberSequence + AssignedNumber pattern into SDTA. The reset behavior (yearly/monthly) and assignment tracking add significant value over the current SequenceTracker. The atomic `SELECT FOR UPDATE` pattern is production-critical for concurrent number generation. Would need to add `tenant_id` to make it multi-tenant.

#### 4.2 Lifecycle / State Machine Framework (HIGH VALUE)

**Source:** `lifecycle/models.py`
**ServizDesk Spec:** System Status Specification V3

The Desktop Version implements a generic, data-driven state machine framework:

- **LifecycleStateDef** — Registers allowed states per entity type (normal, locked, final). Single default enforced per entity.
- **LifecycleTransitionRule** — Defines allowed transitions with required_permission and requires_reason flags. Self-transitions blocked. Deny-by-default policy.
- **LifecycleTransitionAudit** — Immutable log of every state change (who, when, from→to, reason, override flag).

service03 currently uses CharField with TextChoices for status fields — there is no enforcement of valid transitions at the model level. The Desktop Version's lifecycle framework would add:

- **Transition validation** — Only allowed transitions can execute
- **Permission gating** — Transitions can require specific permissions
- **Reason tracking** — Transitions can require justification
- **Audit trail** — Every state change logged immutably
- **Admin-configurable** — States and transitions defined in data, not code

**Recommendation:** This is the strongest candidate for adaptation. It directly implements what System Status V3 specifies for Customer, Asset, WorkOrder, Invoice, etc. status lifecycles. Add `tenant_id` to LifecycleStateDef and LifecycleTransitionRule (system-level defaults + tenant overrides for Pro/Enterprise). LifecycleTransitionAudit should be tenant-scoped.

#### 4.3 Audit Framework (MEDIUM VALUE)

**Source:** `audit/models.py`, `audit/middleware.py`
**ServizDesk Spec:** Data Models V6 — SystemAudits, SessionLog, LoginAttemptLog

The Desktop Version has a three-layer audit system:

- **Session** — Created on every login attempt (successful or failed). Tracks: attempted_username, auth_result, failure_reason, client_info, ip_address, user_snapshot (JSON), end_reason (logout/timeout/admin_invalidate).
- **UserTransaction** — Discrete action log per session. Tracks: event_type (create/update/delete), entity_type, entity_id, summary.
- **AuditMiddleware** — Stores current user in thread-local for signal access.

service03 already has SystemAudits, SessionLog, and LoginAttemptLog. However, the Desktop Version's Session model adds some useful fields not in service03:

| Field | Desktop Version | service03 |
|-------|----------------|-----------|
| user_snapshot (JSON at login time) | Yes | permission_snapshot (JSON) |
| auth_failure_reason | Yes | failure_reason |
| end_reason (logout/timeout/admin) | Yes | Not present |
| client_info (browser details) | Yes | browser, os, device_type (separate fields) |

**Recommendation:** service03's audit models are already more granular (separate browser/os/device fields). The `end_reason` field from Desktop Version would be a good addition to SessionLog. The UserTransaction concept (per-action logging within a session) could supplement SystemAudits for richer activity trails, but may be overkill for MVP.

#### 4.4 Backup & Recovery (LOW VALUE — Desktop Only)

**Source:** `backup/models.py`
**ServizDesk Spec:** Not applicable (SaaS backup is infrastructure-level)

The Desktop Version has BackupSettings (singleton config), Backup (metadata + versioning), and BackupLog models. This is a desktop/on-premise pattern. In the SaaS model, backups are handled at the infrastructure layer (PostgreSQL pg_dump, cloud snapshots), not the application layer.

**Recommendation:** Not directly reusable. The Backup model's metadata pattern (app_version, schema_version, database_size, duration tracking) could inform a future DataExportLog enhancement, but this is not a priority.

#### 4.5 Value Lists / Picklists (LOW VALUE)

**Source:** `core/models.py` (Preference, ValueList, ValueListItem)
**ServizDesk Spec:** Top-Down V4 (various dropdowns), Data Models V6

The Desktop Version has a dynamic picklist system (ValueList + ValueListItem) where dropdown options are admin-configurable. service03 currently uses Django TextChoices (code-defined enums) for all status/type fields.

**Recommendation:** The current TextChoices approach is appropriate for Lite tier where options are fixed. For Pro/Enterprise, tenant-configurable dropdowns would add value. The ValueList pattern could be adapted with tenant_id for future custom field support. Not needed for MVP.

#### 4.6 File Storage Infrastructure (LOW VALUE)

**Source:** `files/models.py`
**ServizDesk Spec:** Data Models V6 Section 1.8 (Note, Document)

The Desktop Version has StoredFile (metadata), FileUploadLog, and FileDownloadLog models with deterministic path generation (`{root}/{entity_type}/{entity_id}/{file_id}`). service03 does not yet have Note/Document models.

**Recommendation:** When building the Note/Document attachment system per Data Models V6 Section 1.8, the Desktop Version's StoredFile metadata pattern and deterministic path generation are worth referencing. The FileDownloadLog (immutable audit) is a good security pattern.

#### 4.7 CRM Models (NOT REUSABLE)

The Desktop Version's Client, Person, Contact, Address, Phone, Email, Product models are single-tenant versions of what service03 already has in multi-tenant form. The XOR constraint pattern (Phone/Email can belong to Client OR Contact but not both) is identical to service03's approach.

**Recommendation:** Not reusable — service03 already has the multi-tenant versions.

---

# Section 5: Django-CRM-master (BottleCRM) — Reference Patterns

## Status: REFERENCE ONLY — Different Architecture

BottleCRM is a production-grade open-source CRM with a SvelteKit frontend. It uses Django REST Framework (API-first) rather than Django templates (server-rendered). Its multi-tenancy uses `org_id` instead of `tenant_id`. It is architecturally different from ServizDesk (which uses HTMX + server-rendered templates).

### Patterns Worth Studying

#### 5.1 RLS Implementation (REFERENCE)

**Source:** `RLS_SETUP.md`, `backend/common/middleware/rls_context.py`

BottleCRM's RLS is conceptually identical to ServizDesk's but uses a different session variable (`app.current_org` vs `app.current_tenant_id`). Their RLS policy SQL is well-documented:

```sql
CREATE POLICY org_isolation ON lead
    USING (org_id::text = NULLIF(current_setting('app.current_org', true), ''));
```

The `NULLIF` + `current_setting(..., true)` pattern returns no rows when context is not set — a fail-safe default. This is the same pattern ServizDesk should use.

**Key insight from their setup:** They use `FORCE ROW LEVEL SECURITY` which applies RLS even to the table owner. This prevents accidental bypass. They also document that the application database user MUST be non-superuser (superusers bypass RLS).

**Recommendation:** Reference their `RLS_SETUP.md` when writing ServizDesk's `setup_rls.sql`. Their management command (`manage_rls --status/--verify-user/--test`) is also worth replicating.

#### 5.2 Kanban / Pipeline Pattern (FUTURE REFERENCE)

**Source:** `backend/leads/models.py`, `backend/cases/models.py`, `backend/tasks/models.py`

BottleCRM implements a reusable pipeline/kanban pattern across multiple entities (Leads, Cases, Tasks):

- **Pipeline** — Named container (e.g., "Inbound", "Enterprise"). One default per org.
- **Stage** — Ordered steps within a pipeline. Has: stage_type (open/won/lost), maps_to_status, wip_limit, color, win_probability.
- **Entity** — Has `stage` FK and `kanban_order` (Decimal for drag-drop positioning).

This pattern maps to ServizDesk's future Scheduling & Dispatch features (Top-Down V4 Section 3) and could inform Work Order board views.

**Recommendation:** Not needed for MVP. Worth revisiting for Plus/Pro scheduling board UI.

#### 5.3 Opportunity Line Items & Deal Aging (FUTURE REFERENCE)

BottleCRM's Opportunity model tracks stage aging (days_in_current_stage, green/yellow/red status) and auto-recalculates amount from line items. This maps to ServizDesk's Opportunity entity (Top-Down V4 Section 1.21, Pro+ tier).

**Recommendation:** Reference when building Opportunity features for Pro tier.

#### 5.4 SalesGoal Tracking (NOT APPLICABLE)

BottleCRM has a SalesGoal model with milestone tracking (50%/90%/100% notifications). ServizDesk specs do not include sales goal tracking.

#### 5.5 Generic Attachments via ContentType (DESIGN DECISION)

BottleCRM uses Django's ContentType framework for Comments and Attachments — any model can have comments/attachments via a generic foreign key. ServizDesk's specs use an explicit Exclusive Arc pattern (Note/Document has nullable FKs to each parent type). The explicit approach is safer for RLS (no generic queries that could bypass tenant filtering) and more explicit in the schema.

**Recommendation:** Stick with ServizDesk's Exclusive Arc pattern per Data Models V6 Section 1.8. The ContentType approach is elegant but harder to secure with RLS.

---

# Section 6: koalixcrm-master — Reference Patterns

## Status: REFERENCE ONLY — Different Domain & Stack

KoalixCRM is a mature open-source ERP/CRM focused on invoicing, accounting, and project management. It uses Django admin heavily and generates PDFs via XSL-T + Apache FOP. It is single-tenant and has no multi-tenancy.

### Patterns Worth Studying

#### 6.1 Document Generation Chain (FUTURE REFERENCE)

KoalixCRM implements a document factory pattern where documents chain into each other:

- Quote → Purchase Confirmation → Delivery Note → Invoice → Credit Note
- Each document type inherits from a common SalesDocument base
- Documents carry forward line items, customer references, and terms

This maps conceptually to ServizDesk's Quote → Invoice flow (Top-Down V4 Sections 1.6–1.7). However, ServizDesk's approach is simpler (WorkOrderInvoice junction rather than document inheritance chains).

**Recommendation:** Not directly applicable. ServizDesk's flat model approach is simpler and better suited to the HTMX architecture.

#### 6.2 Pricing Engine with Temporal Validity (FUTURE REFERENCE)

KoalixCRM has a sophisticated pricing engine where prices have valid_from/valid_until dates, currency transforms, unit transforms, and customer-group-specific pricing. This maps to ServizDesk's Pricebook/PricebookEntry models (Pro/Enterprise tier, Data Models V6).

**Recommendation:** Worth studying when building Pricebook features for Pro/Enterprise tier. The temporal validity concept (prices valid within date ranges) is not in the current spec but could add value.

#### 6.3 Double-Entry Accounting (REFERENCE)

KoalixCRM implements true double-entry bookkeeping with a general ledger. ServizDesk has a simpler Accounting + Ledger model in service03. The KoalixCRM pattern is more rigorous (balanced debits/credits per transaction).

**Recommendation:** Reference when building the Accounting module per Top-Down V4 Section 1.17. The current Ledger model in service03 already follows a debit/credit pattern.

#### 6.4 Plugin Architecture (DESIGN INSIGHT)

KoalixCRM uses Django's plugin system to add functionality (e.g., subscriptions module). This demonstrates how to extend a core platform without modifying base code. ServizDesk's TenantAddOn model enables/disables features per tenant, which achieves a similar effect at the configuration level rather than the code level.

**Recommendation:** The add-on/feature-flag approach in service03 (TenantAddOn) is the right pattern for SaaS. Code-level plugins add deployment complexity.

---

# Section 7: Cross-Project Pattern Comparison

## Multi-Tenancy Approaches

| Pattern | service03 (SDTA) | BottleCRM | Desktop Version | service01 |
|---------|-----------------|-----------|-----------------|-----------|
| Isolation layer | TenantModel + RLS | BaseOrgModel + RLS | None | BaseTenantModel + RLS |
| Context storage | asgiref.local.Local() | crum + middleware | N/A | contextvars.ContextVar |
| DB session variable | SET LOCAL app.current_tenant_id | SET app.current_org | N/A | SET LOCAL app.current_tenant_id |
| PgBouncer safe | Yes (SET LOCAL + atomic) | Unclear (SET without LOCAL) | N/A | Yes (SET LOCAL + atomic) |
| Dual DB roles | sdta_app + sdta_migration | crm_user (single) | N/A | djangouser (single) |
| Staff separation | StaffUser (separate model) | Profile.role = ADMIN | Django superuser | Django superuser |
| Manager filtering | TenantManager | OrgScopedManager | N/A | TenantModelManager |

**Winner:** service03. It has the most robust implementation — dual DB roles, SET LOCAL for PgBouncer safety, separate StaffUser model, asgiref.local for async safety.

## Base Model Patterns

| Feature | service03 | Desktop Version | BottleCRM | service01 |
|---------|-----------|-----------------|-----------|-----------|
| UUID PK | Yes | Yes | Yes | Yes |
| created_by | CharField (email) | FK to User | FK to User (via crum) | CharField |
| updated_by | CharField (email) | FK to User | FK to User (via crum) | CharField |
| created_on/at | auto_now_add | auto_now_add | auto_now_add | auto_now_add |
| updated_on/at | auto_now | auto_now | auto_now | auto_now |
| Soft delete | Not present | is_active flag | Not present | Not present |
| Lifecycle state | Not in base | LifecycleModel abstract | Not present | Not present |

**Note:** service03 stores created_by/updated_by as CharField (email string) rather than FK to User. This is intentional — it survives user deletion and doesn't require joins for display. The Desktop Version's FK approach is cleaner for queries but creates cascade/SET_NULL complexity.

## Entity Coverage Comparison

| Entity | service03 | service01 | Desktop Version | Data Models V6 |
|--------|-----------|-----------|-----------------|----------------|
| Customer | Yes | Yes | Client (equivalent) | Yes |
| Person | Yes | Yes | Yes | Yes |
| Contact | Yes | Yes | Yes | Yes |
| Address | Yes | Yes | Yes | Yes |
| Phone | Yes | Yes | Yes | Yes |
| Social | Yes | Yes | No (Email separate) | Yes |
| Asset | Yes | Yes | No (Product only) | Yes |
| SubAsset | Yes | No (parent_asset FK) | No | Yes |
| ServiceRequest | Yes | TroubleCall (equivalent) | No | Yes |
| WorkOrder | Yes | Yes | No | Yes |
| WorkOrderTeam | Yes | Yes | No | Yes |
| WorkOrderLine | Yes | Yes | No | Yes |
| Quote | Yes | No | No | Yes |
| Invoice | Yes | No | No | Yes |
| Payment | Yes | No | No | Yes |
| Task | Yes | No | No | Yes |
| Product | Yes | Yes | Yes | Yes |
| KitItem | Yes | BundleItem (equivalent) | No | Yes |
| Vendor | Yes | Yes | No | Yes |
| PurchaseOrder | Yes | No | No | Yes |
| Warehouse | Yes | No | No | Yes |
| WorkGroup | Yes | No | No | Yes |
| Vehicle | Yes | No | No | Yes |
| Lead | Yes | No | No | Yes |
| Opportunity | Yes | No | No | Yes |
| Automation | Yes | No | No | Not in V6 (Email Spec) |
| Note/Document | **MISSING** | No | Yes | Yes |
| Numbering | SequenceTracker | No | NumberingRule (richer) | SequenceTracker |
| Lifecycle/States | TextChoices only | TextChoices only | Full framework | TextChoices |

---

# Section 8: Priority Recommendations

## Tier 1 — Adapt for SDTA Build (High Value)

### R1: Lifecycle/State Machine Framework
**Source:** Desktop Version (`lifecycle/`)
**Target:** New SDTA app or add to infrastructure
**Effort:** Medium (3-5 days to adapt + add tenant_id)
**Value:** Enforces valid status transitions per System Status V3. Prevents invalid state changes. Provides immutable audit of all transitions. Admin-configurable.
**Action:** Create tenant-scoped versions of LifecycleStateDef, LifecycleTransitionRule, LifecycleTransitionAudit. Seed with transitions from System Status V3 (Customer, Asset, WorkOrder, Invoice, etc.).

### R2: Enhanced Numbering Service
**Source:** Desktop Version (`numbering/`)
**Target:** Replace SequenceTracker in SDTA
**Effort:** Low-Medium (2-3 days)
**Value:** Adds yearly/monthly reset, atomic SELECT FOR UPDATE, assignment tracking, custom formats. The current SequenceTracker is minimal.
**Action:** Adapt NumberingRule, NumberSequence, AssignedNumber with tenant_id. Port `generate_number()` utility with atomic locking. Add NumberingMixin to models that need auto-numbering.

### R3: Note/Document Attachment Models
**Source:** Desktop Version (`notes/`, `documents/`, `files/`)
**Target:** New models in SDTA per Data Models V6 Section 1.8
**Effort:** Low (1-2 days)
**Value:** Fills the gap in service03. The exclusive arc pattern (NoteLink/DocumentLink) is already specified in Data Models V6.
**Action:** Create tenant-scoped Note, NoteLink, Document, DocumentLink, StoredFile models. Follow the Desktop Version's XOR validation pattern.

## Tier 2 — Reference When Building Features (Medium Value)

### R4: RLS Setup Script
**Source:** Django-CRM-master (`RLS_SETUP.md`)
**Target:** ServizDesk setup_rls.sql
**Effort:** Low (reference only)
**Value:** Well-documented RLS policy patterns. NULLIF + FORCE ROW LEVEL SECURITY patterns. Management command for RLS verification.
**Action:** Use as reference when writing setup_rls.sql. Replicate their `manage_rls --status --verify-user --test` command.

### R5: Kanban/Pipeline Board Pattern
**Source:** Django-CRM-master (leads/cases/tasks)
**Target:** Future scheduling/dispatch UI (Plus+ tier)
**Effort:** N/A (future reference)
**Value:** Reusable Pipeline → Stage → Entity pattern with drag-drop ordering and WIP limits.

### R6: Temporal Pricing / Pricebook
**Source:** koalixcrm-master (pricing engine)
**Target:** Pricebook features (Pro/Enterprise)
**Effort:** N/A (future reference)
**Value:** Price validity date ranges, currency transforms, customer-group pricing.

## Tier 3 — Archive / No Action

### R7: service01 — Archive entirely. Superseded by service03.
### R8: service02 — Archive. Duplicate of files with wrong DB defaults.
### R9: Desktop Version CRM models — Not reusable (single-tenant, already in service03).
### R10: koalixcrm-master — Keep as reference library. No portable code.
### R11: Django-CRM-master — Keep as reference library. Different architecture (DRF + SvelteKit vs HTMX).
### R12: Desktop Version backup module — Desktop-only pattern, not applicable to SaaS.

---

# Section 9: Duplicate / Obsolete File Assessment

| Project | Recommendation | Reason |
|---------|---------------|--------|
| **service03** | KEEP — Active codebase | This is the current SDTA |
| **files** | KEEP — Reference | Canonical infrastructure layer |
| **service02** | CAN REMOVE | Duplicate of files with wrong DB defaults |
| **service01** | CAN REMOVE | Fully superseded by service03 |
| **Desktop Version** | KEEP — Reference | Contains utility modules worth adapting (R1, R2, R3) |
| **Django-CRM-master** | KEEP — Reference | RLS setup guide and pipeline patterns |
| **koalixcrm-master** | OPTIONAL — Reference | Pricing/accounting patterns for future tiers |

---

# Section 10: Next Steps

1. **Confirm service03 is the active SDTA codebase** — If so, development continues there.
2. **Adapt Lifecycle Framework (R1)** — Highest-value reuse from Desktop Version. Enforces System Status V3 transitions.
3. **Enhance Numbering Service (R2)** — Replace SequenceTracker with richer NumberingRule pattern.
4. **Build Note/Document models (R3)** — Fill the gap in service03 per Data Models V6 Section 1.8.
5. **Write setup_rls.sql** — Reference Django-CRM-master's RLS_SETUP.md.
6. **Archive service01 and service02** — Remove from Code to Review.
