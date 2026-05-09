from django.contrib import admin
from django.utils.html import format_html

from .models import AppSetting, NavItem


@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
	list_display = ("key", "value", "created_at", "created_by", "updated_at", "updated_by")
	search_fields = ("key", "value")
	list_filter = ("is_active",)
	readonly_fields = ("created_at", "created_by", "updated_at", "updated_by")

	def save_model(self, request, obj, form, change):
		if not change:
			obj.created_by = request.user
		obj.updated_by = request.user
		super().save_model(request, obj, form, change)


@admin.register(NavItem)
class NavItemAdmin(admin.ModelAdmin):
	list_display = ("label", "section", "order", "parent_label", "url_name", "status")
	list_filter = ("section", "is_active")
	search_fields = ("label", "key", "url_name")
	readonly_fields = ("created_at", "created_by", "updated_at", "updated_by")
	filter_horizontal = ("required_roles",)

	fieldsets = (
		("Identity", {"fields": ("key", "label", "url_name", "icon")}),
		("Grouping", {"fields": ("section", "order", "parent")}),
		("Visibility", {"fields": ("required_roles", "is_active")}),
		("Audit", {"fields": ("created_at", "created_by", "updated_at", "updated_by"), "classes": ("collapse",)}),
	)

	def save_model(self, request, obj, form, change):
		if not change:
			obj.created_by = request.user
		obj.updated_by = request.user
		super().save_model(request, obj, form, change)

	def parent_label(self, obj):
		return obj.parent.label if obj.parent else "—"
	parent_label.short_description = "Parent"

	def status(self, obj):
		if obj.is_active:
			return format_html('<span style="color: green;">●</span> Active')
		return format_html('<span style="color: gray;">●</span> Inactive')
	status.short_description = "Status"

