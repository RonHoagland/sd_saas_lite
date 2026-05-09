# ServizDesk Note & Document Implementation Specification V1

**Date:** March 2026
**Scope:** SDTA — Note & Document Model Implementation, Exclusive Arc Enforcement, and File Audit Trail
**Status:** Working Draft
**Adapted From:** Desktop Version `notes/`, `documents/`, `files/` modules
**Implements:** Data Models V6 Section 1.8 (Attachments — Exclusive Arc Pattern)
**Cross-References:** Data Models V6, File Upload Specification V1, Database Specification V2, Multi-Tenancy Specification V1

---

## 1. Overview

Data Models V6 Section 1.8 defines the schemas for Note and Document. File Upload Specification V1 defines the infrastructure (S3 storage, virus scanning, pre-signed URLs, security controls). This specification covers the remaining implementation gap: how the Note and Document models are built, how the exclusive arc constraint is enforced, the file audit trail models, and integration patterns for views and background tasks.

---

## 2. Note Model — Implementation Details

### 2.1 Schema

Per Data Models V6 Section 1.8. The Note model extends TenantModel and has 25 nullable parent FKs.

### 2.2 Exclusive Arc Enforcement

**Exactly one parent FK must be non-null per row.** Enforced at two levels:

#### Application Level

```python
def clean(self):
    parent_fields = [
        self.customer_id, self.contact_id, self.lead_id,
        self.opportunity_id, self.quote_id, self.invoice_id,
        self.work_order_id, self.asset_id, self.service_request_id,
        self.prev_maint_id, self.workflow_id, self.payment_id,
        self.user_id, self.vendor_id, self.purchase_order_id,
        self.work_group_id, self.task_id, self.vehicle_id,
        self.warehouse_id, self.ledger_id, self.requisition_id,
        self.rma_id, self.equipment_id, self.safety_form_id,
        self.vendor_bill_id,
    ]
    set_count = sum(1 for f in parent_fields if f is not None)
    if set_count == 0:
        raise ValidationError("A Note must be attached to exactly one parent entity.")
    if set_count > 1:
        raise ValidationError("A Note cannot be attached to multiple parent entities.")

def save(self, *args, **kwargs):
    self.clean()
    super().save(*args, **kwargs)
```

#### Database Level

A PostgreSQL CHECK constraint ensures integrity even if application validation is bypassed:

```sql
ALTER TABLE note ADD CONSTRAINT note_exclusive_arc CHECK (
    (
        (customer_id IS NOT NULL)::int +
        (contact_id IS NOT NULL)::int +
        (lead_id IS NOT NULL)::int +
        (opportunity_id IS NOT NULL)::int +
        (quote_id IS NOT NULL)::int +
        (invoice_id IS NOT NULL)::int +
        (work_order_id IS NOT NULL)::int +
        (asset_id IS NOT NULL)::int +
        (service_request_id IS NOT NULL)::int +
        (prev_maint_id IS NOT NULL)::int +
        (workflow_id IS NOT NULL)::int +
        (payment_id IS NOT NULL)::int +
        (user_id IS NOT NULL)::int +
        (vendor_id IS NOT NULL)::int +
        (purchase_order_id IS NOT NULL)::int +
        (work_group_id IS NOT NULL)::int +
        (task_id IS NOT NULL)::int +
        (vehicle_id IS NOT NULL)::int +
        (warehouse_id IS NOT NULL)::int +
        (ledger_id IS NOT NULL)::int +
        (requisition_id IS NOT NULL)::int +
        (rma_id IS NOT NULL)::int +
        (equipment_id IS NOT NULL)::int +
        (safety_form_id IS NOT NULL)::int +
        (vendor_bill_id IS NOT NULL)::int
    ) = 1
);
```

This constraint is added via Django migration using `AddConstraint` with a `CheckConstraint`.

### 2.3 Indexes

Each parent FK column receives a **partial index** (WHERE FK IS NOT NULL) to avoid indexing the many null values:

```sql
CREATE INDEX idx_note_customer ON note (tenant_id, customer_id) WHERE customer_id IS NOT NULL;
CREATE INDEX idx_note_work_order ON note (tenant_id, work_order_id) WHERE work_order_id IS NOT NULL;
-- Repeat for each parent FK
```

In Django, these are implemented via `Meta.indexes` with `condition=Q(field__isnull=False)`.

### 2.4 Cascade Delete

All parent FKs use `on_delete=CASCADE`. When a parent entity is deleted, all Notes attached to it are deleted. A Note without a parent has no business context.

### 2.5 Reverse Relationships

Each parent FK uses a unique `related_name` to avoid Django conflicts:

