# ServizDesk Multi-Tenancy Technical Specification (SDTA)
**Document Version:** V1
**Status:** Working Draft (Resolves Gap 3.2)

## 1. Overview
This document defines the implementation details for multi-tenant isolation in the ServizDesk Tenant App (SDTA). It ensures that all data access is automatically scoped to the correct tenant at the ORM layer, with PostgreSQL Row-Level Security (RLS) as the final enforcement layer.

## 2. Global Tenant Context
To ensure async-safety and thread-safety in Django 6.x, we use `asgiref.local.Local` to store the active tenant ID for the current request context.

```python
from asgiref.local import Local

_thread_locals = Local()

def set_current_tenant_id(tenant_id):
    _thread_locals.tenant_id = tenant_id

def get_current_tenant_id():
    return getattr(_thread_locals, 'tenant_id', None)

def clear_current_tenant_id():
    if hasattr(_thread_locals, 'tenant_id'):
        del _thread_locals.tenant_id
```

## 3. Tenant Manager (`TenantManager`)
The `TenantManager` overrides `get_queryset` to automatically inject the `tenant_id` filter.

```python
from django.db import models

class TenantManager(models.Manager):
    def get_queryset(self):
        tenant_id = get_current_tenant_id()
        # If no tenant is set (e.g., system task), return all rows
        # but RLS will still block unauthorized access in production.
        if tenant_id:
            return super().get_queryset().filter(tenant_id=tenant_id)
        return super().get_queryset()
```

### 3.1 Bulk Creation & Filtering
- **`.create()`**: The manager does not need to override `.create()` directly, as the `TenantModel.save()` method handles auto-injection (see Section 4).
- **`.raw()`**: Raw SQL bypasses the manager. These queries MUST be manually scoped by the developer, with PostgreSQL RLS serving as the fallback enforcement.

## 4. Base Tenant Model (`TenantModel`)
All tenant-scoped models must inherit from `TenantModel`.

```python
class TenantModel(models.Model):
    tenant_id = models.UUIDField(db_index=True, editable=False)
    
    objects = TenantManager()
    all_objects = models.Manager() # Bypass filter for system use

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        current_tenant_id = get_current_tenant_id()
        
        if not self.tenant_id:
            if current_tenant_id:
                self.tenant_id = current_tenant_id
            else:
                raise ValueError("Cannot save TenantModel without a tenant_id in context.")
        
        # Security Guard: Prevent cross-tenant data corruption
        if current_tenant_id and self.tenant_id != current_tenant_id:
            raise PermissionError("Tenant ID mismatch: Attempted to save data for a different tenant.")
            
        super().save(*args, **kwargs)
```

## 5. Middleware Injection
The `TenantMiddleware` extracts the `tenant_id` from the authenticated user and sets both the Python-level context (used by `TenantManager`) and the PostgreSQL-level context (used by RLS) simultaneously.

```python
from django.db import connection, transaction
from .tenant_context import set_current_tenant_id, clear_current_tenant_id

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Set Python-level context so TenantManager filters correctly
        set_current_tenant_id(request.user.tenant_id)
        try:
            # Wrap the request in a transaction so SET LOCAL persists for all
            # ORM calls within the view. SET LOCAL is transaction-scoped in
            # PostgreSQL and has no effect outside a transaction.
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SET LOCAL app.current_tenant_id = %s",
                        [str(request.user.tenant_id)]
                    )
                response = self.get_response(request)
        finally:
            # CRITICAL: Always clear context to prevent leak to next request
            clear_current_tenant_id()

        return response
```

> **Why `transaction.atomic()` is required here:** `SET LOCAL` in PostgreSQL is transaction-scoped. Without a surrounding transaction, the setting applies only for the duration of the implicit one-statement transaction used for the `SET LOCAL` command itself, and is gone by the time the next query executes. Wrapping `get_response(request)` in `transaction.atomic()` ensures the tenant context persists for every ORM operation inside the view.

## 6. Exclusive Arc Integration
When dealing with the "Exclusive Arc" pattern (Notes, Documents), the `TenantModel` logic ensures that even if a developer provides a parent object (e.g., `Note.objects.create(customer=customer_obj)`), the `tenant_id` is validated to ensure it matches the note's context.

## 7. Security Constraints Summary
| Action | Enforcement Mechanism |
|---|---|
| **ORM Query** | `TenantManager` injects `.filter(tenant_id=...)` |
| **ORM Create** | `TenantModel.save()` auto-populates `tenant_id` |
| **Cross-Tenant Write** | `TenantModel.save()` raises `PermissionError` on mismatch |
| **Raw SQL** | PostgreSQL Row-Level Security (Layer 3) |
| **System Tasks (cross-tenant reads)** | Use `model.all_objects` with the `'worker'` DB alias (`sdta_migration`, BYPASSRLS) |
| **Provisioning / Seeding** | Manually set Python context + `SET LOCAL` before first write (Section 8) |
| **Login / Password Reset** | Resolve tenant from `SubdomainIndex` before authenticating user (Section 9) |
| **Per-Tenant Celery Tasks** | Call `set_current_tenant_id(tenant_id)` at task start before any record creation (Section 10) |
| **Management Commands** | Use `'worker'` DB alias for cross-tenant queries; set context for per-tenant writes (Section 11) |
| **Backend / Support Staff Access** | Use `sdta_support` role (BYPASSRLS, DML-only, vault-locked) (Section 12) |

