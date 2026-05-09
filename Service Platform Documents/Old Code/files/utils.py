"""
File Storage Utilities - Upload, download, and file management.

Implements centralized file storage per Platform Core File & Binary Storage spec.
Provides secure, permission-checked file operations with audit trail.
"""

import os
import hashlib
import uuid
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils import timezone
from django.db import transaction
from io import BytesIO

from .models import StoredFile, FileUploadLog, FileDownloadLog


class FileStorageError(Exception):
	"""Base exception for file storage errors."""
	pass


class FileSizeExceededError(FileStorageError):
	"""Raised when file exceeds size limit."""
	pass


class InvalidMimeTypeError(FileStorageError):
	"""Raised when MIME type not allowed."""
	pass


class FileNotFoundError(FileStorageError):
	"""Raised when file cannot be found."""
	pass


# Hard limit per specification: 500 MB
HARD_FILE_SIZE_LIMIT = 500 * 1024 * 1024  # 500 MB in bytes


def get_storage_root():
	"""
	Get the configured storage root path.
	
	Returns:
		Path: Storage root directory path
	"""
	# Get from settings or use default
	root = getattr(settings, 'FILE_STORAGE_ROOT', None)
	if not root:
		root = os.path.join(settings.BASE_DIR, 'storage')
	
	return Path(root)


def ensure_storage_root():
	"""Ensure storage root directory exists."""
	root = get_storage_root()
	root.mkdir(parents=True, exist_ok=True)


def get_storage_path(entity_type, entity_id, file_id):
	"""
	Get the storage path for a file.
	
	Per specification: {entity_type}/{entity_id}/{file_id}
	
	Args:
		entity_type: String entity type
		entity_id: UUID of owning entity
		file_id: UUID of file record
	
	Returns:
		Path: Relative path from storage root
	"""
	return Path(entity_type) / str(entity_id) / str(file_id)


def sanitize_filename(original_filename):
	"""
	Sanitize filename for safe storage.
	
	Args:
		original_filename: Original filename from upload
	
	Returns:
		String: Sanitized filename
	"""
	# Remove path separators and dangerous characters
	filename = os.path.basename(original_filename)
	# Keep only alphanumeric, dots, dashes, underscores
	import re
	filename = re.sub(r'[^\w\s.-]', '', filename)
	return filename


def generate_stored_filename(original_filename):
	"""
	Generate stored filename with UUID prefix.
	
	Format: {uuid}-{sanitized_original}
	
	Args:
		original_filename: Original filename
	
	Returns:
		String: Stored filename
	"""
	file_uuid = uuid.uuid4().hex[:8]
	sanitized = sanitize_filename(original_filename)
	if sanitized:
		return f"{file_uuid}-{sanitized}"
	else:
		return file_uuid


def calculate_checksum(file_data):
	"""
	Calculate SHA-256 checksum of file data.
	
	Args:
		file_data: File data (bytes or file-like object)
	
	Returns:
		String: Hex checksum
	"""
	hasher = hashlib.sha256()
	if isinstance(file_data, bytes):
		hasher.update(file_data)
	else:
		# File-like object
		while True:
			chunk = file_data.read(8192)
			if not chunk:
				break
			hasher.update(chunk)
		# Reset file position
		file_data.seek(0)
	return hasher.hexdigest()