| Parent | related_name |
|---|---|
| Customer | `customer_notes` |
| Contact | `contact_notes` |
| WorkOrder | `work_order_notes` |
| Asset | `asset_notes` |
| Invoice | `invoice_notes` |
| Quote | `quote_notes` |
| ServiceRequest | `service_request_notes` |
| Task | `task_notes` |
| Vendor | `vendor_notes` |
| *(others follow same pattern)* | `{entity_type}_notes` |

### 2.6 Note Type Enum

| Value | Label |
|---|---|
| `INTERNAL_NOTE` | Internal Note |
| `CALL` | Call |
| `EMAIL` | Email |
| `SITE_VISIT` | Site Visit |
| `CUSTOMER_COMMENT` | Customer Comment |
| `REMINDER` | Reminder |

---

## 3. Document Model — Implementation Details

### 3.1 Schema

Per Data Models V6 Section 1.8. The Document model extends TenantModel and has the same 25 nullable parent FKs as Note, plus file metadata fields (`original_filename`, `file_key`, `file_size_bytes`, `mime_type`, `sha256_hash`, `scan_status`).

### 3.2 Exclusive Arc Enforcement

Identical to Note (Section 2.2). Same application-level validation and database CHECK constraint.

### 3.3 Reverse Relationships

Same pattern as Note, using `{entity_type}_documents`:

| Parent | related_name |
|---|---|
| Customer | `customer_documents` |
| WorkOrder | `work_order_documents` |
| *(others follow same pattern)* | `{entity_type}_documents` |

### 3.4 Scan Status Enum

| Value | Label | Access | S3 Location |
|---|---|---|---|
| `PENDING` | Pending | NOT accessible — file is in quarantine. | Quarantine S3 Bucket/Prefix |
| `CLEAN` | Clean | Accessible via pre-signed URL. | Clean S3 Bucket/Prefix (promoted from quarantine) |
| `INFECTED` | Infected | NOT accessible — file is deleted from storage. | Deleted immediately |

> **Terminology Note:** `PENDING` is the database enum value for the quarantine state described in File Upload Specification V1 Section 3.3. The ClamAV background task promotes files from `PENDING` to `CLEAN` (moving them from the quarantine prefix to the clean prefix) or marks them `INFECTED` (deleting them from S3).

### 3.5 File Key Security

Per File Upload Specification V1 Section 5.2: the `file_key` field is internal only. It must NEVER appear in:

- API/view responses
- HTMX fragments
- HTML attributes
- JavaScript variables
- Log messages visible to tenants

The only identifier exposed to the frontend is the Document's UUID (`id` field). File access uses the pre-signed URL flow defined in File Upload Specification V1 Section 5.

### 3.6 Immutability of File Metadata

Once a Document record is created, the following fields are immutable (enforced in `save()`):

- `file_key`
- `original_filename`
- `file_size_bytes`
- `mime_type`
- `sha256_hash`

Only `scan_status` may be updated (by the ClamAV background task).

---

## 4. File Audit Trail Models

### 4.1 `FileUploadLog`

Audit record for every upload attempt. Extends TenantModel.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → TenantState | Via TenantModel. |
| `document_id` | UUID FK → Document | Nullable — null if upload failed before Document creation. SET_NULL on delete. |
| `entity_type` | CharField(50) | Parent entity type. |
| `entity_id` | UUID | Parent entity ID. |
| `original_filename` | CharField(255) | Filename from upload request. |
| `file_size_bytes` | BigIntegerField, nullable | Null if failed before size detection. |
| `status` | Enum | `SUCCESS`, `FAILED`, `REJECTED`. |
| `failure_reason` | TextField, blank | Error description for `FAILED` or `REJECTED` (e.g., "Exceeds 100 MB limit", "Blocked MIME type: application/x-executable"). |
| `ip_address` | GenericIPAddressField, nullable | Client IP. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

**Indexes:**

- `(tenant_id, entity_type, entity_id)` — All uploads for a specific entity.
- `(tenant_id, status)` — Filter by outcome.
- `(created_on)` — Chronological.

### 4.2 `FileDownloadLog`

Immutable audit record for every file access (download or inline view). Does NOT extend TenantModel — uses raw fields for immutability.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Plain field (not FK). Preserved after tenant deletion. |
| `timestamp` | DateTimeField | auto_now_add, editable=False. |
| `user_id` | UUID | Plain field (not FK). Preserved after user deletion. |
| `user_display` | CharField(200) | Snapshot of user email at download time. |
| `document_id` | UUID FK → Document | PROTECT on delete. |
| `entity_type` | CharField(50) | Parent entity type. |
| `entity_id` | UUID | Parent entity ID. |
| `ip_address` | GenericIPAddressField, nullable | Client IP. |

**Immutability Enforcement:**

- `save()` raises `ValidationError` if `self.pk is not None` (blocks updates).
- `delete()` raises `ValidationError` (blocks deletion).
- `Meta.permissions = []` (no Django admin change/delete).

