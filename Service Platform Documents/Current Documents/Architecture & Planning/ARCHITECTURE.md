# ServizDesk Technical Architecture Reference

**Platform**: ServizDesk SDTA (Service Desk & Tenant Administration)
**Version**: Phase 4 — Background Tasks Complete
**Last Updated**: March 2026

---

## Overview

ServizDesk is a multi-tenant SaaS platform for field service management. It covers CRM, service delivery, maintenance, procurement, inventory, fleet management, workforce scheduling, and workflow automation — all scoped to isolated tenants with PostgreSQL Row-Level Security.

The platform is built on Django 5.x with PostgreSQL, Celery for background processing, and S3-compatible file storage (DigitalOcean Spaces). It currently contains 136 models across 18 Django apps.

---

## Table of Contents

1. [Multi-Tenancy Architecture](#1-multi-tenancy-architecture)
2. [Numbering System](#2-numbering-system)
3. [Lifecycle State Machine](#3-lifecycle-state-machine)
4. [Value Lists](#4-value-lists)
5. [Notes System](#5-notes-system)
6. [Documents & File Storage](#6-documents--file-storage)
7. [Background Tasks (Celery)](#7-background-tasks-celery)
8. [Tenant Provisioning (Seed Data)](#8-tenant-provisioning-seed-data)
9. [Domain Apps](#9-domain-apps)
10. [Middleware Stack](#10-middleware-stack)
11. [Security Configuration](#11-security-configuration)
12. [Testing Infrastructure](#12-testing-infrastructure)
13. [Configuration Reference](#13-configuration-reference)

---

## 1. Multi-Tenancy Architecture

Every piece of business data in ServizDesk is tenant-scoped. Isolation is enforced at three levels: the Django ORM layer, the middleware layer, and the PostgreSQL RLS layer.

### TenantModel (config/base_models.py)

All tenant-scoped models inherit from `TenantModel`, which provides six standard fields: a UUID primary key (`id`), a `tenant_id` UUID, and four audit fields (`created_by`, `created_on`, `updated_by`, `updated_on`). The `created_on` and `updated_on` timestamps are always stored in UTC.

TenantModel exposes two managers. The default manager (`objects`) is a `TenantManager` that automatically injects a `tenant_id` filter on every queryset based on the current thread-local context. Application code always uses this manager, which means cross-tenant data leaks are structurally impossible in normal request handling. A second manager (`all_objects`) is unfiltered and reserved for system tasks like Celery background jobs, management commands, and the Django admin running on the `worker` database alias.

The `save()` method on TenantModel enforces two rules. If a tenant context is active and the instance has no `tenant_id`, it auto-injects the current tenant. If the instance's `tenant_id` doesn't match the active context, `save()` raises a `ValueError` to prevent accidental cross-tenant writes.

### Tenant Context (config/tenant_context.py)

Tenant context is stored in an `asgiref.local.Local` object, which is both thread-safe and async-safe. Three functions manage it: `set_current_tenant_id()`, `get_current_tenant_id()`, and `clear_current_tenant_id()`.

In the request cycle, `TenantMiddleware` sets the context before the view runs and clears it after the response. In Celery tasks, `TenantAwareTask.before_start()` sets it and `after_return()` clears it. The context is never persisted — it exists only for the lifetime of a request or task execution.

### Dual Database Aliases

The `default` database alias connects as a PostgreSQL user subject to Row-Level Security policies. Every query on this alias is filtered both by TenantManager (Django) and by RLS policies (PostgreSQL).

The `worker` alias connects as a user with `BYPASSRLS=TRUE`. It is used by background tasks that need cross-tenant reads, the Django admin for staff access, and retention purge jobs. In tests, the `worker` alias mirrors `default` so both point to the same test database.

### PostgreSQL RLS Integration

`TenantMiddleware` issues `SET LOCAL app.current_tenant_id = '{tenant_id}'` at the start of every request. The `SET LOCAL` form (rather than plain `SET`) scopes the variable to the current transaction, which resets automatically on commit — critical for PgBouncer transaction-mode connection pooling.

---

## 2. Numbering System

The numbering system generates human-readable sequential identifiers (like `C-26-0001` for customers or `WO-26-0042` for work orders) that are unique per tenant. It follows a three-model pattern.

### Models (numbering app)

**NumberingRule** defines the pattern for each entity type per tenant. Fields include `prefix` (e.g., "C", "WO"), `include_year` and `year_format` ("YY" or "YYYY"), `include_month`, `sequence_length` (default 4 digits), `delimiter` (default "-"), and `reset_behavior` ("none", "yearly", or "monthly"). Each tenant gets one rule per entity type, enforced by a unique constraint on `(tenant_id, entity_type)`.

**NumberSequence** tracks the current counter value. It has a one-to-one relationship with NumberingRule and stores `current_value` (integer) and `last_reset_date`. This model is intentionally not a TenantModel — it exists solely as a counter for its parent rule.

**AssignedNumber** is an immutable record of each number assignment. It stores the `rule`, `entity_type`, `entity_id`, the generated `number` string, and `assigned_at`/`assigned_by` audit fields. Both `save()` (on existing records) and `delete()` raise `ValidationError` — once a number is assigned, it cannot be changed or removed.

### NumberingMixin

Models that receive sequential numbers (Customer, WorkOrder, Quote, Invoice, Asset, etc.) include `NumberingMixin` and declare a `numbering_entity_type` class attribute. The mixin provides three instance methods: `assign_number()` generates and persists a new number, `get_assigned_number()` retrieves the current number string, and `has_assigned_number()` returns a boolean.

Numbers are not assigned automatically on save. They are assigned on explicit call, typically after the entity passes business validation — this prevents wasting sequence numbers on entities that fail validation.

### Service Layer (numbering/services.py)

The core function `assign_number(tenant_id, entity_type, entity_id, user_display)` handles the full flow: it fetches the rule, checks if a number already exists for this entity, increments the sequence (with reset detection for yearly/monthly resets), formats the number string, creates the AssignedNumber record, and returns it. Duplicate prevention is handled by the unique constraint on `(tenant_id, entity_type, entity_id)`.

### Seeded Entity Types

23 entity types are seeded at tenant provisioning: customer, lead, opportunity, service_request, work_order, quote, invoice, payment, vendor, purchase_order, vendor_bill, requisition, rma, asset, agreement, preventative_maintenance, task, work_group, vehicle, inventory_item, workflow, equipment, and employee.

---

## 3. Lifecycle State Machine

The lifecycle system manages entity states and transitions — which states an entity can be in, which transitions are valid, who can perform them, and a complete audit trail of every state change. It also follows a three-model pattern.

### Models (lifecycle app)

**LifecycleStateDef** defines the valid states for each entity type per tenant. Each state has a `state_name` (machine key like "ACTIVE"), a `state_label` (display text like "Active"), a `state_type` ("normal", "locked", or "final"), and an `is_default` flag. The `state_type` controls behavior: normal states can be entered and exited freely, locked states require special handling to exit, and final states are terminal — no transitions out are allowed unless the transition rule has `is_admin_override=True`. Exactly one state per entity type must be marked `is_default`; the `save()` override enforces this by clearing `is_default` on sibling states when a new default is set.

**LifecycleTransitionRule** defines which state-to-state transitions are valid. Each rule specifies `from_state`, `to_state`, an optional `required_role` for authorization, `requires_reason` (boolean), and `is_admin_override` (allows transitions from final states). A database CHECK constraint prevents self-transitions (`from_state != to_state`), and `clean()` validates that both states exist in LifecycleStateDef and that transitions from final states require `is_admin_override=True`.

**LifecycleTransitionAudit** is an immutable, append-only log of every state transition that actually occurred. It is not a TenantModel — it uses raw UUID fields for `tenant_id`, `user_id`, and `entity_id` rather than foreign keys. This ensures the audit trail survives even if the related entities are deleted. Both `save()` (on existing records) and `delete()` raise `ValidationError`, and `default_permissions` is empty to prevent admin modifications.

### LifecycleMixin

Models that participate in the state machine (Customer, Task, WorkOrder, Quote, Invoice, ServiceRequest, Asset, etc.) include `LifecycleMixin` and declare a `lifecycle_entity_type` class attribute plus a `status` CharField. The mixin provides `execute_transition()` (validates the transition rule, checks role authorization, updates the entity's status field, and creates an audit record), `get_available_transitions()` (returns valid next states for the current user), and `get_transition_history()` (returns the audit log for this entity).

### Seeded Entity Types

29 entity types have lifecycle states seeded at tenant provisioning. Examples include: customer (4 states), lead (5 states), work_order (6 states), payment (10 states including Open, Pending, Processing, On Hold, Partially Applied, Applied, Paid, Returned, Voided, and Refunded), and project (5 states). The seed data includes both state definitions and transition rules — not every state connects to every other state, and the transitions encode real business logic (e.g., a Paid payment cannot transition directly to Open).

---

## 4. Value Lists

Value lists are tenant-configurable picklists used for dropdowns and categorization fields throughout the UI. They allow tenants to customize options without schema changes.

### Models (value_lists app)

**ValueList** represents a named picklist (e.g., "Lead Sources", "Work Order Types"). Each has a `name` for display, a `slug` for programmatic reference, and an `is_system` flag. System lists (seeded at provisioning) cannot be deleted — the `delete()` override raises `ValidationError` if `is_system=True`. Uniqueness is enforced on `(tenant_id, slug)`.

**ValueListItem** represents an individual option within a list. Fields include `label` (display text), `value` (stored in referencing fields), `sort_order` (ascending), `is_default` (only one per list, enforced in `clean()`), and `is_active` (deactivated items are hidden from new selections but preserved on existing records). Uniqueness is enforced on `(tenant_id, value_list, value)`.

### Seeded Lists

System-seeded value lists include: lead_source, work_order_type, asset_category, customer_type, and others. Each comes with standard items that tenants can modify (add items, reorder, deactivate) but cannot delete the list itself.

---

## 5. Notes System

Notes provide a flexible annotation mechanism that can be attached to any of 25 entity types across the platform.

### Models (notes app)

**Note** extends both `TenantModel` and `ExclusiveArcMixin`. It has a `note_type` field (Internal Note, Call, Email, Site Visit, Customer Comment, or Reminder) and a `body` text field. The exclusive arc pattern means each Note has 25 nullable foreign keys — one for each parent entity type — and exactly one must be set. This is enforced by `ExclusiveArcMixin.clean()`, which counts non-null parent FK fields and raises `ValidationError` if the count is not exactly one.

All 25 parent FKs use `related_name='note_records'` (rather than the default `'notes'`) to avoid Django field name collisions with `notes` TextFields on some target models.

### ExclusiveArcMixin (config/base_models.py)

This mixin is shared between the Note and Document models. It references a `PARENT_FK_FIELDS` list of 25 field names (also in `config/base_models.py`) and provides `clean()` validation and a `save()` override that calls `clean()` before persisting.

### Service Layer (notes/services.py)

Two functions: `create_note()` accepts a `parent_field` string (e.g., "work_order"), normalizes it (strips `_id` suffix), validates it against `PARENT_FK_FIELDS`, and creates the Note with the appropriate FK set. `get_notes_for_entity()` retrieves all notes for a given entity, ordered by `created_on` descending.

### Indexing

Each of the 25 parent FK fields has a partial index on `(tenant_id, {fk}_id)` where the FK is not null. This ensures efficient queries like "get all notes for work order X in tenant Y" without scanning the entire table.

---

## 6. Documents & File Storage

The documents system manages file uploads with virus scanning, immutable metadata, audit logging, and a dual-backend storage abstraction.

### Models (documents app)

**Document** extends `TenantModel` and `ExclusiveArcMixin` (same 25 parent FKs as Note). File metadata fields — `original_filename`, `file_key` (the S3/storage path), `file_size_bytes`, `mime_type`, and `sha256_hash` — are immutable after creation. The `save()` override fetches the existing record on update and raises `ValidationError` if any metadata field has changed. Only `scan_status` (Pending, Clean, or Infected) can be modified after creation.

**FileUploadLog** is a TenantModel that records every upload attempt with a status (Success, Failed, or Rejected), the original filename, file size, and optional failure reason. The `document` FK uses `SET_NULL` so upload logs survive document deletion.

**FileDownloadLog** is fully immutable — not a TenantModel, and both `save()` (on existing records) and `delete()` raise `ValidationError`. It uses raw UUID fields for `tenant_id` and `user_id` rather than foreign keys. The `document` FK uses `on_delete=PROTECT`, meaning a document cannot be deleted if it has download logs. This is intentional: files with download history should not be permanently removed.

### Storage Service (documents/storage.py)

The storage layer provides a unified API regardless of whether files are stored locally (development) or in S3-compatible storage (production).

**Backend selection** is controlled by the `SDTA_STORAGE_BACKEND` setting ("local" or "s3"). `LocalBackend` stores files under `MEDIA_ROOT` using the same directory structure as S3. `S3Backend` uses boto3 directly (not django-storages) for full control over key generation, presigned URLs, and tenant isolation.

**File keys** follow the pattern `{tenant_id}/{entity_type}/{entity_id}/{uuid}_{filename}`. The UUID prefix ensures uniqueness even with duplicate filenames. The filename is sanitized to alphanumerics, hyphens, underscores, and dots, with a 100-character cap.

**upload_file()** is the primary upload function. It validates the file (size against `SDTA_MAX_FILE_SIZE_MB`, MIME type against `SDTA_ALLOWED_MIME_TYPES`), computes a SHA-256 hash, generates a unique file key, uploads to the storage backend, creates a Document record with `scan_status=PENDING`, creates a FileUploadLog with status SUCCESS, and dispatches a `scan_uploaded_file` Celery task. If the backend upload fails, it logs a FAILED upload record and re-raises.

**download_url()** generates a download URL but only for documents with `scan_status=CLEAN`. For the S3 backend this is a presigned GET URL (expiring per `SDTA_PRESIGNED_URL_EXPIRY`, default 1 hour). For the local backend it returns a media URL path. Every download creates an immutable FileDownloadLog record.

**delete_file()** removes the file from the storage backend and deletes the Document record. If FileDownloadLog records exist, Django's PROTECT constraint raises `ProtectedError` — this is by design.

**presigned_upload_url()** generates a presigned PUT URL for direct browser-to-S3 uploads, bypassing Django entirely. Returns `None` for the local backend.

**update_scan_status()** is called by the async scan task to update a document's scan status. It uses `all_objects` to bypass the tenant filter.

### Custom Exceptions

`FileTooLargeError` and `DisallowedMimeTypeError` (both extend `ValidationError`) for upload validation failures, and `StorageBackendError` for backend communication failures.

---

## 7. Background Tasks (Celery)

ServizDesk uses Celery for asynchronous task processing with Redis as the message broker and django-db for result storage.

### Task Base Classes (config/base_task.py)

**TenantAwareTask** is the base class for all tenant-scoped background tasks. It hooks into the Celery task lifecycle to manage tenant context automatically. `before_start()` extracts `tenant_id` from the first positional argument (or from kwargs) and calls `set_current_tenant_id()`. `after_return()` always calls `clear_current_tenant_id()` — even on failure — to prevent context leakage between tasks executed by the same worker thread. `on_failure()` and `on_retry()` provide structured logging with tenant context.

The convention is that the first positional argument to every TenantAwareTask must be `tenant_id` (as a UUID string).

Default retry policy: 3 retries, 60-second base delay, exponential backoff (capped at 10 minutes), and jitter to prevent thundering herd effects. These defaults are overridable per-task.

**SystemTask** is for cross-tenant operations like retention purges and health checks. It clears tenant context in `before_start()` rather than setting it. Tasks using this base are expected to use `all_objects` manager and the `worker` database alias for unrestricted access.

### Document Tasks (documents/tasks.py)

**scan_uploaded_file** (TenantAwareTask, queue: `documents`) — Scans an uploaded file for viruses after upload. Currently a placeholder that marks all files as CLEAN. In production, this would integrate with ClamAV, VirusTotal, or a serverless scanning function. Dispatched automatically by `upload_file()`. The scan_status gate in `download_url()` enforces the pattern — files stuck in PENDING cannot be downloaded.

**purge_infected_files** (SystemTask, queue: `maintenance`) — Daily task that deletes files marked INFECTED older than 24 hours. Removes the file from the storage backend and deletes the Document record. FileUploadLog records survive (SET_NULL on the document FK).

**purge_stale_pending** (SystemTask, queue: `maintenance`) — Hourly task that finds documents stuck in PENDING status for more than 4 hours (indicating the scan task failed or was never dispatched) and re-dispatches `scan_uploaded_file` for each one.

### System Tasks (config/periodic_tasks.py)

**retention_purge_audit_logs** (SystemTask, queue: `maintenance`) — Weekly task that purges old records: FileUploadLog older than 90 days (configurable via `SDTA_RETENTION_UPLOAD_LOG_DAYS`), LifecycleTransitionAudit older than 365 days (`SDTA_RETENTION_LIFECYCLE_AUDIT_DAYS`), and AssignedNumber older than 365 days (`SDTA_RETENTION_ASSIGNED_NUMBER_DAYS`). FileDownloadLog records are retained indefinitely.

**retention_purge_sessions** (SystemTask, queue: `maintenance`) — Daily task that runs Django's `clearsessions` command to clean up expired database sessions.

**system_health_check** (SystemTask, queue: `default`) — Runs every 5 minutes. Verifies that the Celery worker can reach both the default and worker database connections. Returns a status dict suitable for external monitoring integration (Uptime Robot, Datadog, etc.).

### Queue Architecture (config/celery.py)

Three queues provide workload isolation:

- **default** — General-purpose tasks and health checks. Workers: `celery -A config worker -Q default,documents --concurrency=4`
- **documents** — File processing (virus scans). Same worker pool as default for simplicity.
- **maintenance** — Periodic cleanup (retention purge, session cleanup, infected file purge). Workers: `celery -A config worker -Q maintenance --concurrency=2`

### Beat Schedule

All times in UTC:

- `purge-infected-files-daily` — 3:00 AM daily
- `purge-stale-pending-hourly` — every hour at :30
- `retention-purge-audit-logs-weekly` — Sunday 2:00 AM
- `retention-purge-sessions-daily` — 4:00 AM daily
- `health-check-every-5-minutes` — every 300 seconds

Run with: `celery -A config beat --loglevel=info`

---

## 8. Tenant Provisioning (Seed Data)

When a new tenant is created, `config/seed.py` populates the initial configuration data they need to operate. The entry point is `seed_tenant(tenant_id, created_by='System')`, which runs inside a database transaction (`@transaction.atomic`).

### What Gets Seeded

**23 numbering rules** — One per entity type, all using the prefix-year-sequence pattern (e.g., C-26-0001). Each rule gets a paired NumberSequence starting at 0.

**123 lifecycle state definitions** across 29 entity types, each with 3-10 states. Followed by **170 transition rules** defining which state changes are valid. States and transitions use `bulk_create()` for performance, which skips model-level validation — safe because the seed definitions are known-good and verified by tests.

**11 value lists** with **64 items** total. These are system lists (`is_system=True`) that tenants can extend but not delete.

### Testing

`tests/test_seed.py` contains 27 test methods. Data integrity tests validate the seed definition dictionaries themselves: correct counts, unique states, exactly one default per entity type, valid transitions (no self-transitions, no transitions from final states without admin_override). Execution tests verify database record creation. An integration test verifies atomicity (all-or-nothing on failure).

---

## 9. Domain Apps

### CRM (crm, 9 models)

Person is the immutable human identity record. Customer (with NumberingMixin and LifecycleMixin) represents a business entity with states: Active, Inactive, Hold, Closed. Contact bridges people to customers and vendors. Lead and Opportunity track the sales pipeline with their own lifecycle states. Address, Phone, and Email are shared contact information records that can be attached to multiple entity types. EmailTemplate stores reusable message templates.

### Service (service, 15 models)

The core service delivery workflow: ServiceRequest (incoming requests), WorkOrder (scheduled work with team assignments via WorkOrderTeam and line items via WorkOrderLine), Quote (proposals with line items and asset associations), and Invoice (billing with line items). Payments has a 10-state lifecycle: Open → Pending → Processing → Applied → Paid, with branches for On Hold, Partially Applied, Returned, Voided, and Refunded. Bank, Accounting, and Ledger handle financial tracking. WorkOrderInvoice bridges work orders to invoices.

### Maintenance (maintenance, 5 models)

Asset tracks equipment and property with lifecycle states and numbering. Agreement manages service contracts. PreventativeMaintenance schedules recurring maintenance activities. MaintenanceSchedule defines the timing patterns.

### Procurement (procurement, 9 models)

Vendor (with lifecycle states), PurchaseOrder and PurchaseOrderLine, VendorBill for accounts payable, Requisition for internal purchase requests, and RMA for returns. All major models have lifecycle management and sequential numbering.

### Tasks (tasks, 5 models)

Task (with LifecycleMixin), TaskAssignment for team member allocation, TaskTag and TaskCategory for organization, and TaskChecklist for subtask tracking.

### Users (users, 11 models)

The custom User model (AUTH_USER_MODEL) is a TenantModel, separate from StaffUser (used for Django admin access). Supporting models include Department, Position, Role, Permission, RolePermission, UserRole, UserSkill, and AvailabilitySchedule.

### Workforce (workforce, 7 models)

WorkGroup (with NumberingMixin and LifecycleMixin) organizes teams. Supporting models for departments, positions, roles, skills, and scheduling.

### Inventory (inventory, 5 models)

InventoryItem (with NumberingMixin and LifecycleMixin), InventoryLocation for warehouse placement, StockMovement for tracking quantity changes, and InventoryAdjustment for corrections.

### Warehouse (warehouse, 6 models)

Warehouse (with LifecycleMixin), SubLocation for bin/shelf organization, ReceivingOrder for inbound shipments, WarehouseInventory for stock levels, and InventoryAudit for cycle counts.

### Fleet (fleet, 4 models)

Vehicle (with NumberingMixin and LifecycleMixin), VehicleType for classification, MaintenanceRecord for service history, and Fuel for fuel tracking.

### Automation (automation, 25 models)

The most complex app. WorkFlow (with NumberingMixin and LifecycleMixin), EquipmentType and Equipment, Trigger/Action/Condition for workflow rule definitions, WorkFlowExecution and WorkFlowLog for execution tracking, SafetyForm (with LifecycleMixin), Project/ProjectTask/ProjectResource for project management, and additional specialized models for sprints, milestones, and employee purchases.

### Infrastructure (infrastructure, 23 models)

System and tenant management: TenantState (lifecycle: Provisioning → Active → Suspended → Archived), ConfigValue (key-value settings), AuditLog (system-wide audit trail), DataExport/DataImport for migrations, and supporting models for system administration.

---

## 10. Middleware Stack

### TenantMiddleware (config/middleware.py)

Runs on every non-admin, non-internal request. After authentication, it extracts the tenant_id from the authenticated user, calls `set_current_tenant_id()` for the Python layer, and executes `SET LOCAL app.current_tenant_id` for the PostgreSQL RLS layer. Uses `SET LOCAL` (transaction-scoped) rather than `SET` (session-scoped) for PgBouncer compatibility. Clears context in the response phase.

### AdminBypassMiddleware

Reserved for future use. Currently a no-op. TenantModelAdmin targets the `worker` database alias directly.

### InternalAPIKeyMiddleware

Protects `/internal/api/` endpoints with a shared secret. Extracts Bearer token from the Authorization header and compares with `INTERNAL_API_KEY` using `secrets.compare_digest()` (constant-time comparison). Returns 401 for invalid tokens, 503 if the key is not configured.

---

## 11. Security Configuration

### Cookie Security

All cookies (session and CSRF) are configured with Secure, HttpOnly, and SameSite=Lax flags. SSL redirect is enabled, HSTS is set to one year with subdomains included, X-Frame-Options is DENY, and content type sniffing is blocked.

### Login Lockout (django-axes)

Accounts lock after 5 failed attempts, with a 30-minute cooloff period. Lockout is tracked by both username and IP address. Successful login resets the failure counter.

### Content Security Policy (django-csp)

Per-request nonce generation for scripts and styles. Allows Stripe (js.stripe.com, api.stripe.com) and Pusher (ws.pusherapp.com) as external sources. Images allow data: URIs and HTTPS sources.

### External Integrations

Stripe for payment processing (secret key and webhook secret from environment). Pusher for real-time WebSocket notifications (app ID, key, secret, and cluster from environment).

---

## 12. Testing Infrastructure

### SDTATestCase (tests/base.py)

All tests inherit from `SDTATestCase`, which provides shared tenant fixtures, automatic tenant context management (set in setUp, cleared in tearDown), and factory helpers for creating test data: `make_person()`, `make_customer()`, `make_contact()`, `make_user()`, `make_department()`, `make_position()`, `make_role()`, `make_product()`, `make_vendor()`, `make_warehouse()`, `make_sub_location()`, and others.

### Test Settings (config/settings_test.py)

Uses an in-memory SQLite-compatible setup with the worker alias mirrored to default. Celery tasks run synchronously (`CELERY_TASK_ALWAYS_EAGER = True`). CSP and axes middleware are disabled. Logging is silenced except for critical errors.

### Test Modules

25 test files covering all major areas: tenant model isolation, security boundaries, Django admin views, all domain apps (CRM, service, maintenance, procurement, tasks, workforce, fleet, warehouse, inventory, automation, infrastructure), value lists, seed data integrity, file storage operations, and Celery task behavior.

---

## 13. Configuration Reference

### Required Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | (none, required) |
| `ALLOWED_HOSTS` | Comma-separated host list | (none, required) |
| `SDTA_DB_PASSWORD` | Runtime DB password | (none, required) |
| `SDTA_MIGRATION_DB_PASSWORD` | Worker/migration DB password | (none, required) |
| `CELERY_BROKER_URL` | Redis broker URL | (none, required) |
| `STRIPE_SECRET_KEY` | Stripe API key | (none, required) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | (none, required) |
| `PUSHER_APP_ID` | Pusher app identifier | (none, required) |
| `PUSHER_KEY` | Pusher API key | (none, required) |
| `PUSHER_SECRET` | Pusher API secret | (none, required) |
| `INTERNAL_API_KEY` | Shared secret for internal API | (none, required) |

### Optional Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DEBUG` | Django debug mode | `False` |
| `SDTA_DB_NAME` | Database name | `serviz_db` |
| `SDTA_DB_USER` | Runtime DB user | `djangouser` |
| `SDTA_DB_HOST` | Database host | `localhost` |
| `SDTA_DB_PORT` | Database port | `5432` |
| `SDTA_DB_SSLMODE` | PostgreSQL SSL mode | `disable` |
| `SDTA_MIGRATION_DB_USER` | Worker DB user | `djangouser` |
| `SDTA_STORAGE_BACKEND` | File storage backend | `local` |
| `SDTA_S3_ACCESS_KEY` | S3 access key | (empty) |
| `SDTA_S3_SECRET_KEY` | S3 secret key | (empty) |
| `SDTA_S3_BUCKET_NAME` | S3 bucket name | `servizdesk-files` |
| `SDTA_S3_REGION` | S3 region | `nyc3` |
| `SDTA_S3_ENDPOINT_URL` | S3 endpoint URL | `https://nyc3.digitaloceanspaces.com` |
| `SDTA_MAX_FILE_SIZE_MB` | Max upload size in MB | `25` |
| `SDTA_PRESIGNED_URL_EXPIRY` | Presigned URL lifetime (seconds) | `3600` |
| `PUSHER_CLUSTER` | Pusher cluster | `us2` |
| `SDTA_INTERNAL_BASE_URL` | Internal API base URL | `http://localhost:8000` |

### Retention Settings (optional, set in settings.py)

| Setting | Description | Default |
|---|---|---|
| `SDTA_RETENTION_UPLOAD_LOG_DAYS` | FileUploadLog retention | 90 days |
| `SDTA_RETENTION_LIFECYCLE_AUDIT_DAYS` | LifecycleTransitionAudit retention | 365 days |
| `SDTA_RETENTION_ASSIGNED_NUMBER_DAYS` | AssignedNumber retention | 365 days |

### Allowed MIME Types

`application/pdf`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `text/csv`, `text/plain`, `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `image/svg+xml`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`

---

## Architectural Patterns Summary

**Multi-tenancy**: TenantModel + TenantManager + RLS + TenantMiddleware + TenantAwareTask — five layers of isolation.

**Three-model pattern**: Used by both Numbering (Rule → Sequence → AssignedNumber) and Lifecycle (StateDef → TransitionRule → TransitionAudit). Definition models are tenant-configurable, runtime models track state, audit models are immutable.

**Exclusive arc**: Notes and Documents use 25 nullable parent FKs with exactly-one validation. Shared via ExclusiveArcMixin in config/base_models.py. Partial indexes per FK field for query performance.

**Immutability**: AssignedNumber, LifecycleTransitionAudit, FileDownloadLog, and Document (file metadata fields only). Enforced via save()/delete() overrides and empty default_permissions.

**Service layer**: Business logic lives in `services.py` files (numbering, lifecycle, notes, documents, storage), not in models or views. Models handle validation and persistence; services handle orchestration.

**Mixin composition**: NumberingMixin and LifecycleMixin attach to domain models via class attributes (`numbering_entity_type`, `lifecycle_entity_type`). Mixins delegate to services for actual logic.

**Dual-backend storage**: Local filesystem for development, S3-compatible for production. Same key structure and API regardless of backend. Files never served through Django — always presigned URLs or media paths.

**Tenant-aware Celery**: TenantAwareTask automatically manages context. SystemTask for cross-tenant operations. Three queues for workload isolation. Beat schedule for periodic maintenance.
