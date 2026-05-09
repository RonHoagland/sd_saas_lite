# tests/test_celery_tasks.py
# Tests for Celery task infrastructure and document background tasks.
#
# All tests run with CELERY_TASK_ALWAYS_EAGER = True (settings_test.py),
# so tasks execute synchronously in the test process.

import uuid
from unittest.mock import patch, MagicMock
from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from tests.base import SDTATestCase
from config.base_task import TenantAwareTask, SystemTask
from config.tenant_context import get_current_tenant_id, clear_current_tenant_id


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def make_upload(name='test.pdf', content=b'test file content', content_type='application/pdf'):
    return SimpleUploadedFile(name, content, content_type=content_type)


# ═══════════════════════════════════════════════════════════════════════════════
# TenantAwareTask base class tests
# ═══════════════════════════════════════════════════════════════════════════════

class TenantAwareTaskTest(TestCase):
    """Tests for the TenantAwareTask base class."""

    def test_extract_tenant_id_from_args(self):
        """tenant_id extracted from first positional arg."""
        task = TenantAwareTask()
        tid = uuid.uuid4()
        result = task._extract_tenant_id((str(tid),), {})
        self.assertEqual(result, str(tid))

    def test_extract_tenant_id_from_kwargs(self):
        """tenant_id extracted from kwargs when present."""
        task = TenantAwareTask()
        tid = uuid.uuid4()
        result = task._extract_tenant_id((), {'tenant_id': str(tid)})
        self.assertEqual(result, str(tid))

    def test_extract_tenant_id_kwargs_preferred_over_args(self):
        """kwargs take precedence over args."""
        task = TenantAwareTask()
        tid_arg = uuid.uuid4()
        tid_kwarg = uuid.uuid4()
        result = task._extract_tenant_id((str(tid_arg),), {'tenant_id': str(tid_kwarg)})
        self.assertEqual(result, str(tid_kwarg))

    def test_extract_tenant_id_none_when_empty(self):
        """Returns None when no args or kwargs."""
        task = TenantAwareTask()
        result = task._extract_tenant_id((), {})
        self.assertIsNone(result)

    def test_default_retry_policy(self):
        """Verify default retry settings."""
        self.assertEqual(TenantAwareTask.max_retries, 3)
        self.assertEqual(TenantAwareTask.default_retry_delay, 60)
        self.assertTrue(TenantAwareTask.retry_backoff)
        self.assertTrue(TenantAwareTask.retry_jitter)

    def test_before_start_sets_tenant_context(self):
        """before_start() sets tenant context from args."""
        task = TenantAwareTask()
        task.name = 'test_task'
        tid = str(uuid.uuid4())
        task.before_start('task-id-123', (tid,), {})
        self.assertEqual(get_current_tenant_id(), tid)
        clear_current_tenant_id()

    def test_after_return_clears_tenant_context(self):
        """after_return() clears tenant context."""
        task = TenantAwareTask()
        task.name = 'test_task'
        tid = str(uuid.uuid4())
        task.before_start('task-id-123', (tid,), {})
        self.assertEqual(get_current_tenant_id(), tid)
        task.after_return('SUCCESS', None, 'task-id-123', (tid,), {}, None)
        self.assertIsNone(get_current_tenant_id())


class SystemTaskTest(TestCase):
    """Tests for the SystemTask base class."""

    def test_default_retry_policy(self):
        """Verify default retry settings."""
        self.assertEqual(SystemTask.max_retries, 3)
        self.assertEqual(SystemTask.default_retry_delay, 120)

    def test_before_start_clears_tenant_context(self):
        """System tasks ensure no tenant context leaks in."""
        from config.tenant_context import set_current_tenant_id
        set_current_tenant_id(str(uuid.uuid4()))

        task = SystemTask()
        task.name = 'system_test_task'
        task.before_start('task-id-456', (), {})
        self.assertIsNone(get_current_tenant_id())


# ═══════════════════════════════════════════════════════════════════════════════
# Document task tests — scan_uploaded_file
# ═══════════════════════════════════════════════════════════════════════════════

