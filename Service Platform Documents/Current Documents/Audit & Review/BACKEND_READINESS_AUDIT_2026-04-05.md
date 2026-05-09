# Backend Readiness Audit (Pre-React)

Date: 2026-04-05  
Scope: Backend code + runtime validation against local PostgreSQL (`djangouser`)  
Mode: Read-only audit (no production code fixes applied)

## Executive Assessment

Current backend state is **not frontend-ready** and has multiple **release-blocking** defects:

- Migration and schema state is inconsistent enough to block reliable test execution.
- Tenant isolation has critical gaps in the application layer and relies on middleware behavior that is currently broken.
- Several service-layer and serializer contracts are invalid against current models.
- Existing test suite cannot be trusted as a readiness gate in current state.

---

## Runtime Evidence Collected

1) `manage.py check` ran and reported:
- `auth.W004`: `users.User.email` is `USERNAME_FIELD` but not unique.

2) `manage.py test` failed before execution due DB/bootstrap issues:
- `django.db.utils.ProgrammingError: relation "crm_customer" does not exist`

3) `manage.py migrate --plan` failed with migration history inconsistency:
- `InconsistentMigrationHistory: Migration infrastructure.0001_initial is applied before its dependency automation.0001_initial`

4) Middleware simulation showed tenant context is unavailable inside request handling:
- `during_view= None`
- `after_response= None`

5) Tenant manager SQL (with no tenant context) had no tenant filter:
- `SELECT ... FROM "users_department"` (no `WHERE tenant_id = ...`)

6) Model-vs-DB drift audit:
- `tenant_model_count=129`
- `missing_table_count=119`
- `tables_checked=18`
- `drifted_models=13`

7) Runtime model contract check:
- `Quote() got unexpected keyword arguments: 'service_request'`
- `Quote() got unexpected keyword arguments: 'subject'`

8) Runtime user contract check:
- `has_username_attr= False`
- `username_field= email`

---

## Findings (Severity Ordered)

## Critical

### 1) Tenant context is not set during view execution
**Where:** `config/middleware.py`  
**Why this is critical:** Tenant scoping logic (`TenantManager`, custom permissions) depends on thread-local tenant context. It is being set after response generation, so it is unavailable during the request.

**Impact:**
- Application-level tenant filtering/permission checks can fail open or behave unpredictably.
- Multi-tenant data boundaries are at risk if RLS assumptions fail or are incomplete.

**Evidence:**
- Middleware simulation returned `during_view= None`.

---

### 2) Many tenant-facing viewsets use `all_objects` (unfiltered manager)
**Where:** `notes/api.py`, `documents/api.py`, `numbering/api.py`, `lifecycle/api.py` and others  
**Why this is critical:** `all_objects` bypasses tenant manager filtering by design. Combined with broken tenant context wiring, this is an acute cross-tenant exposure risk.

**Impact:**
- Cross-tenant data exposure through APIs is possible if DB-level RLS does not fully protect every affected table/query path.

---

### 3) Migration history is inconsistent in live DB
**Where:** migration state (`manage.py migrate --plan`)  
**Why this is critical:** You cannot trust migration order, test DB creation, or schema parity.

**Impact:**
- CI/test bootstrap is unstable.
- Deploy risk is high (non-deterministic migration behavior).

**Evidence:**
- `infrastructure.0001_initial` marked applied before dependency `automation.0001_initial`.

---

### 4) Massive schema drift between models and actual DB
**Where:** live DB vs model metadata  
**Why this is critical:** Runtime behavior will fail unpredictably (missing columns, missing tables, invalid query assumptions).

**Impact:**
- API requests can crash on serialization/querying.
- Any frontend integration will hit inconsistent contracts.

**Evidence examples:**
- `crm_customer.lead_source` missing in DB (runtime error observed).
- 119 TenantModel tables missing.
- 13 checked models had column mismatches.

---

### 5) Core service conversion logic uses invalid model fields
**Where:** `service/services.py`  
**Why this is critical:** Conversion endpoints are expected frontend workflows; invalid kwargs cause hard failures.

**Examples:**
- `convert_service_request_to_quote()` sets `Quote(service_request=..., subject=...)` but `Quote` model has neither field.

**Evidence:**
- Runtime TypeError for both kwargs.

---

## High

