# documents/tasks.py
# Celery tasks for the Documents app.
# Source: Note & Document Implementation Spec V1, Section 5.
#
# Tasks:
#   - scan_uploaded_file: Virus scan a newly uploaded document.
#   - purge_infected_files: Periodic cleanup of infected files.

import logging

from celery import shared_task

from config.base_task import TenantAwareTask, SystemTask
from .storage import _get_backend as _storage_backend

logger = logging.getLogger('sdta.documents.tasks')


def _get_backend():
    """
    Test seam for patching backend access in task tests.
    """
    return _storage_backend()


@shared_task(
    base=TenantAwareTask,
    bind=True,
    name='documents.scan_uploaded_file',
    max_retries=3,
    default_retry_delay=30,
    queue='documents',
)
def scan_uploaded_file(self, tenant_id, document_id):
    """
    Scan an uploaded file for viruses/malware.

    Called automatically by upload_file() after a successful upload.
    Updates the Document's scan_status to CLEAN or INFECTED.

    This is a placeholder implementation that marks files as CLEAN.
    In production, this would integrate with ClamAV, VirusTotal,
    or a similar scanning service.

    Args:
        tenant_id: UUID string of the tenant.
        document_id: UUID string of the Document to scan.
    """
    from .models import Document, ScanStatus
    from .storage import update_scan_status

    logger.info(
        'Scanning document %s for tenant %s',
        document_id, tenant_id,
    )

    # Fetch the document using all_objects (bypasses tenant filter
    # since tenant context is set by TenantAwareTask, but all_objects
    # is safer for background tasks).
    try:
        doc = Document.all_objects.get(id=document_id, tenant_id=tenant_id)
    except Document.DoesNotExist:
        logger.error(
            'Document %s not found for tenant %s — skipping scan',
            document_id, tenant_id,
        )
        return {'status': 'not_found', 'document_id': document_id}

    # Skip if already scanned
    if doc.scan_status != ScanStatus.PENDING:
        logger.info(
            'Document %s already has scan_status=%s — skipping',
            document_id, doc.scan_status,
        )
        return {'status': 'already_scanned', 'document_id': document_id}

    # ── Scan implementation ───────────────────────────────────────────────
    # TODO: Replace with real virus scanning integration.
    #
    # Production options:
    #   1. ClamAV via clamd socket:
    #      import clamd
    #      cd = clamd.ClamdUnixSocket()
    #      result = cd.scan(file_path)
    #
    #   2. VirusTotal API:
    #      POST file hash to /files/{hash} endpoint
    #      Poll for analysis results
    #
    #   3. AWS/DO serverless function:
    #      Trigger a Lambda/Function that runs ClamAV on the S3 object
    #
    # For now, all files are marked CLEAN. This is safe for development
    # because the scan_status gate in download_url() enforces the pattern —
    # files stuck in PENDING cannot be downloaded.
    # ──────────────────────────────────────────────────────────────────────

    new_status = ScanStatus.CLEAN

    try:
        update_scan_status(document_id, tenant_id, new_status)
    except Exception as exc:
        logger.error(
            'Failed to update scan_status for document %s: %s',
            document_id, exc,
        )
        raise self.retry(exc=exc)

    logger.info(
        'Document %s scan complete: %s',
        document_id, new_status,
    )

    return {
        'status': 'scanned',
        'document_id': document_id,
        'scan_result': new_status,
    }


@shared_task(
    base=SystemTask,
    bind=True,
    name='documents.purge_infected_files',
    max_retries=1,
    queue='maintenance',
)
def purge_infected_files(self):
    """
    Periodic task: delete files marked as INFECTED older than 24 hours.

    Runs as a system task (no tenant context) because it iterates across
    all tenants. Uses the `worker` DB alias for cross-tenant access.

    Infected files are removed from storage and their Document records
    are deleted. FileUploadLog records are preserved for audit.
    """
    from datetime import timedelta
    from django.utils import timezone
    from .models import Document, ScanStatus
    cutoff = timezone.now() - timedelta(hours=24)

    infected_docs = Document.all_objects.filter(
        scan_status=ScanStatus.INFECTED,
        created_on__lt=cutoff,
    ).select_related()

    count = 0
    backend = _get_backend()

    for doc in infected_docs:
        try:
            backend.delete(doc.file_key)
            # Delete the Document record. FileUploadLog.document is SET_NULL,
            # so the log survives. FileDownloadLog should not exist for
            # infected files (download_url blocks non-CLEAN downloads).
            doc.delete()
            count += 1
            logger.info(
                'Purged infected document %s (tenant %s)',
                doc.id, doc.tenant_id,
            )
        except Exception as exc:
            logger.error(
                'Failed to purge infected document %s: %s',
                doc.id, exc,
            )

    logger.info('Purged %d infected documents', count)
    return {'purged_count': count}


@shared_task(
    base=SystemTask,
    bind=True,
    name='documents.purge_stale_pending',
    max_retries=1,
    queue='maintenance',
)
def purge_stale_pending(self):
    """
    Periodic task: flag documents stuck in PENDING scan_status for > 4 hours.

    These are files where the scan task failed or was never dispatched.
    This task re-dispatches the scan for them so they don't remain in limbo.
    """
    from datetime import timedelta
    from django.utils import timezone
    from .models import Document, ScanStatus

    cutoff = timezone.now() - timedelta(hours=4)

    stale_docs = Document.all_objects.filter(
        scan_status=ScanStatus.PENDING,
        created_on__lt=cutoff,
    )

    count = 0
    for doc in stale_docs:
        try:
            scan_uploaded_file.delay(str(doc.tenant_id), str(doc.id))
            count += 1
            logger.info(
                'Re-dispatched scan for stale document %s (tenant %s)',
                doc.id, doc.tenant_id,
            )
        except Exception as exc:
            logger.error(
                'Failed to re-dispatch scan for document %s: %s',
                doc.id, exc,
            )

    logger.info('Re-dispatched scans for %d stale documents', count)
    return {'redispatched_count': count}
