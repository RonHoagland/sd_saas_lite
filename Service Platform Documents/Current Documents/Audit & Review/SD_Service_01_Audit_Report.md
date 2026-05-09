# Deep Dive Audit: SD_Service_01 — Full Findings & Remediation Plan

**Date:** April 3, 2026  
**Scope:** 139 models, 64 viewsets, 137 serializers, 24 test files, all config/infrastructure across 18 Django apps

## TL;DR

The core architecture is solid — tenant isolation, lifecycle state machines, numbering, and exclusive-arc patterns are well-designed. No circular imports, no URL conflicts, no serializer collisions. However, there are **3 critical security issues, 5 high-severity bugs, 12+ medium issues, and major test coverage gaps** that need attention.

---

## CRITICAL ISSUES (P0 — Fix Immediately)

### C1. Tenant Isolation Breach — Infrastructure API ViewSets
- **File**: `SD_Service_01/infrastructure/api.py`
- **Problem**: `TenantStateViewSet` and `SubdomainIndexViewSet` use `viewsets.ReadOnlyModelViewSet` (non-tenant-scoped) instead of `ReadOnlyTenantViewSet`. Exposes cross-tenant infrastructure data — users can enumerate all subdomains and tenant states.
- **Fix**: Change both to `ReadOnlyTenantViewSet` and update serializers to extend `TenantModelSerializer`.

### C2. Audit Log Mutability — FileUploadLog
- **File**: `SD_Service_01/documents/api.py`
- **Problem**: `FileUploadLogViewSet` extends `TenantModelViewSet` (full CRUD) instead of `ReadOnlyTenantViewSet`. Audit logs can be modified/deleted after creation.
- **Fix**: Change to `ReadOnlyTenantViewSet`.

### C3. Hardcoded Database Credentials in Version Control
- **File**: `SD_Service_01/config/settings_test.py` (lines 24-29)
- **Problem**: `SDTA_DB_PASSWORD` and `SDTA_MIGRATION_DB_PASSWORD` are hardcoded as plaintext in a committed file.
- **Fix**: Move to `.env.test` file (gitignored), or use environment variable injection in CI.

---

## HIGH-SEVERITY ISSUES (P1 — Fix Soon)

### H1. Ledger Model Missing Exclusive Arc Validation
- **File**: `SD_Service_01/service/models.py` (Ledger model)
- **Problem**: Comment says "only one source document should be set" (invoice, payment, vendor_bill) but NO constraint or `ExclusiveArcMixin` enforces it. A ledger entry can link to both an invoice AND a payment simultaneously.
- **Fix**: Apply `ExclusiveArcMixin` to Ledger model.

### H2. ALLOWED_HOSTS Defaults to Empty
- **File**: `SD_Service_01/config/settings.py` (line 14)
- **Problem**: `ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())` — if the env var is missing, defaults to `[]`, rejecting all requests in production.
- **Fix**: Add validation that raises `ImproperlyConfigured` if empty in non-DEBUG mode.

### H3. Missing `related_name` on 30+ Foreign Keys in CRM
- **File**: `SD_Service_01/crm/models.py`
- **Models**: Contact, Address (8 FKs), Phone (6 FKs), Social (5 FKs), Lead, Opportunity, OpportunityContacts
- **Problem**: Missing `related_name` forces Django's `_set` default; makes API serializers and queries harder.
- **Fix**: Add explicit `related_name` to all FKs.

### H4. Missing Database Indexes on Frequently Queried Fields
- **Files**: `crm/models.py`, `service/models.py`, `maintenance/models.py`
- **Problem**: Address, Phone, Social have zero indexes despite having 8+, 6+, 5+ FK fields. `Invoice.invoice_date`, `WorkOrder.scheduled_date`, `Payment.payment_date`, `Asset.warranty_expiration` — all common filter/sort targets — are unindexed.
- **Fix**: Add composite indexes `(tenant_id, field)` on all high-query FK and date fields.

### H5. No Batch Limiting on Database Purge Operations
- **File**: `SD_Service_01/config/periodic_tasks.py`
- **Problem**: `.filter(...).delete()` on large tables can lock the DB for minutes on large datasets.
- **Fix**: Add batch limiting (e.g., `.order_by('id')[:10000]` loop pattern).

---

## MEDIUM-SEVERITY ISSUES (P2)