class ScanUploadedFileTaskTest(SDTATestCase):
    """Tests for the scan_uploaded_file Celery task."""

    def _create_document(self, scan_status='pending'):
        """Create a Document directly for testing."""
        from documents.models import Document, ScanStatus
        customer = self.make_customer()
        doc = Document(
            tenant_id=self.tenant_id,
            original_filename='test.pdf',
            file_key=f'{self.tenant_id}/customer/{customer.id}/abc123_test.pdf',
            file_size_bytes=1024,
            mime_type='application/pdf',
            sha256_hash='a' * 64,
            scan_status=scan_status,
            customer=customer,
            created_by='test@example.com',
            updated_by='test@example.com',
        )
        doc.save()
        return doc

    def test_scan_marks_document_clean(self):
        """scan_uploaded_file marks a PENDING document as CLEAN."""
        from documents.tasks import scan_uploaded_file
        from documents.models import Document, ScanStatus

        doc = self._create_document(scan_status=ScanStatus.PENDING)

        result = scan_uploaded_file(str(self.tenant_id), str(doc.id))

        self.assertEqual(result['status'], 'scanned')
        self.assertEqual(result['scan_result'], ScanStatus.CLEAN)

        doc.refresh_from_db()
        self.assertEqual(doc.scan_status, ScanStatus.CLEAN)

    def test_scan_skips_already_scanned(self):
        """scan_uploaded_file skips documents not in PENDING status."""
        from documents.tasks import scan_uploaded_file
        from documents.models import ScanStatus

        doc = self._create_document(scan_status=ScanStatus.CLEAN)

        result = scan_uploaded_file(str(self.tenant_id), str(doc.id))

        self.assertEqual(result['status'], 'already_scanned')

    def test_scan_handles_missing_document(self):
        """scan_uploaded_file handles non-existent document gracefully."""
        from documents.tasks import scan_uploaded_file

        fake_id = str(uuid.uuid4())
        # Capture the expected logger.error so it doesn't pollute test output.
        with self.assertLogs('sdta.documents.tasks', level='ERROR') as logs:
            result = scan_uploaded_file(str(self.tenant_id), fake_id)
        self.assertEqual(result['status'], 'not_found')
        self.assertTrue(any('not found' in m for m in logs.output))


# ═══════════════════════════════════════════════════════════════════════════════
# Document task tests — purge_infected_files
# ═══════════════════════════════════════════════════════════════════════════════

class PurgeInfectedFilesTaskTest(SDTATestCase):
    """Tests for the purge_infected_files periodic task."""

    def _create_document(self, scan_status, hours_ago=0):
        """Create a Document with a specific scan_status and created_on offset."""
        from documents.models import Document
        customer = self.make_customer()
        doc = Document(
            tenant_id=self.tenant_id,
            original_filename=f'test_{scan_status}.pdf',
            file_key=f'{self.tenant_id}/customer/{customer.id}/{uuid.uuid4().hex[:12]}_test.pdf',
            file_size_bytes=1024,
            mime_type='application/pdf',
            sha256_hash='b' * 64,
            scan_status=scan_status,
            customer=customer,
            created_by='test@example.com',
            updated_by='test@example.com',
        )
        doc.save()

        # Manually backdate created_on if needed
        if hours_ago > 0:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE documents_document SET created_on = %s WHERE id = %s",
                    [timezone.now() - timedelta(hours=hours_ago), doc.id]
                )
            doc.refresh_from_db()

        return doc

    @patch('documents.tasks._get_backend')
    def test_purges_old_infected_files(self, mock_get_backend):
        """Purges infected documents older than 24 hours."""
        from documents.tasks import purge_infected_files
        from documents.models import Document, ScanStatus

        # Patch the backend import inside the task
        with patch('documents.storage._get_backend') as mock_storage_backend:
            mock_backend = MagicMock()
            mock_get_backend.return_value = mock_backend
            mock_storage_backend.return_value = mock_backend

            # Create an old infected document
            doc = self._create_document(ScanStatus.INFECTED, hours_ago=48)
            doc_id = doc.id

            result = purge_infected_files()

            self.assertEqual(result['purged_count'], 1)
            self.assertFalse(Document.all_objects.filter(id=doc_id).exists())

    def test_does_not_purge_recent_infected(self):
        """Does not purge infected documents less than 24 hours old."""
        from documents.tasks import purge_infected_files
        from documents.models import Document, ScanStatus

        doc = self._create_document(ScanStatus.INFECTED, hours_ago=0)

        result = purge_infected_files()

        self.assertEqual(result['purged_count'], 0)
        self.assertTrue(Document.all_objects.filter(id=doc.id).exists())

    def test_does_not_purge_clean_documents(self):
        """Does not purge clean documents regardless of age."""
        from documents.tasks import purge_infected_files
        from documents.models import Document, ScanStatus

        doc = self._create_document(ScanStatus.CLEAN, hours_ago=48)

        result = purge_infected_files()

        self.assertEqual(result['purged_count'], 0)
        self.assertTrue(Document.all_objects.filter(id=doc.id).exists())


