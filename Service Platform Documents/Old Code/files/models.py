"""
File and Binary Storage Infrastructure Models

Implements centralized file storage per Platform Core File & Binary Storage spec.
Provides secure, traceable file management with metadata tracking.
"""

import os
import uuid
from pathlib import Path
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel


class StoredFile(BaseModel):
	"""
	Metadata record for a stored file.
	
	Tracks file information, ownership, and storage location.
	Binary file is stored separately on filesystem.
	
	Per specification:
	- One file has exactly one owning entity
	- Storage path is deterministic: {root}/{entity_type}/{entity_id}/{file_id}
	- Metadata is immutable once stored
	"""
	
	# Ownership
	entity_type = models.CharField(
		max_length=50,
		help_text="Type of entity that owns this file (e.g., 'client', 'invoice')"
	)
	
	entity_id = models.UUIDField(
		help_text="UUID of entity that owns this file"
	)
	
	# File information
	original_filename = models.CharField(
		max_length=500,
		help_text="Original filename as uploaded"
	)
	
	stored_filename = models.CharField(
		max_length=500,
		help_text="Stored filename (UUID + sanitized original)"
	)
	
	mime_type = models.CharField(
		max_length=100,
		help_text="MIME type of file (e.g., 'application/pdf')"
	)
	
	file_size = models.BigIntegerField(
		help_text="File size in bytes"
	)
	
	# Storage location
	storage_path = models.CharField(
		max_length=1000,
		help_text="Relative storage path from storage root"
	)
	
	# Optional fields
	description = models.TextField(
		blank=True,
		help_text="Optional description of file"
	)
	
	checksum = models.CharField(
		max_length=64,
		blank=True,
		help_text="SHA-256 checksum for integrity verification (Pro only)"
	)
	
	class Meta:
		indexes = [
			models.Index(fields=['entity_type']),
			models.Index(fields=['entity_type', 'entity_id']),
			models.Index(fields=['created_at']),
		]
	
	def __str__(self):
		return f"{self.original_filename} ({self.entity_type}:{self.entity_id})"


class FileUploadLog(BaseModel):
	"""
	Audit log entry for file uploads.
	
	Per specification: Track all file operations for audit trail.
	"""
	
	STATUS_CHOICES = [
		('success', 'Success'),
		('failed', 'Failed'),
		('cancelled', 'Cancelled'),
	]
	
	# Reference to file
	file = models.ForeignKey(
		StoredFile,
		on_delete=models.CASCADE,
		related_name='upload_logs',
		null=True,
		blank=True,
		help_text="The file that was uploaded (null if failed)"
	)
	
	# Upload details
	entity_type = models.CharField(
		max_length=50,
		help_text="Entity type being uploaded to"
	)
	
	entity_id = models.UUIDField(
		help_text="Entity ID being uploaded to"
	)
	
	original_filename = models.CharField(
		max_length=500,
		help_text="Filename from upload"
	)
	
	# Status
	status = models.CharField(
		max_length=20,
		choices=STATUS_CHOICES,
		default='success',
		help_text="Upload success/failure status"
	)
	
	error_message = models.TextField(
		blank=True,
		help_text="Error message if upload failed"
	)
	
	file_size = models.BigIntegerField(
		null=True,
		blank=True,
		help_text="File size in bytes"
	)
	
	class Meta:
		indexes = [
			models.Index(fields=['entity_type', 'entity_id']),
			models.Index(fields=['created_at']),
			models.Index(fields=['status']),
		]
	
	def __str__(self):
		return f"Upload: {self.original_filename} ({self.status})"


class FileDownloadLog(models.Model):
	"""
	Immutable audit log for file downloads.
	
	Per specification: Track all file access for security auditing.
	"""
	
	# Timestamp (immutable)
	timestamp = models.DateTimeField(
		auto_now_add=True,
		editable=False,
		help_text="When file was downloaded"
	)
	
	# User
	user = models.ForeignKey(
		'auth.User',
		on_delete=models.PROTECT,
		related_name='file_downloads',
		help_text="User who downloaded the file"
	)
	
	# File reference
	file = models.ForeignKey(
		StoredFile,
		on_delete=models.PROTECT,
		related_name='download_logs',
		help_text="File that was downloaded"
	)
	
	# Access context
	entity_type = models.CharField(
		max_length=50,
		help_text="Entity type the download was for"
	)
	
	entity_id = models.UUIDField(
		help_text="Entity ID the download was for"
	)
	
	# IP (optional)
	ip_address = models.GenericIPAddressField(
		null=True,
		blank=True,
		help_text="Client IP address (optional)"
	)
	
	class Meta:
		# Immutable
		permissions = []
		indexes = [
			models.Index(fields=['file']),
			models.Index(fields=['user']),
			models.Index(fields=['timestamp']),
		]
	
	def delete(self, *args, **kwargs):
		"""Audit logs cannot be deleted."""
		raise ValidationError("Download logs are immutable and cannot be deleted")
	
	def save(self, *args, **kwargs):
		"""Audit logs cannot be modified after creation."""
		if self.pk is not None and 'force_insert' not in kwargs:
			try:
				FileDownloadLog.objects.get(pk=self.pk)
				raise ValidationError("Download logs are immutable and cannot be modified")
			except FileDownloadLog.DoesNotExist:
				pass
		super().save(*args, **kwargs)
	
	def __str__(self):
		return f"{self.user} downloaded {self.file.original_filename}"
