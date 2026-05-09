"""Admin registrations for Numbering Service."""

from django.contrib import admin
from django.utils.html import format_html

from .models import NumberingRule, NumberSequence, AssignedNumber


@admin.register(NumberingRule)
class NumberingRuleAdmin(admin.ModelAdmin):
	list_display = ("entity_type", "is_enabled_badge", "format_example", "reset_behavior", "is_active")
	list_filter = ("is_enabled", "reset_behavior", "include_year", "include_month", "is_active")
	search_fields = ("entity_type", "prefix", "description")
	readonly_fields = ("id", "created_at", "created_by", "updated_at", "updated_by", "format_preview")
	fieldsets = (
		("Entity", {
			"fields": ("entity_type", "is_enabled")
		}),
		("Format Components", {
			"fields": ("prefix", "include_year", "include_month", "sequence_length", "delimiter")
		}),
		("Sequence Reset", {
			"fields": ("reset_behavior",)
		}),
		("Documentation", {
			"fields": ("description", "format_preview")
		}),
		("Metadata", {
			"fields": ("is_active", "id", "created_at", "created_by", "updated_at", "updated_by"),
			"classes": ("collapse",)
		}),
	)
	
	def is_enabled_badge(self, obj):
		if obj.is_enabled:
			return format_html(
				'<span style="background-color: #28a745; color: white; padding: 3px 6px; border-radius: 3px;">ENABLED</span>'
			)
		return format_html(
			'<span style="background-color: #6c757d; color: white; padding: 3px 6px; border-radius: 3px;">DISABLED</span>'
		)
	is_enabled_badge.short_description = "Status"
	
	def format_example(self, obj):
		"""Display example of number format."""
		components = []
		if obj.prefix:
			components.append(obj.prefix)
		if obj.include_year:
			components.append("2026")
		if obj.include_month:
			components.append("01")
		components.append("0" * obj.sequence_length)
		return obj.delimiter.join(components)
	format_example.short_description = "Format"
	
	def format_preview(self, obj):
		"""Show preview of format."""
		return format_html(
			"<strong>Example:</strong> {}<br/><small>Components: {}</small>",
			self.format_example(obj),
			", ".join([
				"prefix" if obj.prefix else None,
				"year" if obj.include_year else None,
				"month" if obj.include_month else None,
				"sequence",
			] + [None] * (4 - sum([bool(obj.prefix), obj.include_year, obj.include_month])))
		)
	format_preview.short_description = "Format Preview"
	
	def save_model(self, request, obj, form, change):
		if not change:
			obj.created_by = request.user
		obj.updated_by = request.user
		super().save_model(request, obj, form, change)


@admin.register(NumberSequence)
class NumberSequenceAdmin(admin.ModelAdmin):
	list_display = ("rule", "current_value", "last_reset_date", "reset_behavior")
	list_filter = ("rule__reset_behavior", "last_reset_date")
	search_fields = ("rule__entity_type",)
	readonly_fields = ("rule", "current_value", "last_reset_date")
	
	# Make read-only (internal use only)
	def has_add_permission(self, request):
		return False
	
	def has_delete_permission(self, request, obj=None):
		return False
	
	def has_change_permission(self, request, obj=None):
		return False
	
	def reset_behavior(self, obj):
		return obj.rule.get_reset_behavior_display()
	reset_behavior.short_description = "Reset Behavior"


@admin.register(AssignedNumber)
class AssignedNumberAdmin(admin.ModelAdmin):
	list_display = ("number", "entity_type_display", "assigned_at", "assigned_by")
	list_filter = ("entity_type", "assigned_at", "rule")
	search_fields = ("entity_type", "entity_id", "number")
	readonly_fields = ("rule", "entity_type", "entity_id", "number", "assigned_at", "assigned_by", "id", "created_at", "created_by", "updated_at", "updated_by")
	fieldsets = (
		("Assignment", {
			"fields": ("rule", "entity_type", "entity_id", "number")
		}),
		("Details", {
			"fields": ("assigned_at", "assigned_by")
		}),
		("Metadata", {
			"fields": ("id", "created_at", "created_by", "updated_at", "updated_by"),
			"classes": ("collapse",)
		}),
	)
	
	# Make immutable
	def has_add_permission(self, request):
		return False
	
	def has_delete_permission(self, request, obj=None):
		return False
	
	def has_change_permission(self, request, obj=None):
		return False
	
	def entity_type_display(self, obj):
		return f"{obj.entity_type}:{obj.entity_id}"
	entity_type_display.short_description = "Entity"
