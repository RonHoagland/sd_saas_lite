# ServizDesk — Internal REST API Specification V1
**Document Status:** Working Draft — V1
**Date:** March 2026
**Classification:** Internal — Confidential

---

## Document Purpose

This document defines the complete Internal REST API contract between the **ServizDesk Platform (SDP)** and the **ServizDesk Tenant App (SDTA)**. It specifies every endpoint, request payload, response format, authentication mechanism, error codes, and retry behavior.

This API is **private and internal only**. It is accessible exclusively over the private server network or localhost. No external traffic reaches these endpoints.

---

# 1. API Architecture Overview

## 1.1 Communication Model

| Direction | Method | Purpose |
|---|---|---|
| SDP → SDTA | Internal REST API | Provision tenant; update account status; push plan/seat/storage changes; unlock administrator |
| SDTA → SDP | Internal REST API | Notify of seat changes; notify of storage usage; request current plan/limit data; billing section data queries |

**Key Rules:**
- Neither application may write to the other's database directly — ever
- All inter-application data exchange must use this API
- The API is bound to the internal network interface only — not publicly routable
- All requests must be authenticated via a shared Internal API Key (see Section 2)

## 1.2 Base URLs

| Environment | SDTA Internal API Base URL | SDP Internal API Base URL |
|---|---|---|
| Local Dev | `http://localhost:8001/internal/api/v1` | `http://localhost:8000/internal/api/v1` |
| Staging | `http://sdta.internal:8001/internal/api/v1` | `http://sdp.internal:8000/internal/api/v1` |
| Production | `http://sdta.internal/internal/api/v1` | `http://sdp.internal/internal/api/v1` |

> **Security Note:** In production, these URLs are bound to the private network interface. They are never exposed on the public-facing Nginx virtual host. A firewall rule must block external access to port 8001 (SDTA internal) and the `/internal/` path prefix.

## 1.3 API Versioning

All endpoints are versioned under `/v1/`. When breaking changes are required, a new `/v2/` prefix is introduced. Both versions run in parallel during a defined migration window.

---

# 2. Authentication

## 2.1 Mechanism: Shared Internal API Key

A long-lived, high-entropy shared secret is established at deployment time for each environment. This key is **never rotated mid-session** — rotation requires a coordinated deployment of both SDP and SDTA.

**Header format:**

```
Authorization: Bearer <INTERNAL_API_KEY>
```

## 2.2 Key Management

| Item | Specification |
|---|---|
| Key length | Minimum 64 characters, cryptographically random (`secrets.token_hex(64)`) |
| Storage | Secrets vault only (DigitalOcean Secrets or equivalent) — never in source code |
| Environment variable | `INTERNAL_API_KEY` on both SDP and SDTA servers |
| Rotation | Rotate only during planned deployments with both applications updated simultaneously |
| Per-environment | Separate keys for local, staging, and production |

## 2.3 Key Validation (Django Middleware — Both Apps)

Both SDP and SDTA implement the same middleware for validating incoming internal API requests:

```python
class InternalAPIKeyMiddleware:
    """Applied only to URL paths starting with /internal/api/"""

    def __call__(self, request):
        if request.path.startswith('/internal/api/'):
            provided_key = request.headers.get('Authorization', '').removeprefix('Bearer ')
            expected_key = settings.INTERNAL_API_KEY
            # Use constant-time comparison to prevent timing attacks
            if not secrets.compare_digest(provided_key, expected_key):
                return JsonResponse({'error': 'Unauthorized'}, status=401)
        return self.get_response(request)
```

## 2.4 Celery & Background Workers

Celery tasks that call the Internal API use the same `INTERNAL_API_KEY`. The key is read from the environment at task execution time — it is never embedded in the task payload or stored in Redis.

```python
# Pattern for Celery tasks calling internal API
headers = {'Authorization': f'Bearer {settings.INTERNAL_API_KEY}'}
response = requests.post(f'{settings.SDTA_INTERNAL_BASE_URL}/provision-tenant/', 
                         json=payload, headers=headers, timeout=10)
```

