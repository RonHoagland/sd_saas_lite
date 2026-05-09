# SD Service Full — Audit & Strip-Down Plan

**Branch:** `audit-and-stabilize`
**Date:** 2026-04-25
**Scope:** Phase A of the audit-and-stabilize work. Inventory current state, identify code surfaces to strip vs. keep, propose a sequenced strip-down plan. **No code changes in Phase A.**

---

## 1. Executive summary

The codebase is a copy of `sdservice02` — a multi-tenant SaaS Django application originally built as the "ServizDesk Tenant App" (SDTA). It is being repurposed as a **single-tenant standalone Django application** with no SDP platform layer, eventually growing into a full ERP. The foundation is sound. The strip-down is well-bounded.

**Health snapshot:**
- 18 Django apps (5 framework + 11 domain + 2 cross-cutting), all wired and migrated.
- ~45 concrete model classes across 18 apps. ~45 migrations.
- 35 test modules (31 in `tests/`, 4 in app `tests.py`).
- 26 templates. 1 vanilla Bootstrap 5.3.3 + Lucide 0.469.0 theme. No SPA, no HTMX.
- DB: PostgreSQL with two-user split (`djangouser` + `sdta_migration` BYPASSRLS).
- Auth: 4-backend chain. `StaffUser` for `/admin/`, custom `User` for the app.

**Strip-down is small, focused, and reversible:**
- 1 entire Django app (`staff`) is going away.
- 1 URL mount (`/internal/api/v1/`) is empty placeholder — trivial delete.
- 5 Stripe model classes + 5 Stripe admins + Stripe env vars + CSP entries.
- Pusher env vars (unused even today).
- `tenant_id` column from ~45 models + the abstract `TenantModel` and `TenantManager` glue.
- 7 test modules trashed; 22 kept; 2 investigated.
- 1 hardcoded "Lite" tier badge + 13 cosmetic "ServizDesk Lite" string occurrences in templates (deferred — naming decision pending).

**No surprise blockers found.** No SaaS-specific package dependencies (no Stripe SDK, no `django-tenants`, no plan-gating libs), so `requirements.txt` doesn't change. No active tier-gating logic in views/serializers — there is a `tier` field on `TenantState` but nothing actually checks it.

---

## 2. Current-state inventory

### 2.1 Apps

**Framework (5):** `numbering`, `lifecycle`, `value_lists`, `notes`, `documents`
**Cross-cutting (2):** `infrastructure` (tenant orchestration, Stripe, webhooks), `api` (DRF wiring)
**Domain (11):** `users`, `crm`, `service`, `maintenance`, `tasks`, `workforce`, `inventory`, `warehouse`, `procurement`, `fleet`, `automation`
**SaaS-only (1):** `staff` — to be merged into `users` and deleted

### 2.2 Configuration

**Settings (`config/settings.py`):**
- `AUTH_USER_MODEL = 'users.User'` — already the tenant employee model (good).
- `DATABASES` — two aliases (`default` runtime user + `worker` BYPASSRLS user).
- `INSTALLED_APPS` — 32 entries; `staff` is the only one we delete.
- `MIDDLEWARE` — 11 entries; 3 custom (`AdminBypassMiddleware`, `TenantMiddleware`, `InternalAPIKeyMiddleware`).
- `AUTHENTICATION_BACKENDS` — 4 entries: `StaffUserBackend`, `SchemaSafeSessionBackend`, `ModelBackend`, `AxesStandaloneBackend`.

