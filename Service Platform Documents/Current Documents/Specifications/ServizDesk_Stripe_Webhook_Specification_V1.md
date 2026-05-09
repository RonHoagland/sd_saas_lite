# ServizDesk Stripe Webhook Specification (SDTA)
**Document Version:** V1
**Status:** Working Draft (Resolves Gap 3.4)

## 1. Overview
This document defines how the SDTA backend receives, validates, and processes asynchronous payment notifications from Stripe. It ensures perfect data isolation and prevents duplicate processing.

## 2. Global Webhook Endpoint
SDTA exposes a single, shared endpoint for all Stripe traffic:
`POST /api/infrastructure/webhooks/stripe/`

### 2.1 Security Validation
1.  **Signature Verification**: The raw request body must be verified against the `STRIPE_WEBHOOK_SECRET` using the Stripe SDK's signature checker. Unverified requests must be rejected immediately (403 Forbidden).
2.  **IP Filtering (Optional)**: Requests can be optionally whitelist-filtered to known Stripe IP ranges.

## 3. Multi-Tenant Resolution
Because we use Stripe Connect, we must map external notifications to internal tenants.

1.  **Extract Account ID**: Every Connect webhook contains the Stripe account ID in the header: `Stripe-Account: acct_1ABC...`.
2.  **Database Lookup — Use the `'worker'` alias**:

    Stripe webhook requests arrive with no authenticated user. `TenantMiddleware` has not run, so `app.current_tenant_id` is not set. Even though `all_objects` bypasses the ORM's `TenantManager` filter, PostgreSQL RLS **still applies** — with no tenant context set, the RLS policy returns NULL and the query returns 0 rows.

    The fix is to use the `'worker'` database alias, which connects as `sdta_migration` (`BYPASSRLS = TRUE`), allowing the `StripeConnection` record to be found before tenant context is known:

    ```python
    # Step 1: Resolve tenant_id using the worker alias (BYPASSRLS)
    # 'worker' connects as sdta_migration, which has BYPASSRLS = TRUE
    stripe_conn = StripeConnection.all_objects.using('worker').select_related('tenant').get(
        stripe_account_id=acct_id,
        is_active=True
    )
    tenant_id = stripe_conn.tenant_id
    ```

3.  **Context Activation**: Once `tenant_id` is resolved, switch to the scoped application context for all subsequent processing. All remaining queries run through the default connection (`sdta_app`) with the tenant context set:

    ```python
    # Step 2: Activate tenant context for all subsequent queries
    set_current_tenant_id(tenant_id)
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.current_tenant_id = %s", [str(tenant_id)])
            # Step 3: All ORM queries and writes now run scoped to this tenant
            _process_webhook_event(event, tenant_id)
    finally:
        clear_current_tenant_id()
    ```

    **Rule:** The `'worker'` alias is used only for the initial `StripeConnection` lookup. All writes and subsequent reads must use the default connection with `app.current_tenant_id` set. This ensures RLS enforcement is maintained for all data modification operations.

## 4. Idempotency & Logging
To prevent double-counting payments due to Stripe retries or network errors:

1.  **Event Check**: Every Stripe event has a unique ID (e.g., `evt_123`).
2.  **`WebhookLog` Constraint**:
    *   On arrival, search `WebhookLog` for the event ID. This lookup occurs before tenant context is established, so it **must use the `'worker'` alias** (`sdta_migration`, `BYPASSRLS = TRUE`) to bypass RLS:
        ```python
        already_processed = WebhookLog.all_objects.using('worker').filter(
            stripe_event_id=event.id
        ).exists()
        if already_processed:
            return HttpResponse(status=200)
        ```
    *   If the ID exists, return `200 OK` immediately without re-processing.
3.  **Logging**: Store the full JSON payload, the resolved `tenant_id`, and the processing status (`Pending`, `Processed`, `Failed`).

## 5. Invoice Matching (Metadata)
When SDTA generates a payment (Checkout Session or Payment Intent), we MUST attach specific metadata keys:

| Key | Value Type | Usage |
|---|---|---|
| `tenant_id` | UUID | Final validation safety |
| `invoice_id` | UUID | Direct DB lookup (Target) |
| `source` | String | e.g., "InvoicePayment" |

### 5.1 Processing Logic
1.  Extract `invoice_id` and `tenant_id` from the Stripe `metadata` object.
2.  **Safety Check**: Verify that the `tenant_id` in metadata matches the `tenant_id` resolved from the Connecting Account header.
3.  **Record Update**: 
    ```python
    invoice = Invoice.objects.get(id=metadata['invoice_id'])
    # logic to mark paid, generate LedgerEntry, and emit SystemAudits
    ```

## 6. Handled Event Types

The following table is the authoritative registry of Stripe events handled by SDTA. Events not listed here are logged but not acted upon. SDP handles its own subset of Stripe events for platform-level billing.

| Event Type | Handler Action | Status Transition (if any) | Notes |
|---|---|---|---|
| `checkout.session.completed` | New subscription provisioning trigger | Subscription status → Active | SDP handles this; SDTA is notified of successful activation |
| `invoice.payment_succeeded` | Record successful payment, generate LedgerEntry | Account status → Active (if needed) | Updates Invoice.status to Paid, emits SystemAudit |
| `invoice.payment_failed` | Record failed payment, trigger dunning/retry logic | Account status → At Risk (if applicable) | Per Pricing spec Section 6.3; initiate retry sequence and notification |
| `customer.subscription.updated` | Process plan changes and seat count changes | Subscription adjustment recorded | Handles tier upgrades/downgrades and seat modifications; prorated billing applied |
| `customer.subscription.deleted` | Cancellation confirmed, trigger cancellation lifecycle | Subscription status → Cancelled | Initiates 30/60/90-day timeline per Pricing spec cancellation flow |
| `charge.refunded` | Record refund in LedgerEntry | Invoice status adjusted | Updates payment/invoice records; reverses consumed services if applicable |
| `payment_intent.succeeded` | Payment confirmation for one-time charges | LedgerEntry recorded | Handles email/SMS overage billing completion |
| `payment_intent.payment_failed` | Failed one-time payment | Notification sent to account owner | Triggers retry sequence and customer notification per dunning policy |

## 7. Success/Failure Contract
*   **Response 200 OK**: MUST be returned if the signature is valid and the event is logged. 
*   **Deferred Processing**: For high-volume environments, the mapping and update logic should be handed off to a **Celery** background worker to prevent Stripe timeout (which is standardly 10 seconds).

## 7. Data Retention & Purging
To prevent unbounded database growth while maintaining a sufficient audit trail:

1.  **Retention Period**: `WebhookLog` entries are retained for **12 months**.
2.  **Automated Purging**: A scheduled Celery task (`purge_webhook_logs`) runs weekly (Sunday @ 04:00 Local) to hard-delete records where `created_on` is older than 12 months.
3.  **Rationale**: The 12-month window is sufficient to resolve any payment disputes or idempotency issues. Critical financial records (Ledger, Invoices) are stored in their own tables and are NOT affected by this log purge.
