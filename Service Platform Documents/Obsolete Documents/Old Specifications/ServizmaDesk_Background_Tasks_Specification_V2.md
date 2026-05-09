# ServizmaDesk Background Task Specification (SDTA)
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

#### `update_overdue_invoices`
- **Purpose**: Identifies Invoices past their `due_date` that have not been fully paid and transitions their status to `Overdue`.
- **Logic**: Set `status = Overdue` for all Invoices where `status IN (Issued, Partially Paid)` AND `due_date < Current Date (Tenant Local)`.
- **Schedule**: 00:15 (Local).
- **Retry**: 3 retries.
- **Idempotency**: Safe to re-run — only updates records not already in `Overdue` status.

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
- **Purpose**: Identifies Agreements that have reached their `end_date` and transitions them from `Active` to `Expired`. Also transitions linked PM records.
- **Logic**:
    1. Set `status = Expired` for all Agreements where `status = Active` AND `end_date < Current Date`.
    2. For each expired Agreement, set `status = Expired` on all linked PreventativeMaintenance records via CustomerAgreement.
- **Schedule**: 01:15 (Local).
- **Retry**: 3 retries.
- **Note**: Existing in-progress Work Orders generated by the PM are not affected — they continue to completion. Only future generation is stopped.

### 3.5 Compliance & Certification Alerts (Pro+)

#### `check_employee_certification_expiry`
- **Purpose**: Identifies EmployeeSkill records approaching expiration and generates alerts for administrators.
- **Logic**: Query `EmployeeSkill` records where `status = Active` AND `expiration_date` is not null. Generate alerts at two thresholds:
    - **30-day warning**: `expiration_date` is within 30 days of current date.
    - **Expired**: `expiration_date < Current Date`. Automatically set `status = Expired` on the record.
- **Schedule**: 06:00 (Local) — daily.
- **Retry**: 3 retries.
- **User Alert**: `Notification` for Administrators: "Certification Expiring: [Employee Name] — [Skill Name] expires [Date]" or "Certification Expired: [Employee Name] — [Skill Name]".

### 3.6 Fleet Management (Add-On)

#### `check_fleet_compliance`
- **Purpose**: Identifies vehicles with approaching or overdue compliance deadlines (registration, insurance, inspection).
- **Logic**: For each active Vehicle, check `registration_expiry`, `insurance_expiry`, and `next_inspection_date` against alert thresholds configured in Fleet preferences (default: 30-day and 7-day warnings, plus overdue).
- **Schedule**: 06:15 (Local) — daily.
- **Retry**: 3 retries.
- **Condition**: Only runs for tenants with Fleet Management add-on active.
- **User Alert**: `Notification` for Administrators: "Vehicle Compliance Alert: [Vehicle Number] — [Registration/Insurance/Inspection] [expires in X days / is overdue]".

#### `check_vehicle_maintenance_due`
- **Purpose**: Identifies vehicles with upcoming or overdue maintenance based on date and odometer thresholds.
- **Logic**:
    - **Date-based**: Check `VehicleMaintenance` records where `status = Scheduled` AND `scheduled_date` is within alert threshold (default: 14-day and 3-day warnings). Set `status = Overdue` if `scheduled_date < Current Date`.
    - **Odometer-based**: Check where `next_service_odometer` is not null AND `Vehicle.odometer_current` is within 500 miles of `next_service_odometer`.
- **Schedule**: 06:30 (Local) — daily.
- **Retry**: 3 retries.
- **Condition**: Only runs for tenants with Fleet Management add-on active.
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
