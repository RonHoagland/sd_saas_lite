"""
Identity models: Roles, User Roles, and User Profile.

Implements Lite role set (Owner/Admin, Worker/User, Read-Only) and provides
infrastructure for permission checks across the platform.
"""

from django.conf import settings
from django.db import models

from core.models import BaseModel
from django.db.models.signals import pre_delete, post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError



class Role(BaseModel):
	"""System role definition (Lite: Owner, Worker, Read-Only)."""

	key = models.CharField(
		max_length=100,
		unique=True,
		help_text="Machine-friendly role key (e.g., owner_admin, worker_user, read_only)",
	)

	name = models.CharField(
		max_length=200,
		help_text="Human-friendly role name",
	)

	description = models.TextField(
		blank=True,
		help_text="Purpose and scope of this role",
	)

	is_system = models.BooleanField(
		default=True,
		help_text="True for system-defined roles (Owner, Worker, Read-Only)",
	)

	class Meta:
		ordering = ["name"]
		indexes = [
			models.Index(fields=["key"]),
			models.Index(fields=["is_active"]),
		]

	def __str__(self) -> str:  # pragma: no cover - trivial
		return f"{self.name} ({self.key})"


class UserRole(BaseModel):
	"""Assignment of a role to a user."""

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="user_roles",
		help_text="User receiving the role",
	)

	role = models.ForeignKey(
		Role,
		on_delete=models.PROTECT,
		related_name="assigned_users",
		help_text="Assigned role",
	)

	class Meta:
		unique_together = [("user", "role")]
		indexes = [
			models.Index(fields=["user", "role"]),
		]
		ordering = ["user__username"]

	def __str__(self) -> str:  # pragma: no cover - trivial
		return f"{self.user} → {self.role}"


class UserProfile(BaseModel):
	"""Additional profile data for users (non-auth fields)."""

	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="profile",
		help_text="User owning this profile",
	)

	display_name = models.CharField(
		max_length=200,
		blank=True,
		help_text="Preferred display name",
	)

	time_zone = models.CharField(
		max_length=64,
		blank=True,
		help_text="IANA time zone name (e.g., UTC, America/New_York)",
	)

	# Personal Information
	birthday = models.DateField(
		null=True,
		blank=True,
		help_text="Date of birth",
	)

	gender = models.CharField(
		max_length=20,
		choices=[
			("male", "Male"),
			("female", "Female"),
			("other", "Other"),
		],
		blank=True,
		help_text="Gender",
	)

	phone_number = models.CharField(
		max_length=20,
		blank=True,
		help_text="Primary phone number",
	)

	# Employment Information
	position = models.CharField(
		max_length=200,
		blank=True,
		help_text="Job title or position",
	)

	date_left = models.DateField(
		null=True,
		blank=True,
		help_text="Date employee left the organization (if applicable)",
	)

	# Additional Notes
	notes = models.TextField(
		blank=True,
		help_text="Administrative notes about this user",
	)

	class Meta:
		ordering = ["user__username"]
		indexes = [
			models.Index(fields=["user"]),
			models.Index(fields=["position"]),
			models.Index(fields=["date_left"]),
		]

	def __str__(self) -> str:  # pragma: no cover - trivial
		return self.display_name or self.user.get_username()


@receiver(pre_delete, sender=UserRole)
def prevent_last_admin_role_removal(sender, instance, **kwargs):
    """
    Prevent removing the 'administrator' role if it's the last one assigned system-wide.
    """
    if instance.role.key == 'administrator':
        # Count TOTAL assignments of 'administrator' for ACTIVE users
        # If we allow deleting an INACTIVE admin's role, that's fine.
        # But if we delete an ACTIVE admin's role, we must ensure 1 remains.
        
        # Check if the user owning this role IS active used to matter?
        # If user is inactive, they don't count towards the "Safe System State" anyway.
        # But to be safe: We require at least one ACTIVE administrator.
        
        active_admin_count = UserRole.objects.filter(role__key='administrator', user__is_active=True).count()
        
        # If instance.user is active, decreasing count matters.
        if instance.user.is_active:
             if active_admin_count <= 1:
                raise ValidationError(
                    "Cannot remove the last active Administrator role assignment. "
                    "The system requires at least one active Administrator."
                )

@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def prevent_last_admin_deactivation(sender, instance, **kwargs):
    """
    Prevent deactivating the last active administrator.
    """
    if instance.pk and not instance.is_active: 
        # User is being updated and set to inactive.
        # Check if they were active before? Django model instance has new value.
        # We need to check DB state or just trust the check?
        # If we just check "Is this user an admin?" and "Are they the last one?"
        
        is_admin = UserRole.objects.filter(user=instance, role__key='administrator').exists()
        if is_admin:
             active_admin_count = UserRole.objects.filter(role__key='administrator', user__is_active=True).count()
             if active_admin_count <= 1:
                 raise ValidationError(
                    "Cannot deactivate the last Administrator. "
                    "The system requires at least one active Administrator."
                 )

@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def prevent_last_admin_user_deletion(sender, instance, **kwargs):
    """
    Prevent deleting a user if they are the last administrator.
    """
    # Check if this user IS an admin
    is_admin = UserRole.objects.filter(user=instance, role__key='administrator').exists()
    if is_admin:
        # Count TOTAL admins
        admin_count = UserRole.objects.filter(role__key='administrator').count()
        if admin_count <= 1:
            raise ValidationError(
                "Cannot delete the last Administrator account. "
                "The system requires at least one Administrator."
            )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def assign_default_role(sender, instance, created, **kwargs):
    """
    Auto-assign role to new users.
    First user = Administrator
    Others = Worker
    """
    if created:
        # Check total count. If 1, this is the first user.
        # Note: This is racy in high concurrency but acceptable for this scope.
        user_count = sender.objects.count()
        if user_count == 1:
            target_role_key = 'administrator'
        else:
            target_role_key = 'worker'
        
        try:
            # We need to find the role. If seed_roles hasn't run, this might fail.
            # We'll fail silently if roles don't exist to avoid breaking user creation in tests/migrations unless expected.
            role = Role.objects.get(key=target_role_key)
            
            # Assign role. Use instance as creator for self-bootstrapping.
            UserRole.objects.create(
                user=instance,
                role=role,
                created_by=instance,
                updated_by=instance
            )
        except Role.DoesNotExist:
            pass # Roles not seeded yet


