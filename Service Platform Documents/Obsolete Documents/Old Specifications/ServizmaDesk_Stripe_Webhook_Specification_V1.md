# ServizmaDesk Stripe Webhook Specification (SDTA)
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
2.  **Database Lookup**:
    ```python
    connection = StripeConnection.all_objects.select_related('tenant').get(
        stripe_account_id=acct_id, 
        is_active=True
    )
    tenant_id = connection.tenant_id
    ```
3.  **Context Activation**: Use the `TenantManager` context (from Gap 3.2) to activate the `tenant_id` before processing the payload.

## 4. Idempotency & Logging
To prevent double-counting payments due to Stripe retries or network errors:

1.  **Event Check**: Every Stripe event has a unique ID (e.g., `evt_123`).
2.  **`WebhookLog` Constraint**:
    *   On arrival, search the `WebhookLog` (unscoped) for the event ID.
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
    # logic to mark paid, generate LedgerEntry, and emit AuditEvent
    ```

## 6. Success/Failure Contract
*   **Response 200 OK**: MUST be returned if the signature is valid and the event is logged. 
*   **Deferred Processing**: For high-volume environments, the mapping and update logic should be handed off to a **Celery** background worker to prevent Stripe timeout (which is standardly 10 seconds).

## 7. Data Retention & Purging
To prevent unbounded database growth while maintaining a sufficient audit trail:

1.  **Retention Period**: `WebhookLog` entries are retained for **12 months**.
2.  **Automated Purging**: A scheduled Celery task (`purge_old_webhook_logs`) runs monthly to hard-delete records where `created_on` is older than 12 months.
3.  **Rationale**: The 12-month window is sufficient to resolve any payment disputes or idempotency issues. Critical financial records (Ledger, Invoices) are stored in their own tables and are NOT affected by this log purge.