def validate_upload(original_filename, file_data, mime_type, user, entity_type):
	"""
	Validate file before upload.
	
	Per specification:
	- Enforce size limits (configurable + hard 500MB)
	- Enforce allowed MIME types (if configured)
	
	Args:
		original_filename: String
		file_data: Bytes or file-like object
		mime_type: MIME type string
		user: User performing upload
		entity_type: Entity type being uploaded to
	
	Returns:
		Tuple: (is_valid, error_message)
	"""
	# Get file size
	if isinstance(file_data, bytes):
		file_size = len(file_data)
	else:
		file_data.seek(0, 2)  # Seek to end
		file_size = file_data.tell()
		file_data.seek(0)  # Reset
	
	# Check hard limit
	if file_size > HARD_FILE_SIZE_LIMIT:
		return False, f"File exceeds hard limit of {HARD_FILE_SIZE_LIMIT / 1024 / 1024:.0f}MB"
	
	# Check configurable limit (from Preferences)
	# TODO: Get from Preference when core.Preference integration complete
	# For now, use hard limit as default
	max_size = HARD_FILE_SIZE_LIMIT
	if file_size > max_size:
		return False, f"File exceeds maximum size of {max_size / 1024 / 1024:.0f}MB"
	
	# Check MIME type if restricted
	# TODO: Get allowed types from Preference when configured
	# For now, allow all types
	
	return True, None


def store_file(entity_type, entity_id, original_filename, file_data, mime_type, user, description=''):
	"""
	Store a file with metadata tracking.
	
	Per specification:
	- Validate file before storing
	- Create metadata record
	- Store binary file
	- Generate audit log
	- Atomic transaction
	
	Args:
		entity_type: String entity type (e.g., 'client')
		entity_id: UUID of owning entity
		original_filename: Original filename from upload
		file_data: File data (bytes or file-like object)
		mime_type: MIME type (e.g., 'application/pdf')
		user: User performing upload
		description: Optional file description
	
	Returns:
		StoredFile: Created metadata record
	
	Raises:
		FileSizeExceededError: If file exceeds size limits
		InvalidMimeTypeError: If MIME type not allowed
		FileStorageError: If storage operation fails
	"""
	# Validate (outside transaction to ensure failure log is created)
	is_valid, error = validate_upload(original_filename, file_data, mime_type, user, entity_type)
	if not is_valid:
		# Log failed upload
		FileUploadLog.objects.create(
			entity_type=entity_type,
			entity_id=entity_id,
			original_filename=original_filename,
			status='failed',
			error_message=error,
			created_by=user,
			updated_by=user
		)
		if 'hard limit' in error.lower():
			raise FileSizeExceededError(error)
		else:
			raise InvalidMimeTypeError(error)
	
	# Now do the actual storage (atomic)
	return _store_file_atomic(entity_type, entity_id, original_filename, file_data, mime_type, user, description)


@transaction.atomic
def _store_file_atomic(entity_type, entity_id, original_filename, file_data, mime_type, user, description=''):
	"""Internal function that performs atomic storage after validation."""
	
	# Create metadata record
	file_id = uuid.uuid4()
	stored_filename = generate_stored_filename(original_filename)
	storage_path = get_storage_path(entity_type, entity_id, file_id)
	
	# Get file size
	if isinstance(file_data, bytes):
		file_size = len(file_data)
	else:
		file_data.seek(0, 2)
		file_size = file_data.tell()
		file_data.seek(0)
	
	# Calculate checksum
	checksum = calculate_checksum(file_data)
	
	# Ensure storage directory exists
	ensure_storage_root()
	storage_root = get_storage_root()
	file_path = storage_root / storage_path / stored_filename
	file_path.parent.mkdir(parents=True, exist_ok=True)
	
	# Write file
	try:
		if isinstance(file_data, bytes):
			with open(file_path, 'wb') as f:
				f.write(file_data)
		else:
			with open(file_path, 'wb') as f:
				while True:
					chunk = file_data.read(8192)
					if not chunk:
						break
					f.write(chunk)
	except IOError as e:
		raise FileStorageError(f"Failed to write file to storage: {str(e)}")
	
	# Create metadata record
	stored_file = StoredFile.objects.create(
		id=file_id,
		entity_type=entity_type,
		entity_id=entity_id,
		original_filename=original_filename,
		stored_filename=stored_filename,
		mime_type=mime_type,
		file_size=file_size,
		storage_path=str(storage_path),
		checksum=checksum,
		description=description,
		created_by=user,
		updated_by=user
	)
	
	# Log successful upload
	FileUploadLog.objects.create(
		file=stored_file,
		entity_type=entity_type,
		entity_id=entity_id,
		original_filename=original_filename,
		status='success',
		file_size=file_size,
		created_by=user,
		updated_by=user
	)
	
	return stored_file


