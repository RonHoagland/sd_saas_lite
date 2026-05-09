# documents/storage.py
# File storage service layer for the Documents system.
# Source: Technical Architecture V2, Section 5; Note & Document Implementation Spec V1.
#
# Provides a unified API for file operations against either a local filesystem
# (development) or an S3-compatible backend like DigitalOcean Spaces (production).
#
# Key design decisions:
#   - File keys follow: {tenant_id}/{entity_type}/{entity_id}/{uuid}_{filename}
#   - SHA-256 hash computed on upload for integrity verification.
#   - Presigned URLs used for downloads — files are never served through Django.
#   - Virus scan status starts at 'pending'; a Celery task updates it to 'clean'
#     or 'infected' after async scanning.
#   - All operations are tenant-scoped and audit-logged.
#
# Usage:
#   from documents.storage import upload_file, download_url, delete_file
#
#   doc = upload_file(
#       tenant_id=tenant.id,
#       parent_field='work_order',
#       parent_id=wo.id,
#       file_obj=request.FILES['file'],
#       user_id=request.user.id,
#       user_display=request.user.email,
#       ip_address=get_client_ip(request),
#   )
#   url = download_url(doc, user_id=..., user_display=..., ip_address=...)

import hashlib
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Document, FileUploadLog, FileDownloadLog, ScanStatus
from config.base_models import PARENT_FK_FIELDS


# ═══════════════════════════════════════════════════════════════════════════════
# EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class FileTooLargeError(ValidationError):
    """Raised when a file exceeds the configured size limit."""
    pass


class DisallowedMimeTypeError(ValidationError):
    """Raised when a file's MIME type is not in the allowed list."""
    pass


