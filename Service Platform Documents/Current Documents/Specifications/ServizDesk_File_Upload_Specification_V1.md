# ServizDesk File Upload Specification (Top-Down Design)
**Document Version:** V1
**Status:** Approved (Resolves Gap 3.5)

## 1. Overview
This specification establishes the authoritative standards for file handling across the ServizDesk ecosystem. Following the **Top-Down Design** philosophy, these constraints are designed to support high-performance enterprise operations while ensuring multi-tenant security and storage integrity.

## 2. Infrastructure Standards
- **Storage Provider**: S3-Compatible Object Storage.
- **Encryption**: AES-256 (At-Rest) and TLS 1.3 (In-Transit).
- **Versioning**: Enabled for all documents to prevent accidental data loss.

## 3. Mandatory Constraints

### 3.1 File Size & Quota
- **Maximum Single File Size**: **100 MB**. 
    - This allows for high-definition site photos, complex architectural PDFs, and technical training clips.
- **Storage Cap Enforcement**:
    1. **Pre-Stream Check**: Before an upload begins, the backend retrieves the tenant's `storage_limit_bytes` from `TenantState` and checks `StorageTracker.total_bytes_used + StorageTracker.pending_bytes`. If `total_bytes_used + pending_bytes >= storage_limit_bytes`, the request is rejected with a `413 Payload Too Large` error.
    2. **Byte-Counter Termination**: During the upload stream, a proxy-level byte counter monitors the incoming data. If `total_bytes_used + pending_bytes + bytes_received > storage_limit_bytes`, the connection is forcibly terminated.
    3. **Quota Lock**: While a file is in Quarantine, its `file_size_bytes` is immediately added to `StorageTracker.pending_bytes` to prevent "over-drafting" storage via parallel uploads. On promotion to Clean, the value moves from `pending_bytes` to `total_bytes_used`. On Infected deletion, `pending_bytes` is decremented.

### 3.2 Supported Formats
ServizDesk supports a broad range of professional file types. 
- **Images**: All standard formats (JPG, PNG, GIF, HEIC, TIFF, WebP).
- **Documents**: All office and technical formats (PDF, DOCX, XLSX, PPTX, CSV, TXT, RTF).
- **CAD/Vector**: .dwg, .svg, .ai (Common in specialized field service).
- **Compressed**: .zip, .7z (For archiving related records).
- **Prohibited**: Executable binaries (.exe, .dmg, .sh, .bat) are strictly blocked at the gateway.

### 3.3 Security & Validation
1. **MIME-Type Sniffing**: The system MUST verify the magic bytes of every file to ensure the extension matches the actual content.
2. **Virus Scanning (Quarantine & Promotion Workflow)**:
    - **Stage 1 (Upload)**: Files are written to an isolated **Quarantine S3 Bucket/Prefix**. The database record is created with `scan_status = Pending` and is hidden from standard list views.
    - **Stage 2 (Trigger)**: S3 `s3:ObjectCreated` event triggers a Celery security worker.
    - **Stage 3 (Scan)**: The worker downloads the file into a RAM-disk and scans it using **ClamAV**.
    - **Stage 4 (Decision)**:
        - **If Clean**: The file is "Promoted" (moved) to the **Clean S3 Bucket/Prefix**, and `scan_status` is updated to `Clean`. The file becomes visible.
        - **If Infected**: The file is **deleted immediately**. A `Notification` is created for Administrators: "Malicious File Blocked: [Filename]". `scan_status` is updated to `Infected`.
3. **Filename Normalization**: All filenames are sanitized to remove special characters and whitespace before storage.

### 3.4 Object Storage Pathing (Organization)
To ensure absolute isolation and prevent collision, all files follow a strict directory structure:
- **Format**: `/tenant-{tenant_uuid}/{domain_key}/{entity_name}/{record_uuid}/{file_uuid}.{ext}`
- **Domain Keys**: `crm`, `service`, `billing`, `operations`, `fleet`.
- **Example**: `/tenant-abc/service/work-order/uuid-456/uuid-789.pdf`

## 4. Metadata Storage
The `Document` table in the database MUST store the following for every upload:
- `file_key` (The full path in S3)
- `original_filename`
- `mime_type`
- `file_size_bytes`
- `sha256_hash` (For integrity checking)
- `scan_status` (Pending/Clean/Infected)

---

## 5. File Download Security — Pre-Signed URLs

### 5.1 The Problem with Direct S3 URLs

The S3 object storage bucket that holds tenant files must be **completely private** — no public read access, no public ACLs, no static hosting. This means a raw S3 URL like `https://spaces.digitalocean.com/bucket/tenant-abc/service/work-order/...` cannot be accessed by anyone, including authenticated users, without additional authorization.

The secure access pattern is the **pre-signed URL**: a temporary, cryptographically signed URL that grants access to a single object for a limited time window. The signing is performed server-side using the platform's AWS/Spaces credentials. Anyone who holds the URL can access the file during the window — so the URL must only be issued after authentication and tenant verification.

### 5.2 Mandatory Access Pattern

**All file downloads and inline previews must go through a Django view.** The S3 key (file path) must never be exposed directly in the browser or in API responses. The sequence for every file access request is:

```
1. Authenticated request arrives at Django file access endpoint
   e.g. GET /files/<document_uuid>/download/

2. Django looks up Document record by UUID.
   If not found → 404 Not Found.

3. Django verifies Document.tenant_id == request.user.tenant_id.
   If mismatch → 403 Forbidden. (Cross-tenant access attempt.)

4. Django verifies Document.scan_status == 'Clean'.
   If Pending or Infected → 403 Forbidden.

5. Django calls boto3 to generate a pre-signed URL for the S3 key.
   Expiry: 15 minutes.

6. Django returns an HTTP 302 redirect to the pre-signed URL.
   The browser follows the redirect directly to S3/Spaces.
   The S3 key is never returned to the client as a plain string.
```

### 5.3 Pre-Signed URL Rules

| Rule | Requirement |
|------|-------------|
| Expiry | 15 minutes maximum. This limits the window an intercepted URL remains exploitable. |
| Scope | One URL per file per request. Pre-signed URLs are not cached or stored — they are generated fresh on each valid access request. |
| Bucket access | The S3 bucket has no public ACL. All objects default to private. Pre-signed URLs are the only access path. |
| S3 key exposure | The `file_key` column must never appear in API responses, HTMX fragments, or HTML attributes. Only `document_uuid` is exposed to the frontend. |
| Scan gate | Only documents with `scan_status = Clean` are eligible for pre-signed URL generation. Pending and Infected files cannot be accessed regardless of authentication status. |
| Tenant gate | Document lookup always cross-checks `tenant_id` before generating the URL. An authenticated user from Tenant A cannot obtain a pre-signed URL for a file belonging to Tenant B. |

### 5.4 Why This Matters

Without this pattern, several attack vectors are open:

| Missing Control | Risk |
|----------------|------|
| Public S3 bucket | Any person on the internet can download any tenant file if they know (or guess) the object path |
| Long-lived or permanent URLs | An intercepted or leaked link remains exploitable indefinitely |
| No tenant verification before URL generation | An authenticated employee of Tenant A could craft a request to obtain a pre-signed URL for Tenant B's files |
| S3 key exposed in HTML | An attacker with access to one tenant account can enumerate the storage structure and attempt to access other records |

### 5.5 Local Development

In local development, file storage uses the local filesystem (`FileSystemStorage`). Pre-signed URL generation is not used — Django serves files directly via standard file serving. The pre-signed URL flow activates only in staging and production environments where `django-storages` routes to S3/Spaces.
