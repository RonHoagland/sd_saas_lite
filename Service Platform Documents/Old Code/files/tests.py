"""
File Storage Tests - Programming Tests + User/Admin Tests

Tests cover:
1. File storage utilities (upload, download, delete)
2. File metadata management
3. Audit logging (upload and download logs)
4. Permission and error handling
5. Admin interface functionality
"""

import io
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
import uuid

from .models import StoredFile, FileUploadLog, FileDownloadLog
from .utils import (
	store_file, get_file_data, delete_file, get_entity_files,
	sanitize_filename, generate_stored_filename, calculate_checksum,
	validate_upload, FileSizeExceededError, InvalidMimeTypeError, FileNotFoundError
)


# ============================================================================
# PROGRAMMING TESTS - File Storage Utility Logic
# ============================================================================

class TestFileUtilities(TestCase):
	"""Test file utility functions."""
	
	def test_sanitize_filename_removes_dangerous_chars(self):
		"""Test filename sanitization."""
		result = sanitize_filename("test<script>.pdf")
		self.assertEqual(result, "testscript.pdf")
	
	def test_sanitize_filename_preserves_safe_chars(self):
		"""Test that safe characters are preserved."""
		result = sanitize_filename("my-document_2024.pdf")
		self.assertEqual(result, "my-document_2024.pdf")
	
	def test_generate_stored_filename_has_prefix(self):
		"""Test that generated filename has UUID prefix."""
		result = generate_stored_filename("test.pdf")
		parts = result.split("-", 1)
		self.assertEqual(len(parts), 2)
		self.assertTrue(parts[0])  # UUID prefix
		self.assertIn("test.pdf", result)
	
	def test_calculate_checksum_bytes(self):
		"""Test checksum calculation from bytes."""
		data = b"test data"
		checksum = calculate_checksum(data)
		self.assertEqual(len(checksum), 64)  # SHA-256 hex is 64 chars
		self.assertTrue(all(c in '0123456789abcdef' for c in checksum))
	
	def test_calculate_checksum_file_like(self):
		"""Test checksum calculation from file-like object."""
		data = b"test data"
		file_obj = io.BytesIO(data)
		checksum = calculate_checksum(file_obj)
		self.assertEqual(len(checksum), 64)
		# Verify file position reset
		self.assertEqual(file_obj.tell(), 0)
	
	def test_validate_upload_accepts_valid_file(self):
		"""Test upload validation accepts valid file."""
		user = User.objects.create_user(username='testuser', password='pass')
		data = b"x" * 1000  # 1 KB
		is_valid, error = validate_upload("test.pdf", data, "application/pdf", user, "test_entity")
		self.assertTrue(is_valid)
		self.assertIsNone(error)
	
	def test_validate_upload_rejects_oversized_file(self):
		"""Test upload validation rejects files exceeding hard limit."""
		user = User.objects.create_user(username='testuser', password='pass')
		# 501 MB (exceeds 500 MB limit)
		data = b"x" * (501 * 1024 * 1024)
		is_valid, error = validate_upload("test.pdf", data, "application/pdf", user, "test_entity")
		self.assertFalse(is_valid)
		self.assertIn("hard limit", error.lower())