---

## 8. Provisioning Bootstrap — Setting Tenant Context Without a User

**Problem (Chicken-and-Egg):** When the SDP calls `POST /provision-tenant/`, no user exists yet. `TenantMiddleware` does not run because the request is not authenticated. Without tenant context, any attempt to create seed records via `TenantModel.save()` will raise `ValueError: Cannot save TenantModel without a tenant_id in context.`

**Solution:** The provisioning view must manually set both the Python-level context (`set_current_tenant_id`) and the PostgreSQL-level context (`SET LOCAL`) before executing any database writes.

```python
@api_view(['POST'])
@require_internal_api_key
def provision_tenant(request):
    payload = validate_provision_payload(request.data)
    tenant_id = payload['tenant_id']

    # Step 1: Set Python-level context so TenantModel.save() doesn't raise ValueError
    set_current_tenant_id(tenant_id)
    try:
        with transaction.atomic():
            # Step 2: Set PostgreSQL-level context so RLS policy allows the INSERT
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.current_tenant_id = %s", [str(tenant_id)])

            # Step 3: Create all seed records — both layers are now set
            _create_seed_records(payload)

        return Response({"status": "ok", "tenant_id": str(tenant_id)}, status=201)
    finally:
        # Always clear Python context on exit
        clear_current_tenant_id()
```

**Rule:** Both calls are required. `set_current_tenant_id` satisfies `TenantModel.save()`. `SET LOCAL app.current_tenant_id` satisfies the PostgreSQL RLS policy. Neither alone is sufficient.

---

## 9. Pre-Authentication Subdomain Resolver (Login & Password Reset)

**Problem:** The login and password-reset flows must look up the `User` record by email before authentication completes. `TenantMiddleware` has not yet run (no authenticated user), so `app.current_tenant_id` is not set. The RLS policy will block all `User` table reads.

**Solution:** Use a dedicated `SubdomainIndex` lookup table that is **exempt from tenant RLS** (it has no `tenant_id` column). The application resolves the tenant from the request subdomain before attempting any authenticated query.

### SubdomainIndex Table
```python
class SubdomainIndex(models.Model):
    """
    Non-tenant-scoped table. Maps subdomain → tenant_id for pre-auth resolution.
    Written by the provisioning flow. Read-only at runtime.
    No RLS policy — sdta_app has direct DML access.
    """
    subdomain = models.CharField(max_length=63, unique=True, db_index=True)
    tenant_id = models.UUIDField(db_index=True)

    class Meta:
        db_table = 'subdomain_index'
```

### Pre-Auth Resolver Pattern
```python
def resolve_tenant_from_subdomain(request) -> uuid.UUID | None:
    """
    Extracts the subdomain from the request host and returns the tenant_id.
    Called at the top of login and password-reset views before any User lookup.
    """
    host = request.get_host().split(':')[0]       # e.g. "acme.servizdesk.com"
    subdomain = host.split('.')[0]                 # e.g. "acme"
    try:
        return SubdomainIndex.objects.get(subdomain=subdomain).tenant_id
    except SubdomainIndex.DoesNotExist:
        return None
```

### Login View Pattern
```python
def login_view(request):
    tenant_id = resolve_tenant_from_subdomain(request)
    if not tenant_id:
        # Return 400 for any unknown subdomain — does not confirm or deny
        # whether the subdomain has ever been registered.
        return HttpResponseBadRequest("Invalid login URL.")

    set_current_tenant_id(tenant_id)
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # SET LOCAL is transaction-scoped in PostgreSQL.
                # MUST be inside transaction.atomic() or it has no effect.
                cursor.execute("SET LOCAL app.current_tenant_id = %s", [str(tenant_id)])

            # Now safe to query User table — RLS is satisfied
            user = authenticate(request, username=request.POST['email'], password=request.POST['password'])
            # ... MFA intermediate token flow follows authenticate().
            # See Technical Architecture Specification V2, Section 8.6 for the
            # full login sequence including MFA challenge and session establishment.
    finally:
        clear_current_tenant_id()
```

**Rule:** `SubdomainIndex` must be populated by the provisioning flow at tenant creation time and must be cleaned up when the tenant is deleted. The `purge_deleted_tenant_data` Celery task is responsible for deleting the `SubdomainIndex` row as the final step of tenant hard-delete (after `TenantState` is deleted). See Database Specification V2, Section 10.2. Failure to delete this row permanently claims the subdomain and prevents future tenants from using it.

### Password Reset Token Expiry