**.env keys (18):**
- Django core: `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- DB: `SDTA_DB_*` (6 keys), `SDTA_MIGRATION_DB_USER`, `SDTA_MIGRATION_DB_PASSWORD`
- Security/cookies: 6 toggle keys for local-dev cookie/SSL behavior
- Celery: `CELERY_BROKER_URL`
- (settings defaults but not in .env): `SDTA_S3_*`, `STRIPE_*`, `PUSHER_*`, `INTERNAL_API_KEY`, `SDTA_INTERNAL_BASE_URL`

**`requirements.txt` (11 packages):** Django 6.0.x, psycopg2-binary, python-decouple, djangorestframework, django-filter, celery, redis, django-celery-results, django-axes, django-csp, asgiref, Pillow. Nothing SaaS-specific.

### 2.3 URL mounts (`config/urls.py`)

| Path | Target | Strip? |
|------|--------|--------|
| `/` | `splash_login_view` | Refactor (drop tenant resolution) |
| `/home/` | `home_view` | Keep |
| `/logout/` | `logout_view` | Keep |
| (root) | `users.urls`, `crm.urls`, `maintenance.urls`, `service.urls` | Keep |
| `/admin/` | Django admin | Keep (rewire to merged User) |
| `/api/v1/` | `api.urls` | Keep (decision deferred) |
| `/internal/api/v1/` | `infrastructure.internal_urls` (empty placeholder) | **Delete** |

### 2.4 Models

~45 classes across 18 apps — all inherit the abstract `TenantModel` defined at `config/base_models.py:28-110`. Notable groupings:
- **`infrastructure`** has SaaS-specific models we will delete: `TenantState`, `TenantAddOn`, `SubdomainIndex`, `StripeConnection`, `StripeResponse`, `StripeLog`, `StripeConnectionLog`, `StripeAPIRequestLog`, `OnboardingState`, `EmailUsageTracker`, `SMSUsageTracker`. **Decision needed** on `StorageTracker` and `WebhookLog` (see §6).
- **All other apps** have business-logic models that are keepers.

### 2.5 Frontend

- `templates/base.html` — Bootstrap 5 sidebar/topbar shell. Title hardcoded `"ServizDesk Lite"` (line 6).
- `templates/includes/app_sidebar.html` — primary nav. Tier badge hardcoded `"Lite"` (line 23). 3 unimplemented stub nav items at `href="#"` (Tasks, Time Tracking, Products & Services).
- 26 templates total. No tier-specific or SDP/staff-only templates outside what's mentioned.
- `static/vendor/bootstrap-5.3.3/`, `static/vendor/lucide-0.469.0/`. Vendored, no CDN.
- `static/css/site.css` — 278 lines of clean Bootstrap overrides using `--sd-*` CSS custom properties.
- `static/js/home.js` — 12 lines, **dead code** (toggles a `.admin-toggle` element that doesn't exist in the DOM).
- `static/images/logo_placeholder.svg` — **orphan**, never referenced.

### 2.6 Tests

**35 test modules total** (31 in `tests/`, 4 app-level).
- **Keep (22):** behavioral tests for CRUD, financial calculations, storage, API serialization, business workflows. See §5 for the full list.
- **Trash (7):** tenant boundaries, multi-tenant admin patterns, SaaS infrastructure, seed data tied to SaaS provisioning. ~4,500 LOC removed.
- **Investigate (2):** `test_api_auth.py` (auth is behavioral but currently uses `TenantState`); `test_celery_tasks.py` (depends on whether tenant-scoped task handling matters).

No `pytest.ini`, `pyproject.toml`, or `conftest.py` — Django's built-in test runner is used. No `factory_boy`; fixtures are hand-built in `tests/base.py`.

---

## 3. Strip-down plan (sequenced)

Each phase is a self-contained commit-able step. I'll commit after each so you can review or revert any single step.

### Phase B1 — Dead-code & SaaS-edge cleanup (low risk, no model changes)

Files touched: ~10. Migrations: 0. Tests: trash 7 modules.

1. **Delete `/internal/api/v1/`:**
   - Delete `infrastructure/internal_urls.py`
   - Remove `path('internal/api/v1/', ...)` from `config/urls.py`
   - Remove `InternalAPIKeyMiddleware` (lines 121-162) from `config/middleware.py`
   - Remove `'config.middleware.InternalAPIKeyMiddleware'` from `MIDDLEWARE`
   - Remove `INTERNAL_API_KEY`, `SDTA_INTERNAL_BASE_URL` from `config/settings.py`
2. **Delete Stripe code** (no migrations, since we'll do all infrastructure model deletes together in B3):
   - Stub the 5 Stripe model classes for B3 (note them; don't delete yet to avoid migration churn)
   - Delete the 5 Stripe admin classes (`infrastructure/admin.py:130-166`)
   - Delete Stripe serializers/viewsets from `infrastructure/api.py`
   - Remove `STRIPE_*` env vars and CSP whitelist entries from `config/settings.py`
3. **Delete Pusher env vars** (`PUSHER_*`) — not referenced in code.
4. **Frontend dead-code:**
   - Delete `static/images/logo_placeholder.svg`
   - Delete `static/js/home.js` (12 lines, dead)
5. **Trash 7 test modules:**
   - `tests/test_admin.py` (1140 LOC) — Django admin registration tests, mostly multi-tenant patterns
   - `tests/test_cross_module_integrity.py` (588 LOC) — multi-tenant FK/cascade tests
   - `tests/test_infrastructure.py` (1041 LOC) — Stripe, TenantState, billing, subscription
   - `tests/test_middleware_full.py` (216 LOC) — TenantMiddleware/InternalAPIKey
   - `tests/test_security_boundaries.py` (58 LOC) — cross-tenant write blocks
   - `tests/test_seed.py` (327 LOC) — SaaS seed/fixture validation
   - `tests/test_tenant_model.py` (131 LOC) — TenantModel base class behavior
6. **Defer:** `seed_lite_dev.py` management command — review during B3 along with infrastructure cleanup.

### Phase B2 — Merge `users.User` + `staff.StaffUser`

Files touched: ~15. Migrations: 1 (User model merge). Tests: refactor `test_users.py` and `tests/base.py`.

1. **Merge model:** Add `is_staff`, `is_superuser` fields to `users.User` (Django convention). Move any unique fields from `StaffUser` (likely a couple of admin-specific flags) onto `users.User`.
2. **Migration:** Single migration that adds the new fields. (StaffUser data migration is N/A — no production data to preserve in this build.)
3. **Delete `staff/` directory entirely** (`staff/__init__.py`, `apps.py`, `models.py`, `backends.py`, `admin.py`, `migrations/`, `management/`).
4. **Settings updates:**
   - Remove `'staff.apps.StaffConfig'` from `INSTALLED_APPS`.
   - Remove `'staff.backends.StaffUserBackend'` from `AUTHENTICATION_BACKENDS`.
   - `AdminBypassMiddleware` — keep for now, simplify in B4.
5. **Code rewrites:**
   - `config/views.py` `splash_login_view` — drop StaffUser path, drop tenant resolution via subdomain (single-tenant doesn't need it).
   - `config/context_processors.py` — drop `is_system_user` (replace with `request.user.is_staff`), drop `workspace_subdomain`.
   - Preserve `create_system_user` management command — port to a `users` app management command for creating superuser/admin accounts.
6. **Test refactor:**
   - `tests/base.py` — `SDTATestCase` no longer creates StaffUser.
   - `tests/test_users.py` — refactor for merged model.

### Phase B3 — Strip multi-tenancy from models

Files touched: ~50 (all models, admin.py files). Migrations: 1 large schema migration. Tests: refactor base case.

1. **Delete SaaS-only infrastructure models** in `infrastructure/models.py`:
   - `TenantState` (line 26-67), `TenantAddOn`, `SubdomainIndex`
   - `OnboardingState`, `TenantSyncLog`, `DataExportLog`
   - `EmailUsageTracker`, `SMSUsageTracker`, `EmailDeliveryLog`
   - 5 Stripe models (B1 stubs)
   - **Decision needed (§6):** `StorageTracker`, `WebhookLog`, `Notification`, `IssuesErrors`, `SystemAudits`, `NavigationAudit`, `ProcessTransaction`
2. **Strip `tenant_id` and tenant glue** from `config/base_models.py`:
   - Remove `tenant_id = models.UUIDField(...)` from `TenantModel` (line 56)
   - Remove `clean()` cross-FK validation (lines 71-85)
   - Simplify `save()` — keep audit timestamps, drop tenant context enforcement (lines 87-109)
   - Rename `TenantModel` → `AuditedModel` (signals new purpose)
   - Remove `TenantManager` entirely; subclasses will use stock Django manager
3. **Update every model:**
   - All ~45 concrete subclasses keep inheriting `AuditedModel` (rename only)
   - Remove `unique_together` and `indexes` clauses that reference `tenant_id` (e.g. `StorageTracker`, `EmailUsageTracker`, `SMSUsageTracker` if we kept them)
4. **Generate one migration per affected app** (~14 apps) that:
   - Drops `tenant_id` column
   - Drops indexes/constraints on `tenant_id`
5. **Admin cleanup:**
   - `staff/admin.py:22-80` `TenantModelAdmin` mixin gets folded into a simpler `BaseModelAdmin` in `users` or `infrastructure` (already deleting `staff/` in B2; if `staff/admin.py` gets cleaned in B2, finalize here).
   - Remove tenant-aware filtering from per-app admin classes.
6. **Test refactor:**
   - `tests/base.py` — drop tenant fixture creation.

### Phase B4 — Rewire middleware for role-based context

Files touched: ~5. Migrations: 0.

1. **Rewrite `TenantMiddleware`** (`config/middleware.py:16-83`) → `UserContextMiddleware`:
   - Set `app.current_user_id` and `app.current_role_code` PG session vars per request.
   - Drop `tenant_id` lookup logic.
2. **Rename `config/tenant_context.py` → `config/user_context.py`:**
   - `set_current_user_id`, `set_current_role_code`, `get_current_user_id`, `get_current_role_code`.
3. **`AdminBypassMiddleware`** — simplify to: skip user context if path starts with `/admin/` (since admin uses superuser bypass).
4. **RLS policies:** No new policies until ERD lands. The infrastructure (PG session vars) is wired but no RLS policy currently uses them — this is intentional. The DB layer is "RLS-ready" but unenforced for now.
5. **System role codes** — define a Python constant module (e.g., `users/roles.py`):
   ```python
   class SystemRoleCode:
       ADMIN = 'admin'
       MANAGER = 'manager'
       TECHNICIAN = 'technician'
       READONLY = 'readonly'
   ```
   Wire `users.Role.system_code` (FK or CharField with choices) to one of these. Custom roles map to a system code for RLS purposes; fine-grained permissions live in the app.

### Phase B5 — Configuration & DB cleanup

Files touched: 3-5.

1. **`config/settings.py` final pass:**
   - `INSTALLED_APPS` — drop `staff`
   - `AUTHENTICATION_BACKENDS` — drop `StaffUserBackend`
   - `MIDDLEWARE` — drop `InternalAPIKeyMiddleware` (already done in B1)
   - Remove all SaaS-only settings: `STRIPE_*`, `PUSHER_*`, `INTERNAL_API_KEY`, `SDTA_INTERNAL_BASE_URL`
   - **Decision needed:** consolidate `default` + `worker` DB aliases or keep both?
2. **`.env`:**
   - Remove SaaS-only keys (or comment out as "deferred").
   - **Decision needed:** keep `SDTA_MIGRATION_DB_*`?
3. **`config/urls.py`:**
   - Remove `/internal/api/v1/` (already done in B1).
4. **CSP cleanup** — remove Stripe URLs from `CONTENT_SECURITY_POLICY`.

### Phase C — Stabilize

1. Connect to your fresh Postgres. Wait on credentials.
2. Apply migrations.
3. Run remaining test suite. Fix or document failures.
4. Smoke test:
   - `manage.py runserver` starts cleanly.
   - Login at `/` works (with a created superuser).
   - `/home/` loads.
   - `/admin/` loads.
   - One representative list view loads (e.g., `/customers/`).

### Phase D — Pause for ERD

Hand off the working app + report. Wait for ERD to drive Phase E (model redesign).

---

## 4. What we KEEP and why

| Item | Why keep | Note |
|---|---|---|
| Two-DB-user pattern (`default` + `worker`) | Defense in depth — app code can't run DDL or bypass row policies | Optional; flag for decision in §6 |
| RLS infrastructure (middleware sets PG session vars) | Repurposed for user/role context; valuable for ERP-grade row visibility | Wired but unenforced until ERD |
| Field-level audit timestamps on `AuditedModel` (`created_at`, `updated_at`, `created_by`, `updated_by`) | Useful for compliance/forensics, ERP-relevant | Verify these fields exist on current `TenantModel` and preserve |
| `SchemaSafeSessionBackend` (`api/backends.py`) | Schema-drift-safe session rehydration — useful for ongoing dev | Keep |
| `AxesStandaloneBackend` + django-axes | Login lockout protection | Keep |
| Bootstrap 5.3.3 + Lucide 0.469.0 + `site.css` | Existing theme is clean and tier-agnostic | Verbatim per user direction; consider Bootstrap 5.3.4 patch |
| All 11 domain apps + 5 framework apps | Business logic, will adapt to new ERD | Models will likely refactor when ERD lands |
| 22 behavioral test modules | Useful for regression detection during refactor | Some need light refactor for merged User model |
| `/admin/` (Django admin) | Useful for ad-hoc data work | Wired to merged User with `is_staff=True` |
| `/api/v1/` (DRF REST) | Holding off per user direction | Will revisit when external client needs known |
| Celery + Redis | Async task queue, useful for ERP | Note: Redis adds an on-prem deployment dependency |
| CSP, django-axes, secure cookies, HSTS | Production-grade security | Keep all |

---

## 5. Test classification (full)

### KEEP (22)

`tests/test_api_framework.py`, `tests/test_automation.py`, `tests/test_automation_equipment.py`, `tests/test_automation_projects.py`, `tests/test_automation_safety.py`, `tests/test_automation_workflow.py`, `tests/test_crm.py`, `tests/test_financial_calculations.py`, `tests/test_fleet.py`, `tests/test_inventory.py`, `tests/test_maintenance.py`, `tests/test_procurement.py`, `tests/test_service.py`, `tests/test_service_conversions.py`, `tests/test_storage.py`, `tests/test_tasks.py`, `tests/test_users.py`, `tests/test_value_lists.py`, `tests/test_warehouse.py`, `tests/test_workforce.py`, `lifecycle/tests.py`, `notes/tests.py`, `numbering/tests.py`, `service/tests.py`

(Also keep `tests/__init__.py` and `tests/base.py` — base class needs refactor.)

### TRASH (7)

`tests/test_admin.py`, `tests/test_cross_module_integrity.py`, `tests/test_infrastructure.py`, `tests/test_middleware_full.py`, `tests/test_security_boundaries.py`, `tests/test_seed.py`, `tests/test_tenant_model.py`

### INVESTIGATE (2)

- `tests/test_api_auth.py` — auth flows are behavioral, but currently use `TenantState` to set up the auth context. Refactor to use the merged User model directly. Keep the auth coverage.
- `tests/test_celery_tasks.py` — task tests; check if any depend on tenant-scoped queueing. If just behavioral, keep.

---

## 6. Open decisions for you

These are the points where I'd rather have your input than guess. Defaults shown.

1. **Two-DB-user pattern: keep both `default` and `worker` aliases, or consolidate to one?**
   - **Keep:** retains defense-in-depth (`djangouser` can't run DDL even if app is compromised). On-prem deployment friendly.
   - **Consolidate:** simpler `.env`, simpler ops (one Postgres user). Reasonable for single-tenant.
   - **Default:** **keep both** — small operational cost for real security benefit, especially with single-tenant on-prem where customer-deployed Postgres setups vary.

2. **Storage/usage tracking models: `StorageTracker`, `EmailUsageTracker`, `SMSUsageTracker` — delete or repurpose?**
   - **Delete:** these were SaaS-tier-quota models. No tier in single-tenant.
   - **Repurpose:** could measure storage usage as an operational metric for the customer.
   - **Default:** **delete** — operational metrics can be added later if needed; don't carry SaaS framing forward.

3. **`WebhookLog`: generic webhook log — delete or keep?**
   - **Delete:** was for SDP→SDTA inbound webhooks; no SDP now.
   - **Keep:** generic enough to log inbound webhooks from any future integration (Stripe-direct, Postmark, Twilio).
   - **Default:** **keep** as a reusable inbound-webhook audit table. Costs almost nothing.

4. **`Notification`, `IssuesErrors`, `SystemAudits`, `NavigationAudit`, `ProcessTransaction` (in `infrastructure/models.py`):**
   - These look like cross-cutting platform concerns (audit, notifications, error tracking). Need a 5-min review per model — likely keep most but rename/repurpose. I'll flag during execution.

5. **`test_admin.py` (1140 LOC):** trash entirely or salvage?
   - The Django admin still exists post-strip-down (we're keeping it for the merged User). Some admin-coverage might be reusable.
   - **Default:** **trash** — the test asserts about `staff` app + multi-tenant admin patterns specifically. Cheaper to write a fresh, smaller admin smoke test than to rewrite this.

6. **Templates: rename "ServizDesk Lite" → ?**
   - 13 occurrences of "Lite", 7 of "ServizDesk" in templates.
   - This is a **product naming decision**. Should I leave them for now (Phase B doesn't change them) and revisit when you've decided product name?
   - **Default:** **leave for now**, address as a separate dedicated naming pass when the ERD/product direction firms up.

7. **`/api/v1/` DRF endpoints:** strip-but-leave-config, or fully remove for now?
   - Per your direction, holding off touching `/api/v1/` until we know what external clients need. The endpoints today are tenant-scoped (filter by `tenant_id`) — they will be **broken** post-B3 (model strip-down) until refactored.
   - **Default:** **leave config in place, add a single `# TODO: refactor for single-tenant` comment at top of `api/urls.py`**, ignore until you tell me to revive them. Will document the broken state at end of Phase C.

