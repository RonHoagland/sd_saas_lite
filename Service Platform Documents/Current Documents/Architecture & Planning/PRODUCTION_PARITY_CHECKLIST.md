# Service03 — production parity checklist

Use this after the automated suite (`manage.py test --settings=config.settings_test`). That suite uses PostgreSQL for ORM and constraints but **strips** CSP and django-axes and does **not** apply `scripts/setup_rls.sql` to the test database. This checklist closes those gaps on a **disposable copy** of your database.

---

## 1. Roles and RLS (what you are validating)

| Setup | RLS enforced for tenant sessions? | Admin / worker alias sees all tenants? |
|--------|-----------------------------------|----------------------------------------|
| **Spec:** `sdta_app` (no BYPASSRLS) + `sdta_migration` (BYPASSRLS) | Yes, when `app.current_tenant_id` is set and policies are applied | Yes, via `sdta_migration` |
| **Single dev user** (e.g. `djangouser` on `serviz_db`) | **Often no** — superusers and many admin roles bypass RLS | N/A |

To validate RLS for real, use the split roles from [scripts/setup_postgres.sql](scripts/setup_postgres.sql) (or equivalent) and point `.env` at `sdta_app` for `default` and `sdta_migration` for `worker`. For a lighter pass, you can still run the steps below on `djangouser` to confirm **policies exist** and **middleware + full middleware stack** behave.

---

## 2. Prepare a clone database (do not use production data URL by mistake)

Pick a new database name, e.g. `serviz_db_parity`.

**Option A — empty database (recommended for a clean run)**

```bash
dropdb   -h 127.0.0.1 -U djangouser --if-exists serviz_db_parity
createdb -h 127.0.0.1 -U djangouser -O djangouser serviz_db_parity
```

**Option B — copy structure + data from an existing DB**

```bash
dropdb   -h 127.0.0.1 -U djangouser --if-exists serviz_db_parity
createdb -h 127.0.0.1 -U djangouser -T serviz_db serviz_db_parity
```

Point Django at the clone only for this checklist (shell export or temporary `.env`):

- `SDTA_DB_NAME=serviz_db_parity`
- Keep `SDTA_DB_USER`, `SDTA_DB_PASSWORD`, `SDTA_MIGRATION_DB_*`, and host/port aligned with how you run the real app.

---

## 3. Migrations on the clone

From the `service03` directory (with your normal virtualenv activated):

```bash
python manage.py migrate
```

If you use separate DB aliases with **different** users in production, run migrations as the migration-capable user (see comments in [scripts/setup_postgres.sql](scripts/setup_postgres.sql)).

---

## 4. Apply Row-Level Security policies

RLS scripts assume tables already exist (after migrations).

```bash
psql -h 127.0.0.1 -U djangouser -d serviz_db_parity -f scripts/setup_rls.sql
```

Re-run after adding new `TenantModel` tables if those table names are not yet listed in [scripts/setup_rls.sql](scripts/setup_rls.sql).

---

## 5. Optional — quick RLS smoke check in `psql`

Requires a role **subject to** RLS (e.g. `sdta_app`). Replace UUIDs with real `tenant_id` values from your data.

```sql
-- As sdta_app (not a superuser):
SET app.current_tenant_id = '00000000-0000-0000-0000-000000000001';
SELECT COUNT(*) FROM crm_customer;

SET app.current_tenant_id = '00000000-0000-0000-0000-000000000002';
SELECT COUNT(*) FROM crm_customer;
```

Counts should only reflect rows for the UUID you set (if RLS applies to that role). If both sessions see everything, the connected role likely bypasses RLS.

---

## 6. Run Django with **production** settings (not `settings_test`)

Use [config/settings.py](config/settings.py) (default `manage.py` behavior).

```bash
python manage.py runserver 0.0.0.0:8001
```

Confirm in [service03/.env](service03/.env) (or your environment):

| Variable | Parity intent |
|----------|----------------|
| `DEBUG` | `False` for closest match to production |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` / `SECURE_SSL_REDIRECT` | `True` when testing over **HTTPS**; keep your current local `False` only for plain HTTP on localhost |
| `INTERNAL_API_KEY` | Set to a long random value if you will hit `/internal/api/` |
| `CELERY_BROKER_URL` | Points at a real broker if you exercise async tasks |

**What this step validates that tests skip:**

- `django-csp` middleware and `CONTENT_SECURITY_POLICY` (admin pages should load; browser console should not report blocked scripts/styles you expect to allow).
- `django-axes` middleware and lockout behavior (failed logins; confirm lockout and cool-off match [config/settings.py](config/settings.py)).

---

## 7. Manual admin checks (staff user)

1. Open `/admin/`, sign in as a `StaffUser`.
2. Open a **changelist** and a **change** view for a tenant-scoped model (e.g. Customer, Department).
3. Confirm **no 500** and that lists respect how you expect staff to work (cross-tenant visibility uses the **worker** DB user in production).

If change views fail only on the clone after RLS is enabled, verify the **worker** alias uses a role with `BYPASSRLS` (or equivalent) as designed in the database spec.

---

## 8. Internal API surface

Middleware requires `Authorization: Bearer <INTERNAL_API_KEY>` for paths under `/internal/api/`. [infrastructure/internal_urls.py](infrastructure/internal_urls.py) may still be empty; expect **404** on undefined routes, not **401**, when the key is valid.

---

## 9. Record results

Use a short log (date, DB name, roles used, pass/fail per section 5–8). No need to commit secrets or production URLs into the repo.

---

## Reference — automated suite vs this checklist

| Concern | `config.settings_test` + `manage.py test` | This checklist |
|---------|---------------------------------------------|----------------|
| PostgreSQL engine | Yes | Yes |
| CSP | Removed in test settings | Exercise with default settings |
| django-axes | Disabled in test settings | Exercise with default settings |
| `setup_rls.sql` on DB | Not applied by Django | Applied manually to clone |
| `TenantModelAdmin` + `worker` connection | See test notes in [tests/test_admin.py](tests/test_admin.py) | Real admin + real two-role setup |

When this checklist passes on a clone with **split DB roles**, you have much stronger assurance that security and CRUD paths match the intended architecture than the unit/integration suite alone.
