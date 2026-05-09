# ServizDesk Background Task Specification (SDTA)
**Document Version:** V2
**Status:** Working Draft
**Supersedes:** V1

## 1. Overview
This document defines the inventory of background tasks managed by the Celery worker cluster within the SDTA. These tasks handle long-running operations, scheduled data maintenance, and external service synchronization.

## 2. Global Strategy
- **Broker**: Redis (Persistence enabled).
- **Result Backend**: PostgreSQL (via `django-celery-results`).
- **Monitoring**: Sentry (Performance/Exceptions) + **User Log (Notification Table)** for administrator visibility.
- **Timezone**: Maintenance tasks MUST be scheduled using the **`TenantPreference.timezone`**. The scheduler evaluates once per hour and triggers tasks at the appropriate local hour for each tenant.

## 3. Task Inventory

> **Lifecycle Framework Rule:** All entity status changes performed by background tasks must go through `execute_transition()` from the Lifecycle Framework Specification V1. Direct status field updates are prohibited. The `system_user` identifier (e.g., `"System"`) is passed as the user parameter for audit trail purposes. Each task must set tenant context per Multi-Tenancy Specification V1 Section 10 before calling `execute_transition()`.

### 3.1 Data Retention & Purging
These tasks ensure the system complies with data retention policies.

| Task Name | Logic Path | Schedule | Retention | Max Retries |
|---|---|---|---|---|
| `purge_deleted_tenant_data` | `tasks.purge.hard_delete_tenants` | 02:00 (Local) | 60 days after `Pending Deletion` status | 5 (Exp. Backoff) |
| `purge_audit_logs` | `tasks.purge.system_audits` | Sun @ 03:00 (Local)| 18 Months | 3 |
| `purge_session_logs` | `tasks.purge.session_logs` | Sun @ 03:15 (Local)| 18 Months | 3 |
| `purge_login_attempt_logs` | `tasks.purge.login_attempt_logs` | Sun @ 03:20 (Local)| 18 Months | 3 |
| `purge_system_errors` | `tasks.purge.error_logs` | Sun @ 03:30 (Local)| 90 Days | 3 |
| `purge_stripe_request_logs`| `tasks.purge.stripe_logs` | Sun @ 03:45 (Local)| 90 Days | 3 |
| `purge_webhook_logs` | `tasks.purge.webhook_logs` | Sun @ 04:00 (Local)| 12 Months | 3 |
| `purge_email_delivery_logs`| `tasks.purge.email_logs` | Sun @ 04:15 (Local)| 12 Months | 3 |

> **`purge_deleted_tenant_data` — S3 File Cleanup Requirement:** Database record deletion alone does not remove files from object storage. Before deleting `Document` records for a tenant, the task must first enumerate all `Document.file_key` values for that `tenant_id` and delete the corresponding S3/Spaces objects using `boto3`. Failure to do so results in orphaned files accumulating indefinitely in the storage bucket, incurring ongoing storage costs with no corresponding data in the database. The deletion order must be: (1) delete S3 objects, (2) delete database records. If S3 deletion fails after retries, the database records must NOT be deleted — the task must alert via `Notification` and Sentry and stop. Preserving the database records allows the next scheduled run to retry S3 cleanup using the same file references. Proceeding to delete the database records when S3 objects still exist would orphan those files permanently (S3 objects with no database reference and no mechanism to identify or clean them up).

### 3.2 State Synchronization & Maintenance
Tasks that keep the local SDTA database in sync with internal and external realities.

#### `reconcile_storage_usage`
- **Purpose**: Recalculates the `StorageTracker` by summing `file_size_bytes` in the `Document` table per tenant, split by `scan_status`. Corrects any drift caused by partial failures in the upload or scan workflow.
- **Logic**:
    - `total_bytes_used` ← `SUM(file_size_bytes) WHERE scan_status = 'Clean'`
    - `pending_bytes` ← `SUM(file_size_bytes) WHERE scan_status = 'Pending'`
    - Documents with `scan_status = 'Infected'` are excluded (they have already been deleted from S3).
- **Schedule**: 01:00 (Local).
- **Retry**: 3 retries (10 min interval).
- **User Alert**: If reconciliation fails > 3 times, create a high-severity `Notification` for Administrators.