class TestFileStorage(TestCase):
	"""Test file storage operations."""
	
	def setUp(self):
		self.user = User.objects.create_user(username='testuser', password='pass')
	
	def test_store_file_creates_metadata(self):
		"""Test store_file creates metadata record."""
		file_data = b"test content"
		entity_id = uuid.uuid4()
		
		stored = store_file(
			entity_type='test_entity',
			entity_id=entity_id,
			original_filename='test.txt',
			file_data=file_data,
			mime_type='text/plain',
			user=self.user
		)
		
		self.assertIsNotNone(stored.id)
		self.assertEqual(stored.entity_type, 'test_entity')
		self.assertEqual(stored.entity_id, entity_id)
		self.assertEqual(stored.original_filename, 'test.txt')
		self.assertEqual(stored.mime_type, 'text/plain')
		self.assertEqual(stored.file_size, len(file_data))
		self.assertEqual(stored.created_by, self.user)
	
	def test_store_file_creates_upload_log_success(self):
		"""Test store_file creates upload log on success."""
		file_data = b"test content"
		entity_id = uuid.uuid4()
		
		stored = store_file(
			entity_type='test_entity',
			entity_id=entity_id,
			original_filename='test.txt',
			file_data=file_data,
			mime_type='text/plain',
			user=self.user
		)
		
		log = FileUploadLog.objects.get(file=stored)
		self.assertEqual(log.status, 'success')
		self.assertEqual(log.error_message, '')  # No error on success
		self.assertEqual(log.file_size, len(file_data))
	
	def test_store_file_creates_upload_log_failure(self):
		"""Test store_file creates upload log on failure."""
		entity_id = uuid.uuid4()
		oversized = b"x" * (501 * 1024 * 1024)
		
		with self.assertRaises(FileSizeExceededError):
			store_file(
				entity_type='test_entity',
				entity_id=entity_id,
				original_filename='huge.bin',
				file_data=oversized,
				mime_type='application/octet-stream',
				user=self.user
			)
		
		log = FileUploadLog.objects.get(original_filename='huge.bin')
		self.assertEqual(log.status, 'failed')
		self.assertIsNotNone(log.error_message)
	
	def test_get_file_data_returns_content(self):
		"""Test get_file_data returns stored file content."""
		file_data = b"test content"
		entity_id = uuid.uuid4()
		
		stored = store_file(
			entity_type='test_entity',
			entity_id=entity_id,
			original_filename='test.txt',
			file_data=file_data,
			mime_type='text/plain',
			user=self.user
		)
		
		retrieved = get_file_data(stored.id, user=self.user)
		self.assertEqual(retrieved, file_data)
	
	def test_get_file_data_creates_download_log(self):
		"""Test get_file_data creates download log."""
		file_data = b"test content"
		entity_id = uuid.uuid4()
		
		stored = store_file(
			entity_type='test_entity',
			entity_id=entity_id,
			original_filename='test.txt',
			file_data=file_data,
			mime_type='text/plain',
			user=self.user
		)
		
		get_file_data(stored.id, user=self.user, entity_type='test_entity', entity_id=entity_id)
		
		log = FileDownloadLog.objects.get(file=stored)
		self.assertEqual(log.user, self.user)
		self.assertEqual(log.file, stored)
	
	def test_get_file_data_not_found(self):
		"""Test get_file_data raises error for missing file."""
		with self.assertRaises(FileNotFoundError):
			get_file_data(uuid.uuid4(), user=self.user)
	
	def test_delete_file_removes_metadata(self):
		"""Test delete_file removes metadata record."""
		file_data = b"test content"
		entity_id = uuid.uuid4()
		
		stored = store_file(
			entity_type='test_entity',
			entity_id=entity_id,
			original_filename='test.txt',
			file_data=file_data,
			mime_type='text/plain',
			user=self.user
		)
		
		file_id = stored.id
		delete_file(file_id, self.user)
		
		with self.assertRaises(StoredFile.DoesNotExist):
			StoredFile.objects.get(id=file_id)
	
	def test_delete_file_not_found(self):
		"""Test delete_file raises error for missing file."""
		with self.assertRaises(FileNotFoundError):
			delete_file(uuid.uuid4(), self.user)
	
	def test_get_entity_files(self):
		"""Test get_entity_files retrieves all entity files."""
		entity_id = uuid.uuid4()
		
		# Create 3 files for same entity
		for i in range(3):
			store_file(
				entity_type='test_entity',
				entity_id=entity_id,
				original_filename=f'test{i}.txt',
				file_data=b"content",
				mime_type='text/plain',
				user=self.user
			)
		
		# Create file for different entity
		store_file(
			entity_type='test_entity',
			entity_id=uuid.uuid4(),
			original_filename='other.txt',
			file_data=b"content",
			mime_type='text/plain',
			user=self.user
		)
		
		files = get_entity_files('test_entity', entity_id)
		self.assertEqual(files.count(), 3)
		self.assertTrue(all(f.entity_id == entity_id for f in files))