**Indexes:**

- `(tenant_id, document_id)` — Download history for a specific document.
- `(tenant_id, user_id)` — All downloads by a user.
- `(timestamp)` — Chronological.

---

## 5. Service Layer

### 5.1 `create_note(tenant_id, note_type, body, parent_field, parent_id, user_display)`

Creates a Note attached to the specified parent entity.

**Parameters:**

- `parent_field` — String name of the parent FK field (e.g., `"work_order_id"`).
- `parent_id` — UUID of the parent entity.

**Steps:**

1. Validate `parent_field` is a recognized FK field name.
2. Create Note with `{parent_field: parent_id}` and all other parent FKs as null.
3. `clean()` validates exactly one parent is set.
4. Save and return.

### 5.2 `get_notes_for_entity(entity_type, entity_id, tenant_id)`

Returns all Notes where the specified parent FK matches the entity_id.

### 5.3 `upload_document(request, parent_field, parent_id, file)`

Handles the full upload flow per File Upload Specification V1, creating the Document record and FileUploadLog.

### 5.4 `get_documents_for_entity(entity_type, entity_id, tenant_id)`

Returns all Documents where the specified parent FK matches the entity_id and `scan_status = CLEAN`.

### 5.5 `generate_download_url(document_id, user, ip_address)`

Per File Upload Specification V1 Section 5.2:

1. Look up Document.
2. Verify tenant isolation.
3. Verify `scan_status = CLEAN`.
4. Generate pre-signed URL (15-minute expiry).
5. Create FileDownloadLog record.
6. Return pre-signed URL.

---

## 6. Admin Interface

### 6.1 Staff Admin

Note and Document are registered via TenantModelAdmin (uses `worker` DB alias for cross-tenant visibility).

- **NoteAdmin:** list_display = (note_type, body preview, parent entity display, created_on). Filter by note_type, tenant_id.
- **DocumentAdmin:** list_display = (original_filename, mime_type, file_size_bytes, scan_status, parent entity display, created_on). Filter by scan_status, tenant_id.
- **FileUploadLogAdmin:** list_display = (original_filename, status, entity_type, created_on). Filter by status, tenant_id.
- **FileDownloadLogAdmin:** Read-only. list_display = (user_display, document, timestamp, ip_address). Filter by tenant_id.

### 6.2 Tenant Admin (SDTA)

Notes and Documents are managed inline within their parent entity views (e.g., the Work Order detail page shows its notes and documents in a tab or section). There is no standalone Note or Document list view for tenant users — notes and documents are always viewed in the context of their parent.

---

## 7. Multi-Tenancy

### 7.1 Model Inheritance

- Note extends TenantModel.
- Document extends TenantModel.
- FileUploadLog extends TenantModel.
- FileDownloadLog has `tenant_id` as a plain UUID field (not FK) for immutability.

### 7.2 RLS

All four models require PostgreSQL RLS policies in `setup_rls.sql`.

### 7.3 Cross-Tenant Protection

The exclusive arc FKs reference parent entities that are themselves tenant-scoped. Combined with RLS, this means a Document or Note can only be created for a parent entity within the current tenant. The application-level `save()` inherits tenant_id from TenantModel, and RLS prevents cross-tenant reads.

---

## 8. Governance Rules

1. Every Note and Document must have exactly one non-null parent FK (exclusive arc). Enforced at application AND database levels.
2. Parent FK deletion cascades to Notes and Documents.
3. Document file metadata (`file_key`, `original_filename`, `file_size_bytes`, `mime_type`, `sha256_hash`) is immutable after creation.
4. Only `scan_status` may be updated on a Document (by the ClamAV scanning task).
5. Documents with `scan_status != CLEAN` are never accessible regardless of user role.
6. FileDownloadLog records are immutable — cannot be updated or deleted.
7. The `file_key` field is internal only — never exposed to the frontend.
8. Notes and Documents are always displayed in the context of their parent entity, not in standalone list views.
9. File storage follows the path convention defined in File Upload Specification V1 Section 3.4.
10. Virus scanning follows the quarantine-and-promote workflow in File Upload Specification V1 Section 3.3.

---

## 9. Cross-References

| Topic | Document |
|---|---|
| Note and Document field definitions | ServizDesk Data Models V6, Section 1.8 |
| File storage, security, pre-signed URLs | ServizDesk File Upload Specification V1 |
| StorageTracker usage monitoring | ServizDesk Data Models V6, Section 1.9 |
| Plan storage limits | ServizDesk Pricing & Billing Specification V2 |
| ClamAV scanning background task | ServizDesk Background Tasks Specification V2 |
| Multi-tenancy and RLS | ServizDesk Multi-Tenancy Specification V1 |
| Database roles (default/worker) | ServizDesk Database Specification V2 |