---

# 3. Standard Response Envelopes

All responses follow a consistent JSON envelope.

## 3.1 Success Response

```json
{
    "status": "ok",
    "data": { ... }
}
```

## 3.2 Error Response

```json
{
    "status": "error",
    "error_code": "TENANT_ALREADY_EXISTS",
    "message": "A tenant with this ID already exists in SDTA.",
    "detail": { ... }
}
```

## 3.3 Standard HTTP Status Codes

| Code | Meaning |
|---|---|
| `200 OK` | Request succeeded; response body contains result |
| `201 Created` | Resource created successfully |
| `400 Bad Request` | Request payload invalid or missing required fields |
| `401 Unauthorized` | Missing or invalid `INTERNAL_API_KEY` |
| `404 Not Found` | Referenced resource does not exist |
| `409 Conflict` | Request conflicts with existing state (e.g., tenant already exists) |
| `422 Unprocessable Entity` | Payload valid but business rule violation (e.g., usage exceeds downgrade limit) |
| `500 Internal Server Error` | Unexpected error on the receiving application |
| `503 Service Unavailable` | Receiving application temporarily unable to process (triggers retry) |

---

# 4. SDP → SDTA Endpoints

These endpoints are implemented by **SDTA** and called by **SDP**.

---

## 4.1 `POST /provision-tenant/`

Creates a complete, fully initialized tenant workspace in SDTA. This is called during Phase 2 of the provisioning sequence. The entire operation executes as a single atomic database transaction.

**Retry behavior:** SDP retries this endpoint up to 3 times (5s delay, then 15s delay) on `5xx` or timeout. On total failure after 3 attempts, SDP flags the account as `PROVISIONING_FAILED` and raises a Critical System Alert.

### Request Payload

```json
{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "company_name": "Acme HVAC Services",
    "admin_email": "owner@acmehvac.com",
    "admin_first_name": "John",
    "admin_last_name": "Smith",
    "admin_temp_password_hash": "argon2$...",
    "tier": "lite",
    "seat_limit": 10,
    "storage_limit_bytes": 3221225472,
    "email_points_included": 400,
    "sms_points_included": 100,
    "billing_anniversary_date": "2026-03-10",
    "subdomain": "acmehvac"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `tenant_id` | UUID | ✓ | SDP-generated UUID; never reused |
| `company_name` | string | ✓ | Used to seed TenantPreference |
| `admin_email` | string | ✓ | Becomes the Administrator's SDTA login email |
| `admin_first_name` | string | ✓ | |
| `admin_last_name` | string | ✓ | |
| `admin_temp_password_hash` | string | ✓ | Pre-hashed with Argon2/bcrypt — SDTA stores as-is; never transmitted in plaintext |
| `tier` | enum | ✓ | `lite`, `plus`, `pro`, `enterprise` |
| `seat_limit` | integer | ✓ | Max active seats for this tenant |
| `storage_limit_bytes` | integer | ✓ | Storage cap in bytes (e.g., 3 GB = 3221225472) |
| `email_points_included` | integer | ✓ | Email points included in this tier (Lite = 400, Plus = 1,600, Pro = 4,000, Enterprise = 12,000). Lite is restricted to manual sends only; no automated triggers. Used to seed `TenantState.email_points_included` and `EmailUsageTracker`. See Pricing & Billing Specification V2 Section 10A.4. |
| `sms_points_included` | integer | ✓ | SMS points included in this tier (Lite = 100, Plus = 350, Pro = 750, Enterprise = TBD). Lite is restricted to manual sends only; no automated triggers. Used to seed `TenantState.sms_points_included` and `SMSUsageTracker`. See Pricing & Billing Specification V2 Section 10.2. |
| `billing_anniversary_date` | ISO 8601 date | ✓ | Date the billing cycle started. Used to seed `TenantState.email_period_start` and `TenantState.sms_period_start`. |
| `subdomain` | string | ✓ | Tenant's SDTA subdomain (e.g., `acmehvac` → `acmehvac.servizdesk.com`) |

### RLS Bootstrap — Required Before Any DB Write

**Critical:** Every table in SDTA has Row-Level Security (RLS) enforced. The standard `TenantMiddleware` sets the tenant context from `request.user.tenant_id`, but during provisioning no authenticated user exists yet — the Administrator is being created for the first time. Without manually establishing the context, both the Django ORM (`TenantModel.save()`) and PostgreSQL RLS will reject every INSERT.

The endpoint MUST set the tenant context explicitly from the payload **before** opening the atomic transaction:

```python
@api_view(['POST'])
@require_internal_api_key
def provision_tenant(request):
    payload = validate_provision_payload(request.data)
    tenant_id = payload['tenant_id']

    # Bootstrap tenant context — no authenticated user exists yet.
    # Must set both the Python-level context (for TenantModel.save())
    # and the PostgreSQL session variable (for RLS WITH CHECK).
    set_current_tenant_id(tenant_id)

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # SET LOCAL scopes this to the transaction only — cannot leak.
                cursor.execute("SET LOCAL app.current_tenant_id = %s", [str(tenant_id)])

            # All seed record creation follows here — context is now valid.
            _create_seed_records(payload)

        return Response({"status": "ok", ...}, status=201)
    finally:
        # Always clear — even on exception — to prevent context leak.
        clear_current_tenant_id()