---

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Migrations conflict during `tenant_id` drop across many apps | Medium | High | Generate one migration per app, apply in known order. Test on fresh DB first. |
| Removing `TenantModel.clean()` accidentally allows invalid FK | Low | Low | We're single-tenant; cross-tenant FKs are no longer a concern. App-level FK constraints remain enforced by Django. |
| `/api/v1/` endpoints break in Phase B3 and stay broken | High (intentional) | None today, future risk if revived | Document broken state at end of Phase C. Skip API tests in `tests/test_api_framework.py` if they fail. |
| `staff/admin.py:22-80` `TenantModelAdmin` mixin removal breaks all admin classes | Medium | Medium | Provide a stub replacement in `infrastructure/admin.py` that admin classes can inherit from. |
| Existing migrations reference `tenant_id` historically; squashing not done | Low | Low | New migrations will drop the column; old migrations stay as historical record. No squash needed. |
| Test fixtures in `tests/base.py` heavily depend on tenant setup | High | Medium | Refactor `SDTATestCase` in B2 (alongside User merge) to drop tenant. Will affect ~22 keep-tests, but mostly trivial. |

---

## 8. Recommended next steps

1. **Review this report.** Especially §6 open decisions.
2. **Drop in DB credentials** to `.env` whenever Postgres is ready.
3. **Give me a green light** for Phase B (or call out anything that needs to change in the plan above).
4. After B + C complete, ERD work starts.

