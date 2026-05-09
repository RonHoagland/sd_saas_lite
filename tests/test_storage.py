# tests/test_storage.py
# Tests for the file storage service layer (documents/storage.py).

import hashlib
import uuid
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import ProtectedError

from tests.base import SDTATestCase
from documents.models import Document, FileUploadLog, FileDownloadLog, ScanStatus
from documents.storage import (
    upload_file,
    download_url,
    delete_file,
    presigned_upload_url,
    update_scan_status,
    generate_file_key,
    validate_file,
    compute_sha256,
    FileTooLargeError,
    DisallowedMimeTypeError,
    StorageBackendError,
    LocalBackend,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Helper to create an UploadedFile
# ═══════════════════════════════════════════════════════════════════════════════

def make_upload(name='test.pdf', content=b'test file content', content_type='application/pdf'):
    return SimpleUploadedFile(name, content, content_type=content_type)


# ═══════════════════════════════════════════════════════════════════════════════
# File key generation
# ═══════════════════════════════════════════════════════════════════════════════

class GenerateFileKeyTest(SDTATestCase):

    def test_key_contains_tenant_id(self):
        key = generate_file_key(self.tenant_id, 'customer', uuid.uuid4(), 'test.pdf')
        self.assertIn(str(self.tenant_id), key)

    def test_key_contains_entity_type(self):
        key = generate_file_key(self.tenant_id, 'work_order', uuid.uuid4(), 'test.pdf')
        self.assertIn('work_order', key)

    def test_key_contains_entity_id(self):
        entity_id = uuid.uuid4()
        key = generate_file_key(self.tenant_id, 'customer', entity_id, 'test.pdf')
        self.assertIn(str(entity_id), key)

    def test_key_contains_sanitized_filename(self):
        key = generate_file_key(self.tenant_id, 'customer', uuid.uuid4(), 'my report.pdf')
        self.assertIn('my_report.pdf', key)

    def test_key_sanitizes_special_chars(self):
        key = generate_file_key(self.tenant_id, 'customer', uuid.uuid4(), 'file<>:"|.pdf')
        # Special chars replaced with underscores
        self.assertNotIn('<', key)
        self.assertNotIn('>', key)

    def test_key_truncates_long_filenames(self):
        long_name = 'a' * 200 + '.pdf'
        key = generate_file_key(self.tenant_id, 'customer', uuid.uuid4(), long_name)
        # Filename portion should be ≤ 100 chars
        filename_part = key.split('/')[-1]
        # 12 char uuid + '_' + ≤100 char filename
        self.assertLessEqual(len(filename_part), 113)

    def test_key_uniqueness(self):
        args = (self.tenant_id, 'customer', uuid.uuid4(), 'test.pdf')
        key1 = generate_file_key(*args)
        key2 = generate_file_key(*args)
        self.assertNotEqual(key1, key2)  # UUID prefix makes them unique


# ═══════════════════════════════════════════════════════════════════════════════
# File validation
# ═══════════════════════════════════════════════════════════════════════════════

class ValidateFileTest(SDTATestCase):

    def test_valid_file_passes(self):
        f = make_upload()
        validate_file(f)  # Should not raise

    def test_file_too_large_raises(self):
        max_bytes = settings.SDTA_MAX_FILE_SIZE_MB * 1024 * 1024
        big_content = b'x' * (max_bytes + 1)
        f = make_upload(content=big_content)
        with self.assertRaises(FileTooLargeError):
            validate_file(f)

    def test_disallowed_mime_type_raises(self):
        f = make_upload(content_type='application/x-executable')
        with self.assertRaises(DisallowedMimeTypeError):
            validate_file(f)

    def test_allowed_mime_types(self):
        for mime_type in ['application/pdf', 'image/jpeg', 'image/png', 'text/plain']:
            f = make_upload(content_type=mime_type)
            validate_file(f)  # Should not raise


# ═══════════════════════════════════════════════════════════════════════════════
# SHA-256 hash
# ═══════════════════════════════════════════════════════════════════════════════

class ComputeSha256Test(SDTATestCase):

    def test_correct_hash(self):
        content = b'hello world'
        f = make_upload(content=content)
        expected = hashlib.sha256(content).hexdigest()
        self.assertEqual(compute_sha256(f), expected)

    def test_file_position_reset(self):
        f = make_upload(content=b'test')
        compute_sha256(f)
        # File should be back at beginning
        self.assertEqual(f.read(), b'test')

    def test_different_content_different_hash(self):
        f1 = make_upload(content=b'content A')
        f2 = make_upload(content=b'content B')
        self.assertNotEqual(compute_sha256(f1), compute_sha256(f2))


# ═══════════════════════════════════════════════════════════════════════════════
# Local backend
# ═══════════════════════════════════════════════════════════════════════════════

class LocalBackendTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        self.backend = LocalBackend()
        self.test_key = f'{self.tenant_id}/test/test_file.txt'

    def tearDown(self):
        # Clean up any test files
        full_path = Path(settings.MEDIA_ROOT) / self.test_key
        if full_path.exists():
            full_path.unlink()
        super().tearDown()

    def test_put_creates_file(self):
        f = make_upload(content=b'local test')
        self.backend.put(self.test_key, f)
        full_path = Path(settings.MEDIA_ROOT) / self.test_key
        self.assertTrue(full_path.exists())

    def test_exists_returns_true(self):
        f = make_upload(content=b'local test')
        self.backend.put(self.test_key, f)
        self.assertTrue(self.backend.exists(self.test_key))

    def test_exists_returns_false(self):
        self.assertFalse(self.backend.exists('nonexistent/file.txt'))

    def test_delete_removes_file(self):
        f = make_upload(content=b'local test')
        self.backend.put(self.test_key, f)
        self.backend.delete(self.test_key)
        self.assertFalse(self.backend.exists(self.test_key))

    def test_delete_nonexistent_no_error(self):
        self.backend.delete('nonexistent/file.txt')  # Should not raise

    def test_get_download_url(self):
        url = self.backend.get_download_url(self.test_key)
        self.assertIn(self.test_key, url)

    def test_get_upload_url_returns_none(self):
        self.assertIsNone(self.backend.get_upload_url(self.test_key))


# ═══════════════════════════════════════════════════════════════════════════════
# Upload
# ═══════════════════════════════════════════════════════════════════════════════

class UploadFileTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        self.customer = self.make_customer()
        self.user = self.make_user()

    def _upload(self, parent_field='customer', parent_id=None, **kwargs):
        if parent_id is None:
            parent_id = self.customer.id
        defaults = {
            'tenant_id': self.tenant_id,
            'parent_field': parent_field,
            'parent_id': parent_id,
            'file_obj': make_upload(),
            'user_id': self.user.id,
            'user_display': self.user.email,
        }
        defaults.update(kwargs)
        return upload_file(**defaults)

    def test_creates_document(self):
        doc = self._upload()
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.tenant_id, self.tenant_id)

    def test_document_fields_populated(self):
        doc = self._upload()
        self.assertEqual(doc.original_filename, 'test.pdf')
        self.assertEqual(doc.mime_type, 'application/pdf')
        self.assertGreater(len(doc.file_key), 0)
        self.assertGreater(len(doc.sha256_hash), 0)
        self.assertEqual(doc.scan_status, ScanStatus.PENDING)

    def test_document_parent_fk_set(self):
        doc = self._upload()
        self.assertEqual(doc.customer_id, self.customer.id)

    def test_upload_log_created(self):
        doc = self._upload()
        log = FileUploadLog.objects.filter(document=doc).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, FileUploadLog.StatusChoices.SUCCESS)
        self.assertEqual(log.original_filename, 'test.pdf')

    def test_file_stored_on_backend(self):
        doc = self._upload()
        backend = LocalBackend()
        self.assertTrue(backend.exists(doc.file_key))
        # Clean up
        backend.delete(doc.file_key)

    def test_sha256_is_correct(self):
        content = b'known content for hash test'
        expected_hash = hashlib.sha256(content).hexdigest()
        f = make_upload(content=content)
        doc = self._upload(file_obj=f)
        self.assertEqual(doc.sha256_hash, expected_hash)
        # Clean up
        LocalBackend().delete(doc.file_key)

    def test_invalid_parent_field_raises(self):
        with self.assertRaises(ValidationError):
            self._upload(parent_field='nonexistent')

    def test_file_too_large_raises(self):
        max_bytes = settings.SDTA_MAX_FILE_SIZE_MB * 1024 * 1024
        big = make_upload(content=b'x' * (max_bytes + 1))
        with self.assertRaises(FileTooLargeError):
            self._upload(file_obj=big)

    def test_disallowed_mime_raises(self):
        f = make_upload(content_type='application/x-executable')
        with self.assertRaises(DisallowedMimeTypeError):
            self._upload(file_obj=f)

    def test_failed_upload_logs_failure(self):
        with patch('documents.storage._get_backend') as mock_backend:
            mock_backend.return_value.put.side_effect = StorageBackendError('fail')
            with self.assertRaises(StorageBackendError):
                self._upload()

        log = FileUploadLog.objects.filter(
            tenant_id=self.tenant_id,
            status=FileUploadLog.StatusChoices.FAILED,
        ).first()
        self.assertIsNotNone(log)

    def test_parent_field_with_id_suffix(self):
        """parent_field='customer_id' should be normalized to 'customer'."""
        doc = self._upload(parent_field='customer_id')
        self.assertEqual(doc.customer_id, self.customer.id)

    def test_upload_with_ip_address(self):
        doc = self._upload(ip_address='192.168.1.1')
        log = FileUploadLog.objects.filter(document=doc).first()
        self.assertEqual(log.ip_address, '192.168.1.1')


