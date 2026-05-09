"""Admin registrations for Identity components."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Role, UserProfile, UserRole

User = get_user_model()


# Inline UserProfile for User Admin
class UserProfileInline(admin.StackedInline):
	model = UserProfile
	can_delete = False
	verbose_name_plural = "Profile"
	fk_name = "user"
	
	fieldsets = (
		("Display & Preferences", {
			"fields": ("display_name", "time_zone")
		}),
		("Personal Information", {
			"fields": ("birthday", "gender", "phone_number")
		}),
		("Employment Information", {
			"fields": ("position", "date_left")
		}),
		("Notes", {
			"fields": ("notes",)
		}),
		("Status", {
			"fields": ("is_active",)
		}),
	)


# Custom User Admin with Profile Inline
class UserAdmin(BaseUserAdmin):
	inlines = (UserProfileInline,)
	
	list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active", "date_joined")
	list_filter = ("is_staff", "is_superuser", "is_active", "groups")
	search_fields = ("username", "first_name", "last_name", "email")
	
	fieldsets = (
		(None, {
			"fields": ("username", "password")
		}),
		("Personal Info", {
			"fields": ("first_name", "last_name", "email")
		}),
		("Permissions", {
			"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
		}),
		("Important Dates", {
			"fields": ("last_login", "date_joined"),
		}),
	)
	
	readonly_fields = ("last_login", "date_joined")


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)



@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
	list_display = ("name", "key", "is_system", "is_active")
	list_filter = ("is_system", "is_active")
	search_fields = ("name", "key", "description")
	readonly_fields = ("id", "created_at", "created_by", "updated_at", "updated_by")

	def save_model(self, request, obj, form, change):
		if not change:  # Creating new object
			obj.created_by = request.user
		obj.updated_by = request.user
		super().save_model(request, obj, form, change)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
	list_display = ("user", "role", "is_active")
	list_filter = ("role", "is_active")
	search_fields = ("user__username", "role__name", "role__key")
	readonly_fields = ("id", "created_at", "created_by", "updated_at", "updated_by")

	def save_model(self, request, obj, form, change):
		if not change:  # Creating new object
			obj.created_by = request.user
		obj.updated_by = request.user
		super().save_model(request, obj, form, change)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "display_name", "position", "phone_number", "birthday", "date_left", "is_active")
	list_filter = ("gender", "date_left", "is_active")
	search_fields = ("user__username", "user__first_name", "user__last_name", "display_name", "position", "phone_number")
	readonly_fields = ("id", "created_at", "created_by", "updated_at", "updated_by")
	
	fieldsets = (
		("User Link", {
			"fields": ("user",)
		}),
		("Display & Preferences", {
			"fields": ("display_name", "time_zone")
		}),
		("Personal Information", {
			"fields": ("birthday", "gender", "phone_number")
		}),
		("Employment Information", {
			"fields": ("position", "date_left")
		}),
		("Notes", {
			"fields": ("notes",)
		}),
		("Status", {
			"fields": ("is_active",)
		}),
		("Metadata", {
			"fields": ("id", "created_at", "created_by", "updated_at", "updated_by"),
			"classes": ("collapse",)
		}),
	)

	def save_model(self, request, obj, form, change):
		if not change:  # Creating new object
			obj.created_by = request.user
		obj.updated_by = request.user
		super().save_model(request, obj, form, change)