### 6) Test suite is not executable as a gate
**Where:** global test run + migration bootstrap  
**Why this matters:** You asked for module-level confidence before React build. Current suite cannot provide that confidence.

**Evidence:**
- `manage.py test` aborts before test execution (`relation "crm_customer" does not exist`).

---

### 7) Serializer fields reference nonexistent `username` on custom User
**Where:** `service/api.py`, `crm/api.py` (and likely others using `source='...username'`)  
**Why this matters:** Response serialization can break or emit incorrect values.

**Evidence:**
- Runtime check confirms `User` has no `username` attribute and uses `email` as `USERNAME_FIELD`.

---

### 8) RLS script table list is stale/inaccurate for current app/table names
**Where:** `scripts/setup_rls.sql`  
**Examples:**
- References `notes_document` and `notes_fileuploadlog`, but document models are in `documents_*` tables.

**Why this matters:**
- Security posture can be silently weaker than intended if policy coverage is incomplete/mismapped.

---

### 9) Missing migrations for core framework apps
**Where:** `lifecycle`, `value_lists`, `notes`, `documents` (no migration files detected)  
**Why this matters:** Schema cannot be recreated deterministically for CI/test/provisioning.

---

### 10) DB/user auth model warning (`USERNAME_FIELD` not unique)
**Where:** `users/models.py` + `manage.py check`  
**Why this matters:** Authentication behavior can become ambiguous unless backends guarantee uniqueness semantics.

---

## Medium

### 11) React integration blockers in auth/session setup
**Where:** `config/settings.py`  
**Gaps observed:**
- Session auth enabled, but no explicit CORS configuration found.
- `CSRF_COOKIE_HTTPONLY=True` can complicate JS-based SPA CSRF token workflows depending on architecture.

**Why this matters:** Frontend auth bootstrap and cross-origin requests may fail without explicit contract/flow.

---

### 12) Internal API route exists but endpoint surface is empty
**Where:** `infrastructure/internal_urls.py`  
**Why this matters:** If frontend or supporting services depend on internal endpoints, readiness is incomplete.

---

### 13) Placeholder malware scanning still active in document pipeline
**Where:** `documents/tasks.py`  
**Why this matters:** Security/compliance gap for file ingestion in production mode.

---

### 14) Hardcoded credentials in test settings
**Where:** `config/settings_test.py`  
**Why this matters:** Credential management hygiene issue; should be environment-only even in test config.

---

## Test Quality Review Notes

- Existing tests are numerous (`1172` discovered) but currently non-runnable due migration/schema issues.
- `service/tests.py` appears incompatible with current user model contract (`create_user` signature expects `tenant_id`).
- Until migration/schema parity is restored, test outcomes are not reliable indicators of backend health.

---

## Frontend Readiness Verdict

**Verdict:** Not ready for React integration yet.

Primary blockers before frontend kickoff:
1. Restore deterministic migration state and DB schema parity.
2. Fix tenant-context lifecycle in middleware and remove unsafe `all_objects` API exposure.
3. Repair service conversion logic and serializer field mappings.
4. Rebuild/validate test pipeline on a clean migrated DB.

---

## Suggested Remediation Sequence (Work Plan)

1) **Migration integrity reset**
- Resolve inconsistent migration history.
- Add missing migrations (`lifecycle`, `value_lists`, `notes`, `documents`).
- Validate full `migrate` on clean DB.

2) **Tenant security hardening**
- Correct middleware tenant context timing (must be set before view logic and cleared after response).
- Replace `all_objects` with tenant-safe managers in API querysets unless explicitly justified.
- Reconcile `setup_rls.sql` table list with actual table names.

3) **Contract correctness**
- Fix conversion services to match current model fields.
- Replace serializer `username` sources with valid user attributes.

4) **Frontend contract pass**
- Define/implement CORS + CSRF/session strategy for React.
- Lock error format and pagination/filter behavior for API consumers.

5) **Test reliability**
- Repair failing tests and add targeted tests for tenant boundaries, conversion paths, and serializer contracts.
- Run full suite successfully on clean DB as release criterion.

---

## Notes on Test Data

- No persistent audit test records were intentionally inserted because migration/schema inconsistencies prevented a reliable baseline for CRUD validation.
- Runtime validation was done via management commands and short, non-persistent Python probes.