Django's default `PASSWORD_RESET_TIMEOUT` is 3 days. This must be overridden in `settings.py`:

```python
# settings.py
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours (in seconds). Django default is 259200 (3 days).
```

Reset tokens are cryptographically signed by Django using `SECRET_KEY` and include a timestamp. Django validates the signature and checks the token age on use — tokens older than `PASSWORD_RESET_TIMEOUT` seconds are automatically rejected. Tokens are also single-use: Django records that the token has been consumed and will reject any attempt to reuse the same link.

**Why 24 hours:** A reset link that sits unused in an email inbox for 3 days is a meaningful attack window if that inbox is later compromised. 24 hours is the standard for B2B applications handling financial data and provides a reasonable window for employees to act on the link without creating unnecessary exposure.

---

## 10. Per-Tenant Celery Tasks — Setting Context Before Record Creation

**Problem:** Celery workers execute tasks outside of any HTTP request cycle. `TenantMiddleware` does not run. If a per-tenant task creates records (e.g., `generate_pm_work_orders`, `generate_recurring_invoices`), `TenantModel.save()` will raise `ValueError` because no tenant context is set.

**Solution:** Per-tenant tasks must call `set_current_tenant_id(tenant_id)` at the very start of execution, before any database write.

```python
@shared_task(bind=True, max_retries=3)
def generate_pm_work_orders(self, tenant_id: str):
    """
    Background task: auto-generate Work Orders for active Preventative Maintenance records.
    Must set tenant context before any TenantModel.save() call.
    """
    set_current_tenant_id(uuid.UUID(tenant_id))
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.current_tenant_id = %s", [tenant_id])

            # Now safe to create Work Order records
            _run_pm_generation_for_tenant(tenant_id)

    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    finally:
        clear_current_tenant_id()
```

**Rules:**
1. `set_current_tenant_id` must be called before any `TenantModel.save()`.
2. `SET LOCAL app.current_tenant_id` must be set inside the `transaction.atomic()` block before any ORM write.
3. `clear_current_tenant_id()` must always be called in a `finally` block to prevent context leaking between tasks on the same worker thread.

**Cross-tenant reads within a task** (e.g., iterating all active tenants to dispatch per-tenant sub-tasks) must use `Model.all_objects.using('worker')` — the `'worker'` alias connects as `sdta_migration` (BYPASSRLS). See Database Specification V2 Section 4.2 for alias configuration.

---

## 11. Management Commands

**Problem:** Django management commands (`manage.py`) run outside of any request context. `TenantMiddleware` does not run.

**Rules by use case:**

- **Cross-tenant reads** (e.g., iterating all tenants for a maintenance script): Use `Model.all_objects.using('worker')`. The `'worker'` alias connects as `sdta_migration` (BYPASSRLS), which can read all rows without a tenant context set.

- **Per-tenant writes** (e.g., backfilling data for a specific tenant): Call `set_current_tenant_id(tenant_id)` and `SET LOCAL app.current_tenant_id` before any write, then call `clear_current_tenant_id()` in a `finally` block. Same pattern as Section 10.

- **DDL / schema operations**: Always run via `manage.py migrate`, which uses `sdta_migration`. Never run DDL through `sdta_app`.

```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        # Cross-tenant read using worker alias (BYPASSRLS)
        tenants = TenantState.all_objects.using('worker').filter(status='Active')
        for tenant in tenants:
            set_current_tenant_id(tenant.id)
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute("SET LOCAL app.current_tenant_id = %s", [str(tenant.id)])
                    _backfill_tenant(tenant.id)
            finally:
                clear_current_tenant_id()
```

---

## 12. Backend / Support Staff Access

**Problem:** Backend staff and support engineers occasionally need direct database access for investigation, diagnostics, or manual data correction. The `sdta_app` role is subject to RLS and cannot see across tenants. The `sdta_migration` role has full DDL privileges and is too powerful for interactive use.

**Solution:** A dedicated `sdta_support` role provides cross-tenant DML access without DDL privileges.

| Property | Value |
|---|---|
| Role | `sdta_support` |
| `BYPASS RLS` | `TRUE` — can read all tenant rows without setting `app.current_tenant_id` |
| Privileges | `SELECT`, `INSERT`, `UPDATE`, `DELETE` on all tables — **no DDL** (no CREATE, ALTER, DROP) |
| Sequences | `USAGE` only — can advance sequences for INSERT but cannot create or drop them |
| Credentials | Vault-locked. Not distributed in environment configs. Issued individually to staff when needed and rotated after each support incident — credentials are checked out from the secrets vault per-incident and rotated upon check-in. |

**Rules:**
1. `sdta_support` credentials must never be embedded in any application or automation. They are for interactive human use only.
2. All actions performed under `sdta_support` must be logged (use `pg_audit` or equivalent).
3. `sdta_support` must never be granted DDL privileges. Schema changes go through `sdta_migration` only.
4. After completing a support session, the password must be rotated in the vault.