---

## Appendix A — Settings cleanup checklist (for B5)

- [ ] Drop from `INSTALLED_APPS`: `staff.apps.StaffConfig`
- [ ] Drop from `AUTHENTICATION_BACKENDS`: `staff.backends.StaffUserBackend`
- [ ] Drop from `MIDDLEWARE`: `config.middleware.InternalAPIKeyMiddleware` (B1)
- [ ] Drop from `MIDDLEWARE`: revise `config.middleware.AdminBypassMiddleware` (B4)
- [ ] Drop env: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- [ ] Drop env: `PUSHER_APP_ID`, `PUSHER_KEY`, `PUSHER_SECRET`, `PUSHER_CLUSTER`
- [ ] Drop env: `INTERNAL_API_KEY`, `SDTA_INTERNAL_BASE_URL`
- [ ] Decide env: `SDTA_MIGRATION_DB_USER`, `SDTA_MIGRATION_DB_PASSWORD` (§6 #1)
- [ ] CSP: remove Stripe URL allow-list entries
- [ ] Drop versioning: `SERVIZDESK_UI_ASSET_VERSION`, `SERVIZDESK_VERSION` (cosmetic; deferred with naming pass)

## Appendix B — Files to delete (Phase B1 only)

- `infrastructure/internal_urls.py`
- `static/images/logo_placeholder.svg`
- `static/js/home.js`
- `tests/test_admin.py`
- `tests/test_cross_module_integrity.py`
- `tests/test_infrastructure.py`
- `tests/test_middleware_full.py`
- `tests/test_security_boundaries.py`
- `tests/test_seed.py`
- `tests/test_tenant_model.py`

## Appendix C — Files to delete (Phase B2)

- `staff/__init__.py`
- `staff/apps.py`
- `staff/models.py`
- `staff/admin.py`
- `staff/backends.py`
- `staff/migrations/` (entire directory)
- `staff/management/` (entire directory; port `create_system_user` to `users/management/`)

## Appendix D — Files to delete (Phase B3)

Sections of `infrastructure/models.py` and `infrastructure/admin.py` and `infrastructure/api.py`. Specific line ranges in §3.B3.

---

**End of audit report.**
