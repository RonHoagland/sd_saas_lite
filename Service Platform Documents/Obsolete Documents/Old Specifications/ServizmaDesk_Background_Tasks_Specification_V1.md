# ServizmaDesk Background Task Specification (SDTA)
**Document Version:** V1
**Status:** Approved (Resolves Gap 3.3)

## 1. Overview
This document defines the inventory of background tasks managed by the Celery worker cluster within the SDTA. These tasks handle long-running operations, scheduled data maintenance, and external service synchronization.

## 2. Global Strategy
- **Broker**: Redis (Persistence enabled).
- **Result Backend**: PostgreSQL (via `django-celery-results`).
- **Monitoring**: Sentry (Performance/Exceptions) + **User Log (Notification Table)** for administrator visibility.
- **Timezone**: Maintenance tasks MUST be scheduled using the **`TenantPreference.timezone`**. The scheduler evaluates once per hour and triggers tasks at the appropriate local hour for each tenant.

## 3. Task Inventory

### 3.1 Data Retention & Purging
These tasks ensure the system complies with data retention policies.

| Task Name | Logic Path | Schedule | Retention | Max Retries |
|---|---|---|---|---|
| `purge_deleted_tenant_data` | `tasks.purge.hard_delete_tenants` | 02:00 (Local) | 60 Days | 5 (Exp. Backoff) |
| `purge_audit_logs` | `tasks.purge.audit_events` | Sun @ 03:00 (Local)| 18 Months | 3 |
| `purge_session_logs` | `tasks.purge.session_logs` | Sun @ 03:15 (Local)| 18 Months | 3 |
| `purge_system_errors` | `tasks.purge.error_logs` | Sun @ 03:30 (Local)| 90 Days | 3 |
| `purge_stripe_request_logs`| `tasks.purge.stripe_logs` | Sun @ 03:45 (Local)| 90 Days | 3 |
| `purge_webhook_logs` | `tasks.purge.webhook_logs` | Sun @ 04:00 (Local)| 12 Months | 3 |
| `purge_email_delivery_logs`| `tasks.purge.email_logs` | Sun @ 04:15 (Local)| 12 Months | 3 |

### 3.2 State Synchronization & Maintenance
Tasks that keep the local SDTA database in sync with internal and external realities.

#### `reconcile_storage_usage`
- **Purpose**: Recalculates the `StorageTracker` by summing all `file_size_bytes` in the `Document` table per tenant.
- **Schedule**: 01:00 (Local).
- **Retry**: 3 retries (10 min interval).
- **User Alert**: If reconciliation fails > 3 times, create a high-severity `Notification` for Administrators.

#### `sync_tenant_state_cache`
- **Purpose**: Force-refresh local `TenantState` (Tiers, Limits) from the SDP Registry for all active tenants.
- **Schedule**: Every 6 hours (Global UTC).
- **Retry**: 5 retries (Exponential).
- **Fail-safe**: If refresh fails, maintain existing local state to avoid service interruption and log a `Notification` for Admins.

#### `manage_trial_lifecycle`
- **Purpose**: Identify trial accounts reaching thresholds.
- **Logic**:
    - **Day 15**: Set `TenantState.status` to `READ_ONLY` if no subscription active.
    - **Day 45**: Set `pending_cleanup` flag for deletion worker selection.
- **Schedule**: 00:30 (Local).

### 3.3 Financial & Integration
#### `generate_recurring_invoices` (Pro+)
- **Purpose**: Evaluates `recurrence_pattern` on Invoice templates and generates current-period drafts.
- **Schedule**: 00:01 (Local).
- **Retry**: 3 retries. Must be idempotent (check `period_start`/`period_end` existence).
- **User Alert**: If invoice generation fails, generate a `Notification` titled "Auto-Invoicing Error" for Administrators.

## 4. Notification & Logging (User Log)
As per the **Top-Down Design**, background task failures requiring human intervention MUST be surfaced to the user via the `Notification` table:
1. **Critical Failures**: If a task exhausts all retries (e.g., Recurring Invoice failure, Storage Reconcile mismatch), a record is created in the `Notification` table.
2. **Visibility**: These appear in the "User Log" / "Notification Area" in both SDTA and SDP for tenant administrators.
3. **Boilerplate**:
    - `severity = Error`
    - `message = "System Task Failure: [Task Name]. Please retry manually or contact support."`
    - `is_dismissed = False`

## 5. Error Handling & Retry Policy
All tasks MUST implement the following boilerplate:
1. **Exponential Backoff**: `countdown=2**retry_count` for transient network/DB errors.
2. **Dead Letter Alerting**: If the maximum retry count is reached, the task MUST log a CRITICAL error to Sentry with the task payload attached AND create a `Notification` record for users.
3. **Atomic Writes**: Any task modifying multiple records must wrap operations in a `transaction.atomic()` block.