class TestFileDownloadLogImmutability(TestCase):
	"""Test FileDownloadLog immutability."""
	
	def setUp(self):
		self.user = User.objects.create_user(username='testuser', password='pass')
		self.entity_id = uuid.uuid4()
		self.stored_file = store_file(
			entity_type='test_entity',
			entity_id=self.entity_id,
			original_filename='test.txt',
			file_data=b"content",
			mime_type='text/plain',
			user=self.user
		)
	
	def test_download_log_cannot_be_updated(self):
		"""Test that download logs cannot be modified."""
		log = FileDownloadLog.objects.create(
			user=self.user,
			file=self.stored_file,
			entity_type='test_entity',
			entity_id=self.entity_id
		)
		
		# Try to update
		log.ip_address = '192.168.1.2'
		with self.assertRaises(ValidationError):
			log.save()
	
	def test_download_log_cannot_be_deleted(self):
		"""Test that download logs cannot be deleted."""
		log = FileDownloadLog.objects.create(
			user=self.user,
			file=self.stored_file,
			entity_type='test_entity',
			entity_id=self.entity_id
		)
		
		with self.assertRaises(ValidationError):
			log.delete()


# ============================================================================
# USER/ADMIN TESTS - Admin Interface Workflows
# ============================================================================

class TestStoredFileAdmin(TestCase):
	"""Test StoredFile admin interface."""
	
	def setUp(self):
		self.client = Client()
		self.admin_user = User.objects.create_superuser(
			username='admin', password='admin', email='admin@test.com'
		)
		self.client.login(username='admin', password='admin')
		self.entity_id = uuid.uuid4()
	
	def test_admin_list_stored_files(self):
		"""Test admin can view stored files list."""
		# Create test file
		store_file(
			entity_type='test_entity',
			entity_id=self.entity_id,
			original_filename='test.pdf',
			file_data=b"pdf content",
			mime_type='application/pdf',
			user=self.admin_user
		)
		
		response = self.client.get(reverse('admin:files_storedfile_changelist'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'test.pdf')
	
	def test_admin_view_file_metadata(self):
		"""Test admin can view file metadata details."""
		stored = store_file(
			entity_type='test_entity',
			entity_id=self.entity_id,
			original_filename='test.pdf',
			file_data=b"pdf content",
			mime_type='application/pdf',
			user=self.admin_user
		)
		
		response = self.client.get(reverse('admin:files_storedfile_change', args=[stored.id]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'test.pdf')
		self.assertContains(response, 'application/pdf')
	
	def test_admin_cannot_add_file_manually(self):
		"""Test admin cannot manually add files."""
		response = self.client.get(reverse('admin:files_storedfile_add'))
		self.assertEqual(response.status_code, 403)
	
	def test_admin_cannot_delete_file(self):
		"""Test admin cannot delete files."""
		stored = store_file(
			entity_type='test_entity',
			entity_id=self.entity_id,
			original_filename='test.pdf',
			file_data=b"pdf content",
			mime_type='application/pdf',
			user=self.admin_user
		)
		
		# Try to delete via POST
		response = self.client.post(
			reverse('admin:files_storedfile_delete', args=[stored.id]),
			{'post': 'yes'}
		)
		self.assertEqual(response.status_code, 403)
		
		# Verify still exists
		self.assertTrue(StoredFile.objects.filter(id=stored.id).exists())


class TestFileUploadLogAdmin(TestCase):
	"""Test FileUploadLog admin interface."""
	
	def setUp(self):
		self.client = Client()
		self.admin_user = User.objects.create_superuser(
			username='admin', password='admin', email='admin@test.com'
		)
		self.client.login(username='admin', password='admin')
		self.entity_id = uuid.uuid4()
	
	def test_admin_list_upload_logs(self):
		"""Test admin can view upload logs."""
		store_file(
			entity_type='test_entity',
			entity_id=self.entity_id,
			original_filename='test.pdf',
			file_data=b"pdf content",
			mime_type='application/pdf',
			user=self.admin_user
		)
		
		response = self.client.get(reverse('admin:files_fileuploadlog_changelist'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'test.pdf')
	
	def test_admin_view_upload_log_details(self):
		"""Test admin can view upload log entry."""
		stored = store_file(
			entity_type='test_entity',
			entity_id=self.entity_id,
			original_filename='test.pdf',
			file_data=b"pdf content",
			mime_type='application/pdf',
			user=self.admin_user
		)
		
		log = FileUploadLog.objects.get(file=stored)
		response = self.client.get(reverse('admin:files_fileuploadlog_change', args=[log.id]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'success')
	
	def test_admin_cannot_modify_upload_log(self):
		"""Test admin cannot modify upload logs."""
		stored = store_file(
			entity_type='test_entity',
			entity_id=self.entity_id,
			original_filename='test.pdf',
			file_data=b"pdf content",
			mime_type='application/pdf',
			user=self.admin_user
		)
		
		log = FileUploadLog.objects.get(file=stored)
		response = self.client.get(reverse('admin:files_fileuploadlog_change', args=[log.id]))
		# Should be readonly
		self.assertNotContains(response, 'id="id_status"')


class TestFileDownloadLogAdmin(TestCase):
	"""Test FileDownloadLog admin interface."""
	
	def setUp(self):
		self.client = Client()
		self.admin_user = User.objects.create_superuser(
			username='admin', password='admin', email='admin@test.com'
		)
		self.client.login(username='admin', password='admin')
		self.entity_id = uuid.uuid4()
		self.stored_file = store_file(
			entity_type='test_entity',
			entity_id=self.entity_id,
			original_filename='test.pdf',
			file_data=b"pdf content",
			mime_type='application/pdf',
			user=self.admin_user
		)
	
	def test_admin_list_download_logs(self):
		"""Test admin can view download logs."""
		get_file_data(self.stored_file.id, user=self.admin_user)
		
		response = self.client.get(reverse('admin:files_filedownloadlog_changelist'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'test.pdf')
	
	def test_admin_view_download_log_details(self):
		"""Test admin can view download log entry."""
		get_file_data(self.stored_file.id, user=self.admin_user)
		
		log = FileDownloadLog.objects.get(file=self.stored_file)
		response = self.client.get(reverse('admin:files_filedownloadlog_change', args=[log.id]))
		self.assertEqual(response.status_code, 200)
	
	def test_admin_cannot_modify_download_log(self):
		"""Test admin cannot modify download logs."""
		get_file_data(self.stored_file.id, user=self.admin_user)
		
		log = FileDownloadLog.objects.get(file=self.stored_file)
		response = self.client.get(reverse('admin:files_filedownloadlog_change', args=[log.id]))
		# Should be readonly
		self.assertNotContains(response, 'id="id_ip_address"')


class TestFileUploadLogAudit(TestCase):
	"""Test upload log audit trail."""
	
	def setUp(self):
		self.user = User.objects.create_user(username='testuser', password='pass')
		self.entity_id = uuid.uuid4()
	
	def test_successful_upload_logged(self):
		"""Test successful upload is recorded."""
		store_file(
			entity_type='test_entity',
			entity_id=self.entity_id,
			original_filename='test.pdf',
			file_data=b"content",
			mime_type='application/pdf',
			user=self.user
		)
		
		log = FileUploadLog.objects.get(original_filename='test.pdf')
		self.assertEqual(log.status, 'success')
		self.assertEqual(log.entity_type, 'test_entity')
		self.assertEqual(log.entity_id, self.entity_id)
	
	def test_failed_upload_logged(self):
		"""Test failed upload is recorded."""
		oversized = b"x" * (501 * 1024 * 1024)
		
		try:
			store_file(
				entity_type='test_entity',
				entity_id=self.entity_id,
				original_filename='huge.bin',
				file_data=oversized,
				mime_type='application/octet-stream',
				user=self.user
			)
		except FileSizeExceededError:
			pass
		
		log = FileUploadLog.objects.get(original_filename='huge.bin')
		self.assertEqual(log.status, 'failed')
		self.assertIn('hard limit', log.error_message.lower())