### M1. Task and TimeEntry Missing Exclusive Arc Validation
- **File**: `SD_Service_01/tasks/models.py`
- **Problem**: Task has optional FKs to `work_order` and `service_request`; TimeEntry has optional FKs to `task` and `work_order`. No validation that exactly one parent is set.

### M2. Retention Settings Not Defined in settings.py
- **File**: `SD_Service_01/config/periodic_tasks.py`
- **Problem**: Uses `getattr(settings, 'SDTA_RETENTION_*_DAYS', default)` but these settings are never defined. Relies entirely on hardcoded defaults (90, 365, 365 days). Operators can't override.

### M3. IsTenantAdmin Permission Attribute May Not Exist
- **File**: `SD_Service_01/api/permissions.py`
- **Problem**: Checks `getattr(request.user, 'is_tenant_admin', False)` but User model may not have this attribute. Falls back to `False` = nobody is admin.

### M4. Missing Stripe/Pusher Packages in requirements.txt
- **File**: `SD_Service_01/requirements.txt`
- **Problem**: Settings reference `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `PUSHER_*` keys but neither `stripe` nor `pusher` are in requirements.

### M5. staff App Not Included in API URLs
- **File**: `SD_Service_01/api/urls.py`
- **Problem**: staff app is in `INSTALLED_APPS` but its router is not imported/included in the API URL configuration.

### M6. Exception Handler Missing Logging
- **File**: `SD_Service_01/api/exceptions.py`
- **Problem**: Converts exceptions to HTTP responses without logging. Production debugging is impaired.

### M7. TenantManager Returns Unfiltered QuerySet Silently
- **File**: `SD_Service_01/config/base_models.py`
- **Problem**: When no tenant context exists (e.g., bug in view code), returns unfiltered data with no warning/logging. Could mask cross-tenant data leaks.

### M8. Inconsistent Field Naming Conventions
- Various files: `status` vs `state`, `name` vs `title`, `_number` suffix inconsistency, `_date` vs `_at` for timestamps.

### M9. User.prev_employee Self-Reference Missing Index
- **File**: `SD_Service_01/users/models.py`
- **Problem**: Self-referential FK for rehires has no `db_index=True`.

### M10. ExclusiveArcMixin PARENT_FK_FIELDS Hard-Coded
- **File**: `SD_Service_01/config/base_models.py`
- **Problem**: 22-field list must be manually updated when new parent types are added. Silent failure if field names don't match.

### M11. Bare `except Exception` in Periodic Tasks
- **File**: `SD_Service_01/config/periodic_tasks.py`
- **Problem**: Catches ALL exceptions including system errors. Should use specific exception types.

### M12. internal_urls.py Is Empty Placeholder
- **File**: `SD_Service_01/infrastructure/internal_urls.py`
- **Problem**: `urlpatterns = []` — any requests to `/internal/...` return 404. Middleware (`InternalAPIKeyMiddleware`) is wired but no endpoints exist.

---

## TEST COVERAGE GAPS (P1-P2)

### ZERO test coverage for three critical service layers:

**T1. Lifecycle Service** (`lifecycle/services.py`)
- No tests for `execute_transition()`, `get_available_transitions()`, `get_transition_history()`
- Role validation, reason enforcement, final state protection all untested
- State machine correctness is completely unverified

**T2. Numbering Service** (`numbering/services.py`)
- No tests for `generate_number()`, `get_next_sequence_value()`, `check_reset_needed()`, `format_number()`, `assign_number()`
- Race condition handling, yearly/monthly reset logic, all 8 format permutations — all untested

**T3. Notes Service** (`notes/services.py`)
- No tests for `create_note()`, `get_notes_for_entity()`
- Exclusive arc pattern validation for 25 parent types untested

**T4. Missing endpoint-level security tests**
- No tests verifying that API endpoints actually enforce tenant isolation
- Cross-tenant access attempts not tested

**T5. Missing concurrent operation tests**
- No tests for race conditions on numbering sequences or lifecycle transitions

---

## WHAT'S WORKING WELL (No Changes Needed)

- Core tenant isolation architecture (TenantModel, TenantManager, middleware, RLS)
- Celery task definitions match all routing/schedule references
- No circular imports across 18 apps
- No URL routing conflicts (all 64 viewsets properly registered)
- No serializer name conflicts across 137 serializers
- No admin registration conflicts across 100+ models
- Document/Note exclusive arc pattern correctly implemented
- FileDownloadLog immutability properly enforced
- Lifecycle framework design (state machine + audit trail)
- Numbering framework design (format + sequence + assignment)
- Staff/User model separation (no circular deps)
- Soft delete pattern with `all_objects` manager

---

## CROSS-APP CONFLICT ANALYSIS

No conflicts found between apps. All inter-app relationships are clean:

| Hub Model | Dependent Apps | FK Count | Status |
|-----------|---------------|----------|--------|
| `crm.Customer` | service, maintenance, procurement, documents, notes | 12+ | Clean |
| `users.User` | tasks, fleet, service, procurement, warehouse, workforce | 20+ | Clean |
| `inventory.InventoryItem` | fleet, service, warehouse, procurement | 7+ | Clean |
| `maintenance.Asset` | service, workforce, documents, notes | 6+ | Clean |
| `service.WorkOrder` | tasks, fleet, documents, notes | 5+ | Clean |

All FK `related_name` values are unique across apps (where provided). No model name collisions. No circular FK chains.

---

## REMEDIATION STEPS (Grouped by Phase)

### Phase 1: Security Fixes (C1, C2, C3, H2)
1. Fix `TenantStateViewSet` and `SubdomainIndexViewSet` to use `ReadOnlyTenantViewSet` — *infrastructure/api.py*
2. Fix `FileUploadLogViewSet` to use `ReadOnlyTenantViewSet` — *documents/api.py*
3. Remove hardcoded passwords from `settings_test.py`, add `.env.test` pattern
4. Add `ALLOWED_HOSTS` validation in `settings.py`

### Phase 2: Data Integrity Fixes (H1, H3, H4, M1, M9)
5. Apply `ExclusiveArcMixin` to Ledger model — *service/models.py*
6. Add `related_name` to all CRM FKs — *crm/models.py*
7. Add database indexes to Address, Phone, Social, and date fields (`invoice_date`, `payment_date`, `scheduled_date`, `warranty_expiration`)
8. Apply `ExclusiveArcMixin` or validation to Task and TimeEntry — *tasks/models.py*
9. Add `db_index=True` to `User.prev_employee` — *users/models.py*

### Phase 3: Operational Fixes (H5, M2, M4, M5, M6, M7, M11)
10. Add batch limiting to periodic purge operations — *periodic_tasks.py*
11. Define `SDTA_RETENTION_*` settings in `settings.py` with documented defaults
12. Add `stripe` and `pusher` to `requirements.txt` (if used) or remove settings references
13. Wire staff app router into API URLs — *api/urls.py*
14. Add logging to exception handler — *api/exceptions.py*
15. Add logging/warning in TenantManager when no tenant context — *base_models.py*
16. Use specific exception types in periodic tasks — *periodic_tasks.py*

### Phase 4: Test Coverage (T1-T5)
17. Create `test_lifecycle_service.py` (~50 test cases) — lifecycle transitions, roles, final states, audit
18. Create `test_numbering_service.py` (~40 test cases) — format permutations, reset logic, concurrency
19. Create `test_notes_service.py` (~35 test cases) — exclusive arc validation, all 25 parent types
20. Enhance `test_security_boundaries.py` — endpoint-level tenant isolation tests
21. Add concurrent operation tests for numbering and lifecycle

### Phase 5: Code Quality (M3, M8, M10, M12)
22. Verify `is_tenant_admin` attribute exists on User model or update permission class
23. Make `PARENT_FK_FIELDS` dynamic (introspect model FKs) or add validation
24. Document `internal_urls.py` status and planned endpoints

---

## Verification Checklist

1. Run full test suite: `python manage.py test --settings=config.settings_test`
2. Verify no new migration needed after model changes: `python manage.py makemigrations --check`
3. After Phase 1: Test cross-tenant access on infrastructure endpoints
4. After Phase 2: Run `python manage.py makemigrations` for new indexes
5. After Phase 4: Run new test files and confirm all pass
6. Check for import errors: `python -c "import config.urls"` from `SD_Service_01/`

---

## Decisions & Notes

- All Celery task routes verified as valid — no missing task definitions
- `infrastructure/internal_urls.py` is intentionally empty per documented plan — not a bug
- `FileDownloadLog` using raw UUID fields (not FKs) is architecturally intentional for audit immutability
- `TenantPreference` monolithic model may be intentional for simplicity — flagged but not recommended to split now