# ═══════════════════════════════════════════════════════════════════════════════
# Download URL
# ═══════════════════════════════════════════════════════════════════════════════

class DownloadUrlTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        self.customer = self.make_customer()
        self.user = self.make_user()

    def _make_clean_doc(self):
        """Create a Document with CLEAN scan status."""
        doc = upload_file(
            tenant_id=self.tenant_id,
            parent_field='customer',
            parent_id=self.customer.id,
            file_obj=make_upload(),
            user_id=self.user.id,
            user_display=self.user.email,
        )
        # Mark as clean
        doc.scan_status = ScanStatus.CLEAN
        doc.save()
        return doc

    def test_returns_url(self):
        doc = self._make_clean_doc()
        url = download_url(doc, user_id=self.user.id, user_display=self.user.email)
        self.assertIn(doc.file_key, url)
        LocalBackend().delete(doc.file_key)

    def test_creates_download_log(self):
        doc = self._make_clean_doc()
        download_url(doc, user_id=self.user.id, user_display=self.user.email)
        log = FileDownloadLog.objects.filter(document=doc).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user_id, self.user.id)
        LocalBackend().delete(doc.file_key)

    def test_pending_scan_raises(self):
        doc = upload_file(
            tenant_id=self.tenant_id,
            parent_field='customer',
            parent_id=self.customer.id,
            file_obj=make_upload(),
            user_id=self.user.id,
            user_display=self.user.email,
        )
        # scan_status is PENDING by default
        with self.assertRaises(ValidationError):
            download_url(doc, user_id=self.user.id)
        LocalBackend().delete(doc.file_key)

    def test_download_log_with_ip(self):
        doc = self._make_clean_doc()
        download_url(
            doc,
            user_id=self.user.id,
            user_display=self.user.email,
            ip_address='10.0.0.1',
        )
        log = FileDownloadLog.objects.filter(document=doc).first()
        self.assertEqual(log.ip_address, '10.0.0.1')
        LocalBackend().delete(doc.file_key)


