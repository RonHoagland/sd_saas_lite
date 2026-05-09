"""Admin registrations for Lifecycle Framework."""

from django.contrib import admin
from django.utils.html import format_html

from .models import LifecycleStateDef, LifecycleTransitionRule, LifecycleTransitionAudit


@admin.register(LifecycleStateDef)
class LifecycleStateDefAdmin(admin.ModelAdmin):
	list_display = ("entity_type", "state_label", "state_name", "colored_state_type", "is_default", "is_active")
	list_filter = ("entity_type", "state_type", "is_default", "is_active")
	search_fields = ("entity_type", "state_name", "state_label")
	readonly_fields = ("id", "created_at", "created_by", "updated_at", "updated_by")
	fieldsets = (
		("Entity & State", {
			"fields": ("entity_type", "state_name", "state_label")
		}),
		("Classification", {
			"fields": ("state_type", "is_default")
		}),
		("Documentation", {
			"fields": ("description",)
		}),
		("Metadata", {
			"fields": ("is_active", "id", "created_at", "created_by", "updated_at", "updated_by"),
			"classes": ("collapse",)
		}),
	)
	
	def colored_state_type(self, obj):
		colors = {
			'normal': '#28a745',
			'locked': '#fd7e14',
			'final': '#dc3545',
		}
		return format_html(
			'<span style="background-color: {}; color: white; padding: 3px 6px; border-radius: 3px;">{}</span>',
			colors.get(obj.state_type, '#999'),
			obj.get_state_type_display()
		)
	colored_state_type.short_description = "State Type"
	
	def save_model(self, request, obj, form, change):
		if not change:
			obj.created_by = request.user
		obj.updated_by = request.user
		super().save_model(request, obj, form, change)


@admin.register(LifecycleTransitionRule)
class LifecycleTransitionRuleAdmin(admin.ModelAdmin):
	list_display = ("entity_type", "from_state", "arrow", "to_state", "required_permission_display", "requires_reason", "is_active")
	list_filter = ("entity_type", "requires_reason", "is_active")
	search_fields = ("entity_type", "from_state", "to_state", "required_permission")
	readonly_fields = ("id", "created_at", "created_by", "updated_at", "updated_by")
	fieldsets = (
		("Transition Definition", {
			"fields": ("entity_type", "from_state", "to_state")
		}),
		("Requirements", {
			"fields": ("required_permission", "requires_reason")
		}),
		("Documentation", {
			"fields": ("description",)
		}),
		("Metadata", {
			"fields": ("is_active", "id", "created_at", "created_by", "updated_at", "updated_by"),
			"classes": ("collapse",)
		}),
	)
	
	def arrow(self, obj):
		return "→"
	arrow.short_description = ""
	
	def required_permission_display(self, obj):
		if obj.required_permission:
			return format_html(
				'<span style="background-color: #6c757d; color: white; padding: 3px 6px; border-radius: 3px;">{}</span>',
				obj.required_permission
			)
		return "—"
	required_permission_display.short_description = "Required Permission"
	
	def save_model(self, request, obj, form, change):
		if not change:
			obj.created_by = request.user
		obj.updated_by = request.user
		super().save_model(request, obj, form, change)


@admin.register(LifecycleTransitionAudit)
class LifecycleTransitionAuditAdmin(admin.ModelAdmin):
	list_display = ("timestamp", "user", "entity_type_display", "state_transition", "is_override_badge")
	list_filter = ("entity_type", "is_override", "timestamp")
	search_fields = ("entity_type", "entity_id", "user__username")
	readonly_fields = ("timestamp", "user", "entity_type", "entity_id", "from_state", "to_state", "reason", "is_override")
	
	# Make completely read-only
	def has_add_permission(self, request):
		return False
	
	def has_delete_permission(self, request, obj=None):
		return False
	
	def has_change_permission(self, request, obj=None):
		return False
	
	def state_transition(self, obj):
		return f"{obj.from_state} → {obj.to_state}"
	state_transition.short_description = "Transition"
	
	def entity_type_display(self, obj):
		return f"{obj.entity_type}:{obj.entity_id}"
	entity_type_display.short_description = "Entity"
	
	def is_override_badge(self, obj):
		if obj.is_override:
			return format_html(
				'<span style="background-color: #dc3545; color: white; padding: 3px 6px; border-radius: 3px;">OVERRIDE</span>'
			)
		return "—"
	is_override_badge.short_description = "Type"