# ═══════════════════════════════════════════════════════════════════════════════
# Document task tests — purge_stale_pending
# ═══════════════════════════════════════════════════════════════════════════════

class PurgeStalePendingTaskTest(SDTATestCase):
    """Tests for the purge_stale_pending periodic task."""

    def _create_document(self, scan_status, hours_ago=0):
        from documents.models import Document
        customer = self.make_customer()
        doc = Document(
            tenant_id=self.tenant_id,
            original_filename=f'stale_{scan_status}.pdf',
            file_key=f'{self.tenant_id}/customer/{customer.id}/{uuid.uuid4().hex[:12]}_test.pdf',
            file_size_bytes=512,
            mime_type='application/pdf',
            sha256_hash='c' * 64,
            scan_status=scan_status,
            customer=customer,
            created_by='test@example.com',
            updated_by='test@example.com',
        )
        doc.save()

        if hours_ago > 0:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE documents_document SET created_on = %s WHERE id = %s",
                    [timezone.now() - timedelta(hours=hours_ago), doc.id]
                )
            doc.refresh_from_db()

        return doc

    @patch('documents.tasks.scan_uploaded_file')
    def test_redispatches_stale_pending(self, mock_scan):
        """Re-dispatches scan for documents stuck in PENDING > 4 hours."""
        from documents.tasks import purge_stale_pending
        from documents.models import ScanStatus

        mock_scan.delay = MagicMock()

        doc = self._create_document(ScanStatus.PENDING, hours_ago=6)

        result = purge_stale_pending()

        self.assertEqual(result['redispatched_count'], 1)
        mock_scan.delay.assert_called_once_with(str(doc.tenant_id), str(doc.id))

    @patch('documents.tasks.scan_uploaded_file')
    def test_does_not_redispatch_recent_pending(self, mock_scan):
        """Does not re-dispatch for recent PENDING documents."""
        from documents.tasks import purge_stale_pending
        from documents.models import ScanStatus

        mock_scan.delay = MagicMock()

        self._create_document(ScanStatus.PENDING, hours_ago=1)

        result = purge_stale_pending()

        self.assertEqual(result['redispatched_count'], 0)
        mock_scan.delay.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Periodic system task tests
# ═══════════════════════════════════════════════════════════════════════════════

class HealthCheckTaskTest(TestCase):
    """Tests for the system health check task."""

    # Health check probes both default and worker DB connections; declare
    # both so Django's test runner doesn't refuse the worker query.
    databases = {'default', 'worker'}

    def test_health_check_returns_status(self):
        """Health check returns a status dict."""
        from config.periodic_tasks import system_health_check

        result = system_health_check()

        self.assertIn('status', result)
        self.assertIn('timestamp', result)
        self.assertIn('database_default', result)


class RetentionPurgeSessionsTaskTest(TestCase):
    """Tests for the session purge task."""

    def test_purge_sessions_runs(self):
        """Session purge executes without error."""
        from config.periodic_tasks import retention_purge_sessions

        result = retention_purge_sessions()

        self.assertEqual(result['status'], 'success')