# ═══════════════════════════════════════════════════════════════════════════════
# Scan status update
# ═══════════════════════════════════════════════════════════════════════════════

class UpdateScanStatusTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        self.customer = self.make_customer()
        self.user = self.make_user()

    def test_update_to_clean(self):
        doc = upload_file(
            tenant_id=self.tenant_id,
            parent_field='customer',
            parent_id=self.customer.id,
            file_obj=make_upload(),
            user_id=self.user.id,
        )
        updated = update_scan_status(doc.id, self.tenant_id, ScanStatus.CLEAN)
        self.assertEqual(updated.scan_status, ScanStatus.CLEAN)
        LocalBackend().delete(doc.file_key)

    def test_update_to_infected(self):
        doc = upload_file(
            tenant_id=self.tenant_id,
            parent_field='customer',
            parent_id=self.customer.id,
            file_obj=make_upload(),
            user_id=self.user.id,
        )
        updated = update_scan_status(doc.id, self.tenant_id, ScanStatus.INFECTED)
        self.assertEqual(updated.scan_status, ScanStatus.INFECTED)
        LocalBackend().delete(doc.file_key)


# ═══════════════════════════════════════════════════════════════════════════════
# Delete
# ═══════════════════════════════════════════════════════════════════════════════

class DeleteFileTest(SDTATestCase):

    def setUp(self):
        super().setUp()
        self.customer = self.make_customer()
        self.user = self.make_user()

    def test_deletes_from_backend(self):
        doc = upload_file(
            tenant_id=self.tenant_id,
            parent_field='customer',
            parent_id=self.customer.id,
            file_obj=make_upload(),
            user_id=self.user.id,
        )
        file_key = doc.file_key
        delete_file(doc)
        self.assertFalse(LocalBackend().exists(file_key))

    def test_deletes_document_record(self):
        doc = upload_file(
            tenant_id=self.tenant_id,
            parent_field='customer',
            parent_id=self.customer.id,
            file_obj=make_upload(),
            user_id=self.user.id,
        )
        doc_id = doc.id
        delete_file(doc)
        self.assertFalse(Document.all_objects.filter(id=doc_id).exists())

    def test_protected_when_download_logs_exist(self):
        doc = upload_file(
            tenant_id=self.tenant_id,
            parent_field='customer',
            parent_id=self.customer.id,
            file_obj=make_upload(),
            user_id=self.user.id,
        )
        # Mark as clean and download it
        doc.scan_status = ScanStatus.CLEAN
        doc.save()
        download_url(doc, user_id=self.user.id, user_display=self.user.email)

        # Now trying to delete should raise ProtectedError
        with self.assertRaises(ProtectedError):
            delete_file(doc)
        LocalBackend().delete(doc.file_key)


# ═══════════════════════════════════════════════════════════════════════════════
# Presigned upload URL
# ═══════════════════════════════════════════════════════════════════════════════

class PresignedUploadUrlTest(SDTATestCase):

    def test_local_backend_returns_none(self):
        result = presigned_upload_url(
            self.tenant_id, 'customer', uuid.uuid4(), 'test.pdf'
        )
        self.assertIsNone(result)

    def test_invalid_parent_field_raises(self):
        with self.assertRaises(ValidationError):
            presigned_upload_url(
                self.tenant_id, 'nonexistent', uuid.uuid4(), 'test.pdf'
            )

    def test_s3_backend_returns_dict(self):
        with patch('documents.storage._get_backend') as mock:
            mock_backend = MagicMock()
            mock_backend.get_upload_url.return_value = 'https://s3.example.com/upload'
            mock.return_value = mock_backend

            result = presigned_upload_url(
                self.tenant_id, 'customer', uuid.uuid4(), 'test.pdf'
            )
            self.assertIn('file_key', result)
            self.assertIn('upload_url', result)
            self.assertEqual(result['upload_url'], 'https://s3.example.com/upload')