class StorageBackendError(Exception):
    """Raised when the storage backend encounters an error."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# BACKEND ABSTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def _get_backend():
    """Return the appropriate storage backend based on settings."""
    backend = getattr(settings, 'SDTA_STORAGE_BACKEND', 'local')
    if backend == 's3':
        return S3Backend()
    return LocalBackend()


class LocalBackend:
    """
    Local filesystem backend for development.
    Files are stored under MEDIA_ROOT using the same key structure as S3.
    """

    def put(self, file_key, file_obj):
        """Write file to local filesystem."""
        full_path = Path(settings.MEDIA_ROOT) / file_key
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'wb') as dest:
            for chunk in file_obj.chunks():
                dest.write(chunk)

    def delete(self, file_key):
        """Delete file from local filesystem."""
        full_path = Path(settings.MEDIA_ROOT) / file_key
        if full_path.exists():
            full_path.unlink()

    def exists(self, file_key):
        """Check if a file exists locally."""
        full_path = Path(settings.MEDIA_ROOT) / file_key
        return full_path.exists()

    def get_download_url(self, file_key, expiry=None):
        """
        Return a local media URL (no presigning for local backend).
        In development, Django's media serving handles this.
        """
        return f'{settings.MEDIA_URL}{file_key}'

    def get_upload_url(self, file_key, expiry=None, content_type='application/octet-stream'):
        """
        Local backend does not use presigned upload URLs.
        Returns None — uploads go through Django directly.
        """
        return None


class S3Backend:
    """
    S3-compatible backend (DigitalOcean Spaces, AWS S3, MinIO).

    Uses boto3 directly rather than django-storages to keep full control
    over key generation, presigned URLs, and tenant isolation.
    """

    def __init__(self):
        try:
            import boto3
        except ImportError:
            raise StorageBackendError(
                "boto3 is required for S3 backend. Install with: pip install boto3"
            )

        self._client = boto3.client(
            's3',
            region_name=settings.SDTA_S3_REGION,
            endpoint_url=settings.SDTA_S3_ENDPOINT_URL,
            aws_access_key_id=settings.SDTA_S3_ACCESS_KEY,
            aws_secret_access_key=settings.SDTA_S3_SECRET_KEY,
        )
        self._bucket = settings.SDTA_S3_BUCKET_NAME

    def put(self, file_key, file_obj):
        """Upload file to S3."""
        try:
            self._client.upload_fileobj(
                file_obj,
                self._bucket,
                file_key,
                ExtraArgs={
                    'ContentType': getattr(file_obj, 'content_type', 'application/octet-stream'),
                    'ACL': 'private',
                },
            )
        except Exception as e:
            raise StorageBackendError(f"S3 upload failed: {e}") from e

    def delete(self, file_key):
        """Delete file from S3."""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=file_key)
        except Exception as e:
            raise StorageBackendError(f"S3 delete failed: {e}") from e

    def exists(self, file_key):
        """Check if a file exists in S3."""
        try:
            self._client.head_object(Bucket=self._bucket, Key=file_key)
            return True
        except self._client.exceptions.NoSuchKey:
            return False
        except Exception:
            return False

    def get_download_url(self, file_key, expiry=None):
        """Generate a presigned GET URL for downloading."""
        if expiry is None:
            # File Upload Spec V1 §5.3: 15-minute default. Settings layer
            # overrides via SDTA_PRESIGNED_URL_EXPIRY.
            expiry = getattr(settings, 'SDTA_PRESIGNED_URL_EXPIRY', 900)
        try:
            return self._client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self._bucket, 'Key': file_key},
                ExpiresIn=expiry,
            )
        except Exception as e:
            raise StorageBackendError(f"Failed to generate download URL: {e}") from e

    def get_upload_url(self, file_key, expiry=None, content_type='application/octet-stream'):
        """Generate a presigned PUT URL for direct browser upload."""
        if expiry is None:
            # File Upload Spec V1 §5.3: 15-minute default. Settings layer
            # overrides via SDTA_PRESIGNED_URL_EXPIRY.
            expiry = getattr(settings, 'SDTA_PRESIGNED_URL_EXPIRY', 900)
        try:
            return self._client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self._bucket,
                    'Key': file_key,
                    'ContentType': content_type,
                },
                ExpiresIn=expiry,
            )
        except Exception as e:
            raise StorageBackendError(f"Failed to generate upload URL: {e}") from e


# ═══════════════════════════════════════════════════════════════════════════════
# FILE KEY GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_file_key(tenant_id, entity_type, entity_id, original_filename):
    """
    Generate a unique file key for storage.

    Pattern: {tenant_id}/{entity_type}/{entity_id}/{uuid}_{sanitized_filename}

    The UUID prefix ensures uniqueness even if the same file is uploaded
    multiple times. The original filename is preserved for readability.
    """
    # Sanitize filename: keep only alphanumeric, hyphens, underscores, dots
    safe_name = ''.join(
        c if c.isalnum() or c in '-_.' else '_'
        for c in original_filename
    )
    # Truncate to prevent overly long keys
    if len(safe_name) > 100:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:96] + ext

    unique_id = uuid.uuid4().hex[:12]
    return f'{tenant_id}/{entity_type}/{entity_id}/{unique_id}_{safe_name}'


# ═══════════════════════════════════════════════════════════════════════════════
# FILE VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_file(file_obj):
    """
    Validate file size and MIME type against configured limits.

    Args:
        file_obj: Django UploadedFile (or similar with .size and .content_type).

    Raises:
        FileTooLargeError: If file exceeds SDTA_MAX_FILE_SIZE_MB.
        DisallowedMimeTypeError: If MIME type is not in SDTA_ALLOWED_MIME_TYPES.
    """
    max_size_bytes = getattr(settings, 'SDTA_MAX_FILE_SIZE_MB', 25) * 1024 * 1024

    if file_obj.size > max_size_bytes:
        raise FileTooLargeError(
            f"File size ({file_obj.size:,} bytes) exceeds the "
            f"{settings.SDTA_MAX_FILE_SIZE_MB} MB limit."
        )

    allowed_types = getattr(settings, 'SDTA_ALLOWED_MIME_TYPES', [])
    if allowed_types and file_obj.content_type not in allowed_types:
        raise DisallowedMimeTypeError(
            f"File type '{file_obj.content_type}' is not allowed. "
            f"Accepted types: {', '.join(allowed_types)}"
        )


def compute_sha256(file_obj):
    """
    Compute SHA-256 hash of a file.

    Resets the file position to the beginning after reading.
    """
    hasher = hashlib.sha256()
    file_obj.seek(0)
    for chunk in file_obj.chunks():
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API — UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════

def upload_file(
    tenant_id,
    parent_field,
    parent_id,
    file_obj,
    user_id,
    user_display='System',
    ip_address=None,
):
    """
    Upload a file and create a Document record.

    Steps:
        1. Validate file (size + MIME type).
        2. Compute SHA-256 hash.
        3. Generate a unique file key.
        4. Upload to storage backend.
        5. Create Document record (scan_status = PENDING).
        6. Create FileUploadLog (SUCCESS).
        7. Dispatch virus scan task (async).

    Args:
        tenant_id: UUID of the tenant.
        parent_field: FK field name (e.g. 'customer', 'work_order').
        parent_id: UUID of the parent entity.
        file_obj: Django UploadedFile.
        user_id: UUID of the uploading user.
        user_display: Display name for audit (email or 'System').
        ip_address: Client IP address (optional).

    Returns:
        Document instance.

    Raises:
        FileTooLargeError, DisallowedMimeTypeError, ValidationError, StorageBackendError.
    """
    # Normalize parent_field
    if parent_field.endswith('_id'):
        parent_field = parent_field[:-3]

    if parent_field not in PARENT_FK_FIELDS:
        raise ValidationError(
            f"Invalid parent_field '{parent_field}'. "
            f"Must be one of: {', '.join(PARENT_FK_FIELDS)}"
        )

    # Step 1: Validate
    validate_file(file_obj)

    # Step 2: Hash
    sha256_hash = compute_sha256(file_obj)

    # Step 3: Generate key
    file_key = generate_file_key(
        tenant_id, parent_field, parent_id, file_obj.name
    )

    # Step 4: Upload to backend
    backend = _get_backend()
    try:
        backend.put(file_key, file_obj)
    except StorageBackendError:
        # Log the failure
        FileUploadLog.objects.create(
            tenant_id=tenant_id,
            entity_type=parent_field,
            entity_id=parent_id,
            original_filename=file_obj.name,
            file_size_bytes=file_obj.size,
            status=FileUploadLog.StatusChoices.FAILED,
            failure_reason='Storage backend upload failed.',
            ip_address=ip_address,
            created_by=user_display,
            updated_by=user_display,
        )
        raise

    # Step 5: Create Document record
    doc_kwargs = {
        'tenant_id': tenant_id,
        'original_filename': file_obj.name,
        'file_key': file_key,
        'file_size_bytes': file_obj.size,
        'mime_type': getattr(file_obj, 'content_type', ''),
        'sha256_hash': sha256_hash,
        'scan_status': ScanStatus.PENDING,
        f'{parent_field}_id': parent_id,
        'created_by': user_display,
        'updated_by': user_display,
    }
    doc = Document(**doc_kwargs)
    doc.save()

    # Step 6: Log success
    FileUploadLog.objects.create(
        tenant_id=tenant_id,
        document=doc,
        entity_type=parent_field,
        entity_id=parent_id,
        original_filename=file_obj.name,
        file_size_bytes=file_obj.size,
        status=FileUploadLog.StatusChoices.SUCCESS,
        ip_address=ip_address,
        created_by=user_display,
        updated_by=user_display,
    )

    # Step 7: Dispatch async virus scan
    # Import here to avoid circular imports with Celery task registration.
    # Convention: tenant_id is always the first arg for TenantAwareTask.
    from .tasks import scan_uploaded_file
    try:
        scan_uploaded_file.delay(str(tenant_id), str(doc.id))
    except Exception:
        # Keep uploads non-blocking even when broker is unavailable in local/test envs.
        pass

    return doc


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API — DOWNLOAD URL
# ═══════════════════════════════════════════════════════════════════════════════

def download_url(document, user_id, user_display='System', ip_address=None):
    """
    Generate a download URL for a Document and log the access.

    Only documents with scan_status = CLEAN are downloadable.

    Args:
        document: Document instance.
        user_id: UUID of the requesting user.
        user_display: Display name for audit.
        ip_address: Client IP address (optional).

    Returns:
        String URL (presigned for S3, media path for local).

    Raises:
        ValidationError: If document scan_status is not CLEAN.
    """
    if document.scan_status != ScanStatus.CLEAN:
        raise ValidationError(
            f"Document '{document.original_filename}' cannot be downloaded. "
            f"Scan status: {document.scan_status}."
        )

    backend = _get_backend()
    url = backend.get_download_url(document.file_key)

    # Determine entity_type and entity_id from the document's parent FK
    entity_type = None
    entity_id = None
    for field_name in PARENT_FK_FIELDS:
        fk_id = getattr(document, f'{field_name}_id', None)
        if fk_id is not None:
            entity_type = field_name
            entity_id = fk_id
            break

    # Audit log (immutable)
    FileDownloadLog(
        tenant_id=document.tenant_id,
        user_id=user_id,
        user_display=user_display,
        document=document,
        entity_type=entity_type or 'unknown',
        entity_id=entity_id or uuid.UUID(int=0),
        ip_address=ip_address,
    ).save()

    return url


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API — PRESIGNED UPLOAD URL (for direct browser→S3 uploads)
# ═══════════════════════════════════════════════════════════════════════════════

def presigned_upload_url(
    tenant_id,
    parent_field,
    parent_id,
    original_filename,
    content_type='application/octet-stream',
):
    """
    Generate a presigned URL for direct browser-to-S3 upload.

    The client uploads directly to S3 using this URL, then calls
    confirm_upload() to create the Document record.

    Returns:
        dict with 'file_key' and 'upload_url', or None if local backend.
    """
    if parent_field.endswith('_id'):
        parent_field = parent_field[:-3]

    if parent_field not in PARENT_FK_FIELDS:
        raise ValidationError(
            f"Invalid parent_field '{parent_field}'. "
            f"Must be one of: {', '.join(PARENT_FK_FIELDS)}"
        )

    file_key = generate_file_key(tenant_id, parent_field, parent_id, original_filename)
    backend = _get_backend()
    upload_url = backend.get_upload_url(file_key, content_type=content_type)

    if upload_url is None:
        return None  # Local backend — upload through Django instead

    return {
        'file_key': file_key,
        'upload_url': upload_url,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API — DELETE
# ═══════════════════════════════════════════════════════════════════════════════

def delete_file(document, user_display='System'):
    """
    Delete a file from storage and remove the Document record.

    Steps:
        1. Delete the file from the storage backend.
        2. Delete the Document record (cascades to FileUploadLog.document FK).

    Note: FileDownloadLog records are preserved (PROTECT FK) — the Document
    must not have download logs, or they must be handled by the caller.
    Actually, FileDownloadLog has on_delete=PROTECT, so this will raise
    ProtectedError if download logs exist. This is intentional — files
    with download history should not be permanently deleted.

    Args:
        document: Document instance.
        user_display: Audit trail info.

    Raises:
        StorageBackendError: If backend deletion fails.
        ProtectedError: If FileDownloadLog records exist.
    """
    backend = _get_backend()
    backend.delete(document.file_key)
    document.delete()


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API — SCAN STATUS UPDATE
# ═══════════════════════════════════════════════════════════════════════════════

def update_scan_status(document_id, tenant_id, new_status):
    """
    Update the scan_status of a Document after virus scanning.

    Called by the async scan task. Only scan_status is mutable on Document
    (the save() override enforces immutability of all other fields).

    Args:
        document_id: UUID of the Document.
        tenant_id: UUID of the tenant.
        new_status: ScanStatus value ('clean' or 'infected').

    Returns:
        Updated Document instance.
    """
    doc = Document.all_objects.get(id=document_id, tenant_id=tenant_id)

    # Direct field update to bypass immutability check in save()
    # (save() blocks changes to file metadata fields but scan_status is exempt
    # because the immutability check compares specific fields, not scan_status).
    doc.scan_status = new_status
    doc.save()
    return doc