#### `reset_email_usage_counters`
- **Purpose**: Resets `EmailUsageTracker.email_points_used` and `email_points_overage` to 0 for each tenant whose `email_period_start` anniversary falls on today's date. This is the billing cycle reset for email point consumption.
- **Logic**: For each tenant where `TenantState.email_period_start` (day and month) matches today: reset `EmailUsageTracker.email_points_used = 0` and `email_points_overage = 0`. The reset must occur atomically after Stripe has been charged for any overage (this task is downstream of the billing cycle run).
- **Schedule**: 00:05 (Local).
- **Retry**: 3 retries (5 min interval).
- **User Alert**: If reset fails, generate a high-severity `Notification` for Administrators.

#### `reset_sms_usage_counters`
- **Purpose**: Resets `SMSUsageTracker.sms_points_used` and `sms_points_overage` to 0 for each tenant whose `sms_period_start` anniversary falls on today's date.
- **Logic**: Same pattern as `reset_email_usage_counters` — anniversary-based reset after Stripe billing for overage.
- **Schedule**: 00:06 (Local).
- **Retry**: 3 retries (5 min interval).
- **User Alert**: If reset fails, generate a high-severity `Notification` for Administrators.

#### `sync_tenant_state_cache`
- **Purpose**: Force-refresh local `TenantState` (Tiers, Limits) from the SDP Registry for all active tenants.
- **Schedule**: Every 6 hours (Global UTC).
- **Retry**: 5 retries (Exponential).
- **Fail-safe**: If refresh fails, maintain existing local state to avoid service interruption and log a `Notification` for Admins.

#### `manage_trial_lifecycle`
- **Purpose**: Identify trial accounts reaching thresholds and update `TenantState.status` accordingly.
- **Logic**:
    - **Day 15**: If no subscription active, set `TenantState.status = 'Read Only'`. All users can log in and view data but cannot create, edit, or delete records. See Pricing & Billing Specification V2 Section 6.2.
    - **Day 45**: Set `TenantState.status = 'Pending Deletion'`. The tenant is queued for the `purge_deleted_tenant_data` cleanup cycle. A deletion notification email is sent to the Administrator.
- **Schedule**: 00:30 (Local).

### 3.3 Financial & Integration

#### `generate_recurring_invoices` (Plus+)
- **Purpose**: Evaluates `recurrence_pattern` on Invoice templates and generates current-period drafts.
- **Schedule**: 00:01 (Local).
- **Retry**: 3 retries. Must be idempotent (check `period_start`/`period_end` existence).
- **User Alert**: If invoice generation fails, generate a `Notification` titled "Auto-Invoicing Error" for Administrators.

#### `update_overdue_invoices`
- **Purpose**: Identifies Invoices past their `due_date` that have not been fully paid and transitions their status to `Overdue`.
- **Logic**: For all Invoices where `status IN (Issued, Viewed, Partially Paid)` AND `due_date < Current Date (Tenant Local)`, call `execute_transition(invoice, 'OVERDUE', system_user)` per Lifecycle Framework Specification V1.
- **Schedule**: 00:15 (Local).
- **Retry**: 3 retries.
- **Idempotency**: Safe to re-run — only updates records not already in `Overdue` status.

#### `update_overdue_vendor_bills` (Plus+)
- **Purpose**: Identifies Vendor Bills past their `due_date` that have not been fully paid and transitions their status to `Overdue`.
- **Logic**: For all `VendorBill` records where `status IN (Received, Partially Paid)` AND `due_date < Current Date (Tenant Local)`, call `execute_transition(vendor_bill, 'OVERDUE', system_user)` per Lifecycle Framework Specification V1.
- **Schedule**: 00:16 (Local).
- **Retry**: 3 retries.
- **Idempotency**: Safe to re-run — only updates records not already in `Overdue` status.
- **Condition**: Only runs for tenants on Plus or above.

### 3.4 Service Agreements & Preventative Maintenance (Plus+)

#### `generate_pm_work_orders`
- **Purpose**: Evaluates all active PreventativeMaintenance records and auto-generates Work Orders per their schedule when the `auto_gen_work_orders` flag is enabled.
- **Logic**:
    1. Query all `PreventativeMaintenance` records where `status = Active` AND `auto_gen_work_orders = True`.
    2. For each PM, calculate whether a Work Order is due within the `advance_gen_days` window.
    3. If due and no WO already exists for this PM + scheduled period, create a new Work Order with: `customer_id` from PM, `asset_id` from PM, `workflow_id` from PM, `assigned_to` from `default_assignee_id`, `prev_maint_id` linking back to the PM, `status = Scheduled`.
