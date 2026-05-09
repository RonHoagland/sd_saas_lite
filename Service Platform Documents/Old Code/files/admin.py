"""
File Storage Admin Interface.

Provides Django admin interfaces for managing stored files and audit logs.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q
from .models import StoredFile, FileUploadLog, FileDownloadLog


@admin.register(StoredFile)
class StoredFileAdmin(admin.ModelAdmin):
	"""
	Admin interface for stored file metadata.
	
	Features:
	- View all file metadata
	- Filter by entity, date, MIME type
	- Download file info
	- Read-only to prevent untracked modifications
	"""
	
	list_display = (
		'original_filename', 'file_size_display', 'mime_type', 
		'entity_info', 'created_at', 'created_by', 'status'
	)
	list_filter = ('mime_type', 'entity_type', 'created_at', 'is_active')
	search_fields = ('original_filename', 'stored_filename', 'entity_id')
	readonly_fields = (
		'id', 'entity_type', 'entity_id', 'original_filename', 
		'stored_filename', 'mime_type', 'file_size', 'storage_path',
		'checksum', 'created_at', 'created_by', 'updated_at', 'updated_by'
	)
	fieldsets = (
		('File Identity', {
			'fields': ('id', 'original_filename', 'stored_filename', 'mime_type')
		}),
		('Entity Association', {
			'fields': ('entity_type', 'entity_id')
		}),
		('Storage', {
			'fields': ('file_size', 'storage_path', 'checksum')
		}),
		('Metadata', {
			'fields': ('description',)
		}),
		('Audit Trail', {
			'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'is_active'),
			'classes': ('collapse',)
		}),
	)
	
	# Prevent accidental modifications
	def has_add_permission(self, request):
		# Files added via store_file utility, not manual admin entry
		return False
	
	def has_delete_permission(self, request, obj=None):
		# Use delete_file utility for proper cleanup
		return False
	
	def has_change_permission(self, request, obj=None):
		# Files should not be modified
		return False
	
	def file_size_display(self, obj):
		"""Display file size in human-readable format."""
		size = obj.file_size
		for unit in ['B', 'KB', 'MB', 'GB']:
			if size < 1024:
				return f"{size:.1f} {unit}"
			size /= 1024
		return f"{size:.1f} TB"
	file_size_display.short_description = "File Size"
	
	def entity_info(self, obj):
		"""Display entity context."""
		return f"{obj.entity_type} ({obj.entity_id})"
	entity_info.short_description = "Entity"
	
	def status(self, obj):
		"""Display file status indicator."""
		if obj.is_active:
			return format_html('<span style="color: green;">●</span> Active')
		else:
			return format_html('<span style="color: gray;">●</span> Inactive')
	status.short_description = "Status"


@admin.register(FileUploadLog)
class FileUploadLogAdmin(admin.ModelAdmin):
	"""
	Admin interface for file upload audit trail.
	
	Features:
	- View all upload attempts
	- Filter by status, entity, date
	- See success/failure details
	- Immutable read-only log
	"""
	
	list_display = (
		'original_filename', 'status_display', 'file_size_display', 
		'entity_info', 'created_at', 'created_by'
	)
	list_filter = ('status', 'entity_type', 'created_at')
	search_fields = ('original_filename', 'entity_id', 'error_message')
	readonly_fields = (
		'id', 'file', 'entity_type', 'entity_id', 'original_filename',
		'status', 'error_message', 'file_size',
		'created_at', 'created_by', 'updated_at', 'updated_by'
	)
	fieldsets = (
		('Upload Details', {
			'fields': ('file', 'original_filename', 'entity_type', 'entity_id')
		}),
		('Result', {
			'fields': ('status', 'error_message', 'file_size')
		}),
		('Audit Trail', {
			'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
			'classes': ('collapse',)
		}),
	)
	
	# Prevent modifications to audit log
	def has_add_permission(self, request):
		return False
	
	def has_delete_permission(self, request, obj=None):
		return False
	
	def has_change_permission(self, request, obj=None):
		return False
	
	def status_display(self, obj):
		"""Display status with color coding."""
		color = 'green' if obj.status == 'success' else 'red'
		icon = '✓' if obj.status == 'success' else '✗'
		return format_html(
			'<span style="color: {};">{} {}</span>',
			color, icon, obj.status.title()
		)
	status_display.short_description = "Status"
	
	def file_size_display(self, obj):
		"""Display file size in human-readable format."""
		if not obj.file_size:
			return '—'
		size = obj.file_size
		for unit in ['B', 'KB', 'MB', 'GB']:
			if size < 1024:
				return f"{size:.1f} {unit}"
			size /= 1024
		return f"{size:.1f} TB"
	file_size_display.short_description = "File Size"
	
	def entity_info(self, obj):
		"""Display entity context."""
		return f"{obj.entity_type} ({obj.entity_id})"
	entity_info.short_description = "Entity"


@admin.register(FileDownloadLog)
class FileDownloadLogAdmin(admin.ModelAdmin):
	"""
	Admin interface for file download audit log.
	
	Features:
	- View all download access
	- Filter by user, entity, date
	- Track download patterns
	- Immutable read-only log
	"""
	
	list_display = (
		'file_display', 'user', 'entity_info', 
		'timestamp', 'ip_address'
	)
	list_filter = ('user', 'entity_type', 'timestamp')
	search_fields = ('user__username', 'entity_id', 'file__original_filename', 'ip_address')
	readonly_fields = (
		'id', 'timestamp', 'user', 'file', 'entity_type', 'entity_id', 'ip_address'
	)
	fieldsets = (
		('Download Event', {
			'fields': ('timestamp', 'user', 'file')
		}),
		('Entity Context', {
			'fields': ('entity_type', 'entity_id')
		}),
		('Access Details', {
			'fields': ('ip_address',)
		}),
	)
	
	# Prevent modifications to audit log
	def has_add_permission(self, request):
		return False
	
	def has_delete_permission(self, request, obj=None):
		return False
	
	def has_change_permission(self, request, obj=None):
		return False
	
	def file_display(self, obj):
		"""Display file with link to metadata."""
		if obj.file:
			return obj.file.original_filename
		return '—'
	file_display.short_description = "File"
	
	def entity_info(self, obj):
		"""Display entity context."""
		return f"{obj.entity_type} ({obj.entity_id})"
	entity_info.short_description = "Entity"
