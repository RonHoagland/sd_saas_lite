# ServizmaDesk File Upload Specification (Top-Down Design)
**Document Version:** V1
**Status:** Approved (Resolves Gap 3.5)

## 1. Overview
This specification establishes the authoritative standards for file handling across the ServizmaDesk ecosystem. Following the **Top-Down Design** philosophy, these constraints are designed to support high-performance enterprise operations while ensuring multi-tenant security and storage integrity.

## 2. Infrastructure Standards
- **Storage Provider**: S3-Compatible Object Storage.
- **Encryption**: AES-256 (At-Rest) and TLS 1.3 (In-Transit).
- **Versioning**: Enabled for all documents to prevent accidental data loss.

## 3. Mandatory Constraints

### 3.1 File Size & Quota
- **Maximum Single File Size**: **100 MB**. 
    - This allows for high-definition site photos, complex architectural PDFs, and technical training clips.
- **Storage Cap Enforcement**:
    1. **Pre-Stream Check**: Before an upload begins, the backend retrieves the tenant's `storage_limit` (e.g., 3GB) from `TenantState` and the `current_usage` from `StorageTracker`. If `current_usage >= storage_limit`, the request is rejected with a `413 Payload Too Large` error.
    2. **Byte-Counter Termination**: During the upload stream, a proxy-level byte counter monitors the incoming data. If `current_usage + bytes_received > storage_limit`, the connection is forcibly terminated.
    3. **Quota Lock**: While a file is in Quarantine, its `file_size_bytes` is already added to a `pending_quota` counter to prevent "over-drafting" storage via parallel uploads.

### 3.2 Supported Formats
ServizmaDesk supports a broad range of professional file types. 
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