- **Schedule**: 00:30 (Local).
- **Retry**: 3 retries (Exponential).
- **Idempotency**: Must check for existing WOs in the target period before generating. Duplicate WOs must never be created.
- **User Alert**: If generation fails for any PM, create a `Notification`: "PM Work Order Generation Failed: [PM Number] for Asset [Asset Number]".

#### `process_agreement_expirations`
- **Purpose**: Identifies Agreements and CustomerAgreements that have reached their `end_date` and transitions them from `Active` to `Expired`. Also transitions linked PM records.
- **Logic**:
    1. For all `Agreement` records where `status = Active` AND `end_date IS NOT NULL` AND `end_date < Current Date`, call `execute_transition(agreement, 'EXPIRED', system_user)`.
    2. For each expired `Agreement` (Step 1), call `execute_transition(pm, 'EXPIRED', system_user)` on all linked `PreventativeMaintenance` records via `CustomerAgreement`.
    3. For all `CustomerAgreement` records where `status = Active` AND `end_date IS NOT NULL` AND `end_date < Current Date`, call `execute_transition(customer_agreement, 'EXPIRED', system_user)`. For each expired `CustomerAgreement`, also transition all directly linked `PreventativeMaintenance` records not already expired by Step 2.
- **Schedule**: 01:15 (Local).
- **Retry**: 3 retries.
- **Note**: Existing in-progress Work Orders generated by the PM are not affected — they continue to completion. Only future generation is stopped. CustomerAgreements may expire independently of their Agreement template — a template can remain Active while individual enrollments expire based on their own `end_date`.

### 3.5 Security & Compliance Alerts

#### `check_stale_mfa_exemptions`
- **Purpose**: Identifies employees whose `mfa_exempt` flag has been set to `True` for more than 24 hours without being cleared. Creates a `Notification` for Administrators to prompt follow-up.
- **Logic**: Query `User` records where `mfa_exempt = True` AND `updated_on < (now() - 24 hours)`. For each match, create one `Notification` for the tenant's Administrators: "MFA Exemption Overdue: [Employee Name] has had their MFA exemption active for over 24 hours. Please verify that MFA has been reconfigured and clear the exemption."
- **Schedule**: 08:00 (Local) — daily.
- **Retry**: 3 retries.
- **Idempotency**: Only creates one Notification per employee per day. Check for an existing unread notification of the same type for that employee before creating a duplicate.
- **Note**: MFA exemptions are recovery-only and must not be left active permanently. See Permission Management Specification V2, Section 12.4.

### 3.6 Compliance & Certification Alerts (Pro+)

#### `check_employee_certification_expiry`
- **Purpose**: Identifies EmployeeSkill records approaching expiration and generates alerts for administrators.
- **Logic**: Query `EmployeeSkill` records where `status = Active` AND `expiration_date` is not null. Generate alerts at two thresholds:
    - **30-day warning**: `expiration_date` is within 30 days of current date.
    - **Expired**: `expiration_date < Current Date`. Call `execute_transition(employee_skill, 'EXPIRED', system_user)` per Lifecycle Framework Specification V1.
- **Schedule**: 06:00 (Local) — daily.
- **Retry**: 3 retries.
- **User Alert**: `Notification` for Administrators: "Certification Expiring: [Employee Name] — [Skill Name] expires [Date]" or "Certification Expired: [Employee Name] — [Skill Name]".

### 3.7 Fleet Maintenance (Add-On)

#### `check_fleet_compliance`
- **Purpose**: Identifies vehicles with approaching or overdue compliance deadlines (registration, insurance, inspection).
- **Logic**: For each active Vehicle, check `registration_expiry`, `insurance_expiry`, and `next_inspection_date` against alert thresholds configured in Fleet preferences (default: 30-day and 7-day warnings, plus overdue).
- **Schedule**: 06:15 (Local) — daily.
- **Retry**: 3 retries.
- **Condition**: Only runs for tenants with Fleet Maintenance add-on active.
- **User Alert**: `Notification` for Administrators: "Vehicle Compliance Alert: [Vehicle Number] — [Registration/Insurance/Inspection] [expires in X days / is overdue]".

#### `check_vehicle_maintenance_due`
- **Purpose**: Identifies vehicles with upcoming or overdue maintenance based on date and odometer thresholds.
- **Logic**:
    - **Date-based**: Check `VehicleMaintenance` records where `status = Scheduled` AND `scheduled_date` is within alert threshold (default: 14-day and 3-day warnings). If `scheduled_date < Current Date`, call `execute_transition(vehicle_maintenance, 'OVERDUE', system_user)` per Lifecycle Framework Specification V1.
    - **Odometer-based**: Check where `next_service_odometer` is not null AND `Vehicle.odometer_current` is within 500 miles of `next_service_odometer`.
