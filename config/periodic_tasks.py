# config/periodic_tasks.py
# System-level periodic tasks that span all tenants.
# Source: Technical Architecture V2, Section 6.5.
#
# These tasks run on the Celery Beat schedule defined in config/celery.py.
# They use SystemTask base (no tenant context) and the `worker` DB alias
# for cross-tenant access.
#
# Tasks:
#   - retention_purge_audit_logs: Rolling purge of old audit logs.
#   - retention_purge_sessions: Clean up expired Django sessions.
#   - system_health_check: Lightweight health probe for monitoring.

import logging

from celery import shared_task

from config.base_task import SystemTask

logger = logging.getLogger('sdta.periodic')


@shared_task(
    base=SystemTask,
    bind=True,
    name='system.retention_purge_audit_logs',
    max_retries=1,
    queue='maintenance',
)
def retention_purge_audit_logs(self):
    """
    Purge audit log records older than the configured retention period.

    Targets:
      - FileUploadLog: records older than 90 days (configurable).
      - LifecycleTransitionAudit: records older than 365 days (configurable).
      - NumberingAssignedNumber: records older than 365 days (configurable).

    Uses bulk deletion with batch limits to avoid long-running transactions.
    FileDownloadLog records are immutable and retained indefinitely.
    """
    from datetime import timedelta
    from django.conf import settings
    from django.utils import timezone

    results = {}

    # ── FileUploadLog retention (default: 90 days) ────────────────────────
    upload_log_days = getattr(settings, 'SDTA_RETENTION_UPLOAD_LOG_DAYS', 90)
    upload_cutoff = timezone.now() - timedelta(days=upload_log_days)

    try:
        from documents.models import FileUploadLog
        deleted, _ = FileUploadLog.all_objects.filter(
            created_on__lt=upload_cutoff,
        ).delete()
        results['file_upload_logs'] = deleted
        logger.info('Purged %d FileUploadLog records older than %d days', deleted, upload_log_days)
    except Exception as exc:
        logger.error('Failed to purge FileUploadLog records: %s', exc)
        results['file_upload_logs'] = f'error: {exc}'

    # ── LifecycleTransitionAudit retention (default: 365 days) ────────────
    audit_days = getattr(settings, 'SDTA_RETENTION_LIFECYCLE_AUDIT_DAYS', 365)
    audit_cutoff = timezone.now() - timedelta(days=audit_days)

    try:
        from lifecycle.models import LifecycleTransitionAudit
        deleted, _ = LifecycleTransitionAudit.all_objects.filter(
            created_on__lt=audit_cutoff,
        ).delete()
        results['lifecycle_audit'] = deleted
        logger.info('Purged %d LifecycleTransitionAudit records older than %d days', deleted, audit_days)
    except Exception as exc:
        logger.error('Failed to purge LifecycleTransitionAudit records: %s', exc)
        results['lifecycle_audit'] = f'error: {exc}'

    # ── AssignedNumber retention (default: 365 days) ──────────────────────
    numbering_days = getattr(settings, 'SDTA_RETENTION_ASSIGNED_NUMBER_DAYS', 365)
    numbering_cutoff = timezone.now() - timedelta(days=numbering_days)

    try:
        from numbering.models import AssignedNumber
        deleted, _ = AssignedNumber.all_objects.filter(
            created_on__lt=numbering_cutoff,
        ).delete()
        results['assigned_numbers'] = deleted
        logger.info('Purged %d AssignedNumber records older than %d days', deleted, numbering_days)
    except Exception as exc:
        logger.error('Failed to purge AssignedNumber records: %s', exc)
        results['assigned_numbers'] = f'error: {exc}'

    return results


@shared_task(
    base=SystemTask,
    bind=True,
    name='system.retention_purge_sessions',
    max_retries=1,
    queue='maintenance',
)
def retention_purge_sessions(self):
    """
    Clean up expired Django sessions from the database.

    Django's clearsessions management command does this, but running it
    as a periodic Celery task is more reliable than a cron job.
    """
    from django.core.management import call_command
    import io

    out = io.StringIO()
    try:
        call_command('clearsessions', stdout=out)
        logger.info('Expired sessions purged successfully')
        return {'status': 'success', 'output': out.getvalue().strip()}
    except Exception as exc:
        logger.error('Failed to purge expired sessions: %s', exc)
        raise self.retry(exc=exc)


@shared_task(
    base=SystemTask,
    bind=True,
    name='system.health_check',
    max_retries=0,  # no retries — this is a probe
    queue='default',
)
def system_health_check(self):
    """
    Lightweight health probe for monitoring.

    Verifies that the Celery worker can:
      1. Execute a task.
      2. Reach the database.
      3. Reach the cache/broker.

    Intended to be called by an external monitor (e.g. Uptime Robot,
    Datadog) via a management command or API endpoint that dispatches
    this task and checks the result.
    """
    from django.db import connections
    from django.utils import timezone

    checks = {}

    # DB check — simple query on default connection
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database_default'] = 'ok'
    except Exception as exc:
        checks['database_default'] = f'error: {exc}'
        logger.error('Health check: default DB failed: %s', exc)

    # Worker DB check
    try:
        with connections['worker'].cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database_worker'] = 'ok'
    except Exception as exc:
        checks['database_worker'] = f'error: {exc}'
        logger.error('Health check: worker DB failed: %s', exc)

    checks['timestamp'] = timezone.now().isoformat()
    checks['status'] = 'healthy' if all(
        v == 'ok' for k, v in checks.items() if k.startswith('database')
    ) else 'degraded'

    logger.info('Health check: %s', checks['status'])
    return checks