```

> **Rule:** `set_current_tenant_id()` and `SET LOCAL app.current_tenant_id` must both be called. The Python-level call satisfies `TenantModel.save()`; the SQL call satisfies PostgreSQL RLS. One without the other will cause failures.

### SDTA Actions (All-or-Nothing Transaction)

SDTA executes the following in a single atomic transaction (after tenant context is established per the bootstrap pattern above):

1. Create `TenantState` record (`status=Active`, `tier`, `seat_limit`, `storage_limit_bytes`, `email_points_included`, `email_period_start` = `billing_anniversary_date`, `sms_points_included`, `sms_period_start` = `billing_anniversary_date`, `onboarding_wizard_completed=False`)
2. Create `TenantPreference` record (seed with `company_name`, `subdomain`, system defaults for all other fields)
3. Create Administrator `User` record (`email`, `first_name`, `last_name`, `password_hash`, `role=Administrator`, `status=Active`, employee number generated from the `E` prefix sequence)
4. Create `StorageTracker` record (`total_bytes_used=0`, `pending_bytes=0`)
5. Create `EmailUsageTracker` record (`email_points_used=0`, `email_points_overage=0`)
6. Create `SMSUsageTracker` record (`sms_points_used=0`, `sms_points_overage=0`)
7. Create `OnboardingState` record (`is_completed=False`, all checklist items initialized to `False`)
8. Create `SequenceTracker` records for all entity types (all tiers: Customer, Asset, WorkOrder, Quote, Invoice, Payments, Task, InventoryItem, Employee, ServiceRequest; Plus+: Vendor, PurchaseOrder, VendorBill, RMA, Requisition, WorkGroup, Agreement, PreventativeMaintenance, Lead; Pro+: Opportunity, WorkFlow, Equipment; Fleet Add-On: Vehicle). All `last_value` seeded to `0`. See Tenant Provisioning Seed Data Specification V2 Section 5.
9. Create initial `Notification` record: "Welcome to ServizDesk! Complete your setup with the onboarding checklist."

### Success Response — `201 Created`

```json
{
    "status": "ok",
    "data": {
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "admin_user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "provisioned_at": "2026-03-10T19:00:00Z"
    }
}
```

### Error Responses

| Code | Error Code | Meaning |
|---|---|---|
| `400` | `INVALID_PAYLOAD` | Missing or malformed required fields |
| `409` | `TENANT_ALREADY_EXISTS` | A TenantState record with this `tenant_id` already exists |
| `500` | `PROVISIONING_FAILED` | Transaction failed; SDTA rolled back; safe to retry |

---

## 4.2 `POST /update-account-status/`

Updates the tenant's account status in SDTA. Used for suspension, reactivation, cancellation transitions, and read-only mode enforcement.

### Request Payload

```json
{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "suspended",
    "reason": "payment_failed",
    "effective_at": "2026-03-10T19:00:00Z"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `tenant_id` | UUID | ✓ | |
| `status` | enum | ✓ | See valid values below |
| `reason` | string | ✓ | Free text — logged in SDTA SystemAudits |
| `effective_at` | ISO 8601 datetime | ✓ | When the status change takes effect; SDTA may schedule if future |

**Valid `status` values:**

| API Value | DB `TenantState.status` Value | SDTA Behavior |
|---|---|---|
| `active` | `Active` | Full access restored for all users |
| `suspended` | `Suspended` | All employee logins blocked except Administrator (Admin Area only) |
| `read_only` | `Read Only` | All users can log in; no creates/edits/deletes permitted |
| `cancelled_pending_expiry` | `Cancelled (Pending Expiry)` | No new records; read/export access continues until billing period end |
| `cancelled_read_only` | `Cancelled (Read Only)` | All users can log in; no creates/edits/deletes permitted; 30-day window after billing period end before full access is revoked |
| `cancelled_expired` | `Cancelled` | All SDTA access revoked; 60-day data retention countdown begins |
| `pending_deletion` | `Pending Deletion` | Celery worker begins permanent hard-delete of all tenant data |

> **Implementation note:** SDTA must map the incoming snake_case API value to the corresponding `TenantState.status` DB enum value before persisting.

### Success Response — `200 OK`

```json
{
    "status": "ok",
    "data": {
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "previous_status": "active",
        "new_status": "suspended",
        "updated_at": "2026-03-10T19:00:00Z"
    }
}
```

### Error Responses

| Code | Error Code | Meaning |
|---|---|---|
| `404` | `TENANT_NOT_FOUND` | No TenantState record for this `tenant_id` |
| `422` | `INVALID_STATUS_TRANSITION` | The requested status transition is not permitted (e.g., `pending_deletion` → `active`) |

---

## 4.3 `POST /update-limits/`

Updates the tenant's seat limit, storage limit, and/or tier in SDTA. Called when a plan upgrade, downgrade, seat purchase, or storage add-on is processed.

### Request Payload

```json
{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "tier": "plus",
    "seat_limit": 25,
    "storage_limit_bytes": 10737418240,
    "email_points_included": 1600,
    "sms_points_included": 350,
    "add_ons": {
        "fleet": { "status": "active" },
        "extra_storage": { "status": "active", "unit_limit": 5368709120 }
    }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `tenant_id` | UUID | ✓ | |
| `tier` | enum | ✗ | Omit if tier is not changing |
| `seat_limit` | integer | ✗ | Omit if seat limit is not changing |
| `storage_limit_bytes` | integer | ✗ | Omit if storage limit is not changing |
| `email_points_included` | integer | ✗ | Omit if email allocation is not changing. Required when tier changes. |
| `sms_points_included` | integer | ✗ | Omit if SMS allocation is not changing. Required when tier changes. |
| `add_ons` | object | ✗ | Dictionary of add-on details (type: {status, unit_limit}) |

**Note:** At least one of `tier`, `seat_limit`, `storage_limit_bytes`, `email_points_included`, `sms_points_included`, or `add_ons` must be provided.

### SDTA Actions

1. Update `TenantState` with any changed values
2. If `tier` changes, log a `TenantSyncLog` record
3. If new `storage_limit_bytes` is less than current `StorageTracker.total_bytes_used` → return `422 STORAGE_USAGE_EXCEEDS_NEW_LIMIT` (SDP must enforce this check before calling; this is a safety valve)
4. Emit an in-app `Notification` to the Administrator confirming the plan/limit change

### Success Response — `200 OK`

```json
{
    "status": "ok",
    "data": {
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "tier": "plus",
        "seat_limit": 25,
        "storage_limit_bytes": 10737418240,
        "updated_at": "2026-03-10T19:00:00Z"
    }
}
```

### Error Responses

| Code | Error Code | Meaning |
|---|---|---|
| `400` | `NO_CHANGES_PROVIDED` | All optional fields omitted |
| `404` | `TENANT_NOT_FOUND` | |
| `422` | `STORAGE_USAGE_EXCEEDS_NEW_LIMIT` | Cannot lower storage limit below current usage |

---

## 4.4 `POST /unlock-administrator/`

Unlocks a locked Administrator account. Called by SDP after successful account recovery verification. Uses the same 3-retry pattern as provisioning.

### Request Payload

```json
{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "admin_email": "owner@acmehvac.com",
    "new_password_hash": "argon2$..."
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `tenant_id` | UUID | ✓ | |
| `admin_email` | string | ✓ | Identifies which User record to unlock |
| `new_password_hash` | string | ✓ | Pre-hashed replacement password |

### SDTA Actions

1. Look up the User record by `tenant_id` + `admin_email`
2. Verify the User has the Administrator role
3. Clear `failed_login_count` → 0
4. Update `password` to `new_password_hash`
5. Set `status = Active`
6. Log an `SystemAudits`: `action=Unlocked, entity_type=User, entity_id=<user_id>`

### Success Response — `200 OK`

```json
{
    "status": "ok",
    "data": {
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "unlocked_at": "2026-03-10T19:00:00Z"
    }
}
```

### Error Responses

| Code | Error Code | Meaning |
|---|---|---|
| `404` | `TENANT_NOT_FOUND` | No TenantState for this `tenant_id` |
| `404` | `USER_NOT_FOUND` | No User matching `admin_email` on this tenant |
| `422` | `NOT_ADMINISTRATOR` | Matched user does not have the Administrator role |

---

## 4.5 `POST /sync-tenant-state/`

Full re-sync of a tenant's state from SDP. Used after a TenantSyncLog failure or on staff-initiated force-sync from the SDP back office.

### Request Payload

```json
{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "tier": "lite",
    "status": "active",
    "seat_limit": 10,
    "storage_limit_bytes": 3221225472,
    "email_points_included": 400,
    "email_period_start": "2026-03-10",
    "sms_points_included": 100,
    "sms_period_start": "2026-03-10",
    "add_ons": {
        "fleet": { "status": "active" }
    }
}
```

### SDTA Actions

Overwrites the entire `TenantState` record with the provided values. Logs a `TenantSyncLog` record with `sync_type=ForcedResync`.

### Success Response — `200 OK`

```json
{
    "status": "ok",
    "data": {
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "synced_at": "2026-03-10T19:00:00Z"
    }
}
```

---

# 5. SDTA → SDP Endpoints

These endpoints are implemented by **SDP** and called by **SDTA**.

---

## 5.1 `GET /tenant-state/{tenant_id}/`

Retrieves the current authoritative state for a tenant from SDP. SDTA calls this to refresh its local `TenantState` cache (e.g., on cache miss or scheduled background sync).

### Response — `200 OK`

```json
{
    "status": "ok",
    "data": {
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "tier": "lite",
        "status": "active",
        "seat_limit": 10,
        "storage_limit_bytes": 3221225472,
        "email_points_included": 400,
        "email_period_start": "2026-03-10",
        "sms_points_included": 100,
        "sms_period_start": "2026-03-10",
        "billing_cycle": "monthly",
        "next_billing_date": "2026-04-10",
        "add_ons": {
            "fleet": { "status": "active" }
        }
    }
}
```

---

## 5.2 `POST /notify-seat-change/`

Called by SDTA whenever an employee is created or terminated, to keep SDP's active seat count in sync for display and reporting purposes.

> **⚠️ Purchased Seats Model — Critical Design Note:**
> ServizDesk uses a **Purchased Seats** billing model. This endpoint reports active seat utilization to SDP for informational purposes only. It does **NOT** modify the Stripe subscription quantity.
>
> Stripe subscription quantity (= purchased seat count, reflected as `TenantState.seat_limit` in SDTA) is only updated when a tenant explicitly **purchases additional seats** or **releases vacant seats** from the Billing section in SDTA. Both of those actions are processed entirely within SDP and communicated to SDTA via the `/update-limits/` endpoint.
>
> When an employee is set to Terminated, their seat becomes vacant but the purchased seat count is unchanged — the tenant continues to be billed for the same number of seats until they explicitly remove the vacant seat from their plan in the Billing section. See Pricing & Billing Specification V2 Section 3.3.

### Request Payload

```json
{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "active_seat_count": 7,
    "employee_id": "uuid-of-the-changed-employee",
    "change_type": "added"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `tenant_id` | UUID | ✓ | |
| `active_seat_count` | integer | ✓ | Current count of non-Terminated employees (Active + On Leave + Inactive) after the change |
| `employee_id` | UUID | ✓ | The employee that was added or terminated |
| `change_type` | enum | ✓ | `added` (new employee created), `terminated` (employee set to Terminated) |

**Seat counting rules:** Active + On Leave + Inactive employees count toward `active_seat_count`. Terminated employees (with `termination_date` populated) do not count.

**SDTA enforcement:** Before creating a new employee, SDTA must check that the resulting `active_seat_count` would not exceed `TenantState.seat_limit`. If it would, SDTA must block the creation and display an upgrade prompt. This endpoint is called only after the employee record has been successfully created or terminated.

### Success Response — `200 OK`

```json
{
    "status": "ok",
    "data": {
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "seat_count_acknowledged": 7
    }
}
```

### Error Responses

| Code | Error Code | Meaning |
|---|---|---|
| `422` | `SEAT_COUNT_EXCEEDS_PURCHASED` | `active_seat_count` exceeds the tenant's `seat_limit`; indicates SDTA failed to enforce the limit before calling — investigate |

---

## 5.3 `POST /notify-storage-change/`

Called by SDTA whenever a Document is uploaded or deleted, updating the running storage usage total in SDP.

### Request Payload

```json
{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "total_bytes_used": 1073741824
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `tenant_id` | UUID | ✓ | |
| `total_bytes_used` | integer | ✓ | Current total bytes used (not a delta — always the full current value from `StorageTracker`) |

### Success Response — `200 OK`

```json
{
    "status": "ok",
    "data": {
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "bytes_acknowledged": 1073741824,
        "storage_limit_bytes": 3221225472,
        "usage_percentage": 33.3
    }
}
```

---

## 5.4 `GET /billing-summary/{tenant_id}/`

Called by SDTA to populate the Billing section UI. Returns all billing data that SDTA needs to display to the tenant Administrator.

### Response — `200 OK`

```json
{
    "status": "ok",
    "data": {
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "plan": "lite",
        "billing_cycle": "monthly",
        "current_seats": 7,
        "seat_limit": 10,
        "seat_price_per_month": 27.00,
        "next_billing_date": "2026-04-10",
        "payment_method": {
            "last4": "4242",
            "brand": "visa",
            "exp_month": 12,
            "exp_year": 2028
        },
        "storage_included_bytes": 3221225472,
        "storage_used_bytes": 1073741824,
        "storage_add_ons": [],
        "account_status": "active",
        "recent_invoices": [
            {
                "period": "March 2026",
                "amount": 189.00,
                "status": "paid",
                "stripe_invoice_url": "https://stripe.com/..."
            }
        ]
    }
}
```

---

## 5.5 `POST /request-plan-change/`

Called by SDTA when a tenant Administrator requests an upgrade or downgrade from the Billing section.

### Request Payload

```json
{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "requested_tier": "plus",
    "billing_cycle": "monthly",
    "initiated_by_user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
}
```

### SDP Actions

1. Validate the requested tier change (check usage against lower plan limits for downgrades)
2. Initiate Stripe subscription update (proration handled by Stripe)
3. Call SDTA `/update-limits/` to push the new tier and limits
4. Log the plan change in the SDP audit log
5. Send plan change confirmation email to billing email

### Success Response — `200 OK`

```json
{
    "status": "ok",
    "data": {
        "new_tier": "plus",
        "effective_at": "2026-03-10T19:00:00Z",
        "proration_credit": 15.23
    }
}
```

### Error Responses

| Code | Error Code | Meaning |
|---|---|---|
| `422` | `SEAT_COUNT_EXCEEDS_TIER_LIMIT` | Current seat count exceeds lower tier limit |
| `422` | `STORAGE_USAGE_EXCEEDS_TIER_LIMIT` | Current storage usage exceeds lower tier limit |

---

# 6. Retry & Timeout Policy

## 6.1 SDP Calling SDTA (Provisioning & Critical Operations)

| Endpoint | Timeout | Retry Attempts | Retry Delays | On Total Failure |
|---|---|---|---|---|
| `POST /provision-tenant/` | 10s | 3 | 5s, 15s | Flag `PROVISIONING_FAILED`; raise Critical Alert |
| `POST /unlock-administrator/` | 10s | 3 | 5s, 15s | Show user "try again in a few minutes" |
| `POST /update-account-status/` | 10s | 3 | 5s, 15s | Flag `SYNC_FAILED`; raise Critical Alert |
| `POST /update-limits/` | 10s | 3 | 5s, 15s | Flag `SYNC_FAILED`; raise Critical Alert |
| `POST /sync-tenant-state/` | 10s | 1 | — | Log `TenantSyncLog` failure |

## 6.2 SDTA Calling SDP (Notifications & Data Fetches)

| Endpoint | Timeout | Retry Attempts | Retry Delays | On Total Failure |
|---|---|---|---|---|
| `POST /notify-seat-change/` | 5s | 3 | 2s, 5s | Log `TenantSyncLog` failure; Celery task retries on next background cycle |
| `POST /notify-storage-change/` | 5s | 3 | 2s, 5s | Log failure; StorageTracker remains authoritative in SDTA; retry on next upload |
| `GET /tenant-state/{tenant_id}/` | 5s | 2 | 2s | Serve from cached `TenantState`; attempt refresh on next request |
| `GET /billing-summary/{tenant_id}/` | 8s | 2 | 3s | Return error to UI — user sees "Unable to load billing information. Please try again." |
| `POST /request-plan-change/` | 10s | 1 | — | Show error to user; no retry — user must re-initiate |

## 6.3 Idempotency

All `POST` endpoints on SDTA must be idempotent. SDP may safely retry any call without risk of duplicate processing.

**Implementation pattern for `provision-tenant`:** SDTA checks for an existing `TenantState` record with the provided `tenant_id` before executing. If found, it returns `409 TENANT_ALREADY_EXISTS` — SDP treats this as success (the resource already exists) and proceeds with the provisioning flow.

---

# 7. Celery Background Workers & RLS Bypass

## 7.1 The Problem

Certain Celery background tasks operate across all tenants simultaneously (e.g., the post-cancellation data deletion worker — which fires after the full 90-day window: 30-day `Cancelled (Read Only)` + 60-day `Cancelled` data retention — the storage reconciliation job, the audit event purge). These tasks cannot set `app.current_tenant_id` to a single tenant's UUID because they need to process multiple tenants' data.

## 7.2 Solution: Dedicated Non-RLS Database Connection

Background workers use a separate Django database alias configured with the `sdta_migration` database role, which has `BYPASSRLS = TRUE`. This is defined as a second entry in Django's `DATABASES` setting.

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'USER': env('SDTA_DB_USER'),          # sdta_app — subject to RLS
        ...
    },
    'worker': {
        'ENGINE': 'django.db.backends.postgresql',
        'USER': env('SDTA_WORKER_DB_USER'),   # sdta_migration — bypasses RLS
        'PASSWORD': env('SDTA_WORKER_DB_PASSWORD'),
        ...
    }
}
```

Background workers explicitly use the `'worker'` database alias:

```python
# In Celery task
with transaction.atomic(using='worker'):
    TenantState.objects.using('worker').filter(
        status='Pending Deletion',
        deletion_scheduled_at__lte=timezone.now()
    ).values_list('tenant_id', flat=True)
```

## 7.3 Rule: Worker DB Alias is Celery-Only

The `'worker'` database alias must never be used in Django views, middleware, or any request-cycle code. It is exclusively for Celery tasks. Misuse of this alias in request-cycle code would completely bypass tenant isolation.

A linting rule or code review checklist item should enforce this prohibition.

## 7.4 Per-Tenant Iteration Pattern

When a background worker must operate on multiple tenants, it iterates per tenant and optionally scopes its queries by tenant:

```python
@app.task
def run_deletion_worker():
    tenant_ids = TenantState.objects.using('worker').filter(
        status='Pending Deletion',
        deletion_scheduled_at__lte=timezone.now()
    ).values_list('tenant_id', flat=True)

    for tenant_id in tenant_ids:
        delete_tenant_data.delay(str(tenant_id))  # Dispatch per-tenant sub-task

@app.task
def delete_tenant_data(tenant_id: str):
    with transaction.atomic(using='worker'):
        # Delete in dependency order — leaf tables first
        Note.objects.using('worker').filter(tenant_id=tenant_id).delete()
        Document.objects.using('worker').filter(tenant_id=tenant_id).delete()
        # ... continue through all tables
        TenantState.objects.using('worker').filter(tenant_id=tenant_id).delete()
```

---

# 8. Logging & Observability

## 8.1 `TenantSyncLog` (SDTA)

Every Internal API call that SDTA receives from SDP is logged in `TenantSyncLog`:

| Field | Notes |
|---|---|
| `tenant_id` | The affected tenant |
| `sync_type` | e.g., `ProvisionTenant`, `UpdateStatus`, `UpdateLimits`, `UnlockAdmin`, `ForceSync` |
| `occurred_at` | Timestamp |
| `status` | `Success`, `Failed` |
| `request_payload` | Sanitized JSON of the inbound payload (no password hashes) |
| `response_code` | HTTP status returned |
| `details` | Error message if failed |

## 8.2 SDP Internal API Request Log

Every Internal API call SDP makes to SDTA is logged in SDP's equivalent audit/request log, capturing: endpoint, payload hash, response code, duration_ms, retry count.

## 8.3 Critical System Alert Triggers

The following conditions must generate a Critical System Alert visible on the SDP Staff Dashboard:

| Trigger | Severity |
|---|---|
| `provision-tenant` returns 5xx after 3 retries | P0 — Immediate |
| `update-account-status` fails after 3 retries | P1 — Urgent |
| `unlock-administrator` fails after 3 retries | P1 — Urgent |
| Any SDTA Internal API endpoint returns `401` unexpectedly (key mismatch) | P0 — Immediate |

---

# 9. Security Hardening Checklist

| Item | Required |
|---|---|
| All Internal API endpoints bound to internal network interface only — not publicly routable | ✓ |
| Nginx blocks the `/internal/` path prefix on the public virtual host | ✓ |
| All requests validated against `INTERNAL_API_KEY` via constant-time comparison | ✓ |
| `INTERNAL_API_KEY` stored in secrets vault; never in source code | ✓ |
| Separate keys per environment (local, staging, production) | ✓ |
| Password hashes transmitted between SDP and SDTA — never plaintext passwords | ✓ |
| `TenantSyncLog` sanitizes payloads before storage (strips password hash fields) | ✓ |
| Worker database alias (`sdta_migration`) used only in Celery tasks, never in request-cycle code | ✓ |
| All endpoints are idempotent — safe to call multiple times with same payload | ✓ |
| API versioned at `/v1/` — breaking changes require new `/v2/` prefix | ✓ |

---

# 10. Document Relationships

| Relationship | Document |
|---|---|
| Governed by (inter-app architecture) | ServizDesk Technical Architecture V2, Sections 7.1–7.2 |
| Governed by (provisioning sequence) | ServizDesk Platform (SDP) Specification V2, Section 4 |
| Governed by (account lifecycle) | ServizDesk Platform (SDP) Specification V2, Sections 5–6 |
| Governed by (SDTA data models) | ServizDesk Data Models V6 |
| Governed by (database users/RLS) | ServizDesk Database Specification V2 |

---

*End of ServizDesk Internal REST API Specification V1*