- **Schedule**: 06:30 (Local) — daily.
- **Retry**: 3 retries.
- **Condition**: Only runs for tenants with Fleet Maintenance add-on active.
- **User Alert**: `Notification` for Administrators: "Vehicle Maintenance Due: [Vehicle Number] — [Maintenance Type] [due in X days / overdue / odometer approaching threshold]".

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

## 6. Multi-Tenancy Context in Background Tasks

### 6.1 The Problem

Celery workers execute outside of any HTTP request cycle. `TenantMiddleware` does not run. The PostgreSQL `app.current_tenant_id` session variable is not set. This creates two failure modes for tasks that create or modify records:

- **`TenantModel.save()` raises `ValueError`**: `TenantModel.save()` requires a tenant context to be set in `get_current_tenant_id()`. Without it, it cannot auto-populate `tenant_id` and raises `ValueError: Cannot save TenantModel without a tenant_id in context.`
- **PostgreSQL RLS blocks the write**: Even if `tenant_id` is supplied manually, the RLS `WITH CHECK` constraint requires `app.current_tenant_id` to be set. Without it, the INSERT is rejected.

### 6.2 Two Categories of Tasks

#### Cross-Tenant Tasks (Read-Only Iteration)
Tasks that iterate across all tenants to select which ones need processing (e.g., `manage_trial_lifecycle`, `process_agreement_expirations`) perform **reads only** at the cross-tenant level. These must use the `'worker'` database alias, which connects as `sdta_migration` (`BYPASSRLS = TRUE`):

```python
# Cross-tenant read — use 'worker' alias (sdta_migration, BYPASSRLS)
tenants_to_process = TenantState.all_objects.using('worker').filter(status='Active')
```

These tasks do not create records at the cross-tenant read stage, so no context is needed for the read. If they subsequently write per-tenant records, they must switch to the per-tenant write pattern below.

#### Per-Tenant Tasks (Record Creation / Modification)
Tasks that create or modify `TenantModel` records (e.g., `generate_pm_work_orders`, `generate_recurring_invoices`, `update_overdue_invoices`) **must set tenant context** before any write.

### 6.3 Required Pattern for Per-Tenant Record Creation

```python
@shared_task(bind=True, max_retries=3)
def generate_pm_work_orders(self, tenant_id: str):
    # Step 1: Set Python-level context — satisfies TenantModel.save()
    set_current_tenant_id(uuid.UUID(tenant_id))
    try:
        with transaction.atomic():
            # Step 2: Set PostgreSQL-level context — satisfies RLS WITH CHECK
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.current_tenant_id = %s", [tenant_id])

            # Step 3: All ORM writes are now safe
            _run_pm_generation_for_tenant(tenant_id)

    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    finally:
        # Step 4: ALWAYS clear context — prevents leak to next task on the same thread
        clear_current_tenant_id()
```

### 6.4 Rules

| Rule | Reason |
|---|---|
| Call `set_current_tenant_id(tenant_id)` before any `TenantModel.save()` | Prevents `ValueError` from the Python-layer guard |
| Call `SET LOCAL app.current_tenant_id` inside `transaction.atomic()` before any write | Satisfies the PostgreSQL RLS `WITH CHECK` constraint |
| Always call `clear_current_tenant_id()` in a `finally` block | Prevents tenant context from leaking to the next task running on the same Celery worker thread |
| Cross-tenant reads use `Model.all_objects.using('worker')` | `'worker'` alias connects as `sdta_migration` (BYPASSRLS), bypassing RLS for system-level iteration |
| Never use the `'worker'` alias for per-tenant business writes | All business data writes (creating Work Orders, Invoices, etc.) must go through the default connection (`sdta_app`) with tenant context set, so RLS enforcement is maintained |
| **Exception — Cross-tenant maintenance deletes:** Rolling retention purge tasks (`purge_audit_logs`, `purge_session_logs`, `purge_login_attempt_logs`, etc.) must delete records across ALL tenants by age. These are the one class of write operation where the `'worker'` alias is acceptable — they use `Model.all_objects.using('worker').filter(timestamp_field__lt=cutoff).delete()`. This is not a tenant business write — it is a time-based maintenance operation that inherently operates outside of single-tenant scope. The `'worker'` BYPASSRLS access is the correct choice here and must be used with extra care. |