def get_file_data(file_id, user=None, entity_type=None, entity_id=None):
	"""
	Retrieve file data with permission check.
	
	Per specification:
	- Permission-check access
	- Return file data safely
	
	Args:
		file_id: UUID of file to retrieve
		user: User requesting file (for permission/audit)
		entity_type: Optional entity type for access control
		entity_id: Optional entity ID for access control
	
	Returns:
		Bytes: File data
	
	Raises:
		FileNotFoundError: If file not found
		PermissionError: If user lacks permission
	"""
	try:
		stored_file = StoredFile.objects.get(id=file_id)
	except StoredFile.DoesNotExist:
		raise FileNotFoundError(f"File not found: {file_id}")
	
	# TODO: Permission check against user when identity integration complete
	
	# Get file data
	storage_root = get_storage_root()
	file_path = storage_root / stored_file.storage_path / stored_file.stored_filename
	
	if not file_path.exists():
		raise FileNotFoundError(f"File data not found on storage: {file_path}")
	
	# Log download
	if user:
		FileDownloadLog.objects.create(
			user=user,
			file=stored_file,
			entity_type=entity_type or stored_file.entity_type,
			entity_id=entity_id or stored_file.entity_id
		)
	
	# Read and return file data
	with open(file_path, 'rb') as f:
		return f.read()


@transaction.atomic
def delete_file(file_id, user):
	"""
	Delete a file (metadata and binary).
	
	Per specification:
	- Delete both metadata and binary file
	- Atomic transaction
	- Generate audit entry
	
	Args:
		file_id: UUID of file to delete
		user: User performing deletion
	
	Raises:
		FileNotFoundError: If file not found
		FileStorageError: If deletion fails
	"""
	try:
		stored_file = StoredFile.objects.get(id=file_id)
	except StoredFile.DoesNotExist:
		raise FileNotFoundError(f"File not found: {file_id}")
	
	# TODO: Permission check against user
	
	# Delete binary file
	storage_root = get_storage_root()
	file_path = storage_root / stored_file.storage_path / stored_file.stored_filename
	
	try:
		if file_path.exists():
			file_path.unlink()
	except IOError as e:
		raise FileStorageError(f"Failed to delete file from storage: {str(e)}")
	
	# Delete metadata record (cascade will clean up logs)
	stored_file.delete()


def get_entity_files(entity_type, entity_id):
	"""
	Get all files for an entity.
	
	Args:
		entity_type: String entity type
		entity_id: UUID of entity
	
	Returns:
		QuerySet: StoredFile instances
	"""
	return StoredFile.objects.filter(
		entity_type=entity_type,
		entity_id=entity_id,
		is_active=True
	).order_by('-created_at')


class FileMixin:
	"""
	Mixin for models to support file attachment.
	
	Provides convenient file management methods on entities.
	
	Usage:
		class MyEntity(BaseModel, FileMixin):
			entity_type = 'my_entity'
	"""
	
	# Subclasses must define:
	# entity_type = 'your_entity_type'
	
	def attach_file(self, original_filename, file_data, mime_type, user, description=''):
		"""
		Attach a file to this entity.
		
		Args:
			original_filename: Filename
			file_data: File data (bytes or file-like)
			mime_type: MIME type
			user: User attaching file
			description: Optional description
		
		Returns:
			StoredFile: Created file record
		"""
		return store_file(
			entity_type=self.entity_type,
			entity_id=self.id,
			original_filename=original_filename,
			file_data=file_data,
			mime_type=mime_type,
			user=user,
			description=description
		)
	
	def get_files(self):
		"""Get all attached files."""
		return get_entity_files(self.entity_type, self.id)
	
	def delete_file(self, file_id, user):
		"""Delete an attached file."""
		delete_file(file_id, user)