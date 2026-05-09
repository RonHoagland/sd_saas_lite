"""Tests for Identity app: roles, assignments, and utilities."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from identity.models import Role, UserProfile, UserRole
from identity.utils import user_has_role

User = get_user_model()


@pytest.mark.django_db
class TestRoles:
	def test_create_role(self):
		admin = User.objects.create_user(username="admin", password="pass")

		role = Role.objects.create(
			key="owner_admin",
			name="Owner / Admin",
			description="Full access",
			created_by=admin,
			updated_by=admin,
		)

		assert role.id is not None
		assert role.key == "owner_admin"
		assert role.is_active is True

	def test_assign_role_to_user(self):
		admin = User.objects.create_user(username="admin", password="pass")
		worker = User.objects.create_user(username="worker", password="pass")

		role = Role.objects.create(
			key="worker_user",
			name="Worker",
			created_by=admin,
			updated_by=admin,
		)

		assignment = UserRole.objects.create(
			user=worker,
			role=role,
			created_by=admin,
			updated_by=admin,
		)

		assert assignment.id is not None
		assert assignment.user == worker
		assert assignment.role == role


@pytest.mark.django_db
class TestUserProfile:
	def test_create_profile(self):
		admin = User.objects.create_user(username="admin", password="pass")
		user = User.objects.create_user(username="alice", password="pass")

		profile = UserProfile.objects.create(
			user=user,
			display_name="Alice",
			time_zone="UTC",
			created_by=admin,
			updated_by=admin,
		)

		assert profile.id is not None
		assert profile.display_name == "Alice"
		assert profile.time_zone == "UTC"


@pytest.mark.django_db
class TestRoleUtils:
	def test_user_has_role(self):
		admin = User.objects.create_user(username="admin", password="pass")
		user = User.objects.create_user(username="bob", password="pass")

		role_owner = Role.objects.create(
			key="owner_admin",
			name="Owner",
			created_by=admin,
			updated_by=admin,
		)
		role_worker = Role.objects.create(
			key="worker_user",
			name="Worker",
			created_by=admin,
			updated_by=admin,
		)

		UserRole.objects.create(
			user=user,
			role=role_worker,
			created_by=admin,
			updated_by=admin,
		)

		assert user_has_role(user, ["worker_user"]) is True
		assert user_has_role(user, ["owner_admin"]) is False
		assert user_has_role(user, ["owner_admin", "worker_user"]) is True
		assert user_has_role(None, ["worker_user"]) is False


# ============================================================================
# USER/ADMIN TESTS - Verify admin workflows and UI interactions
# ============================================================================


@pytest.mark.django_db
class TestAdminRoleWorkflows:
	"""Test admin interface workflows for role management."""

	def setup_method(self):
		"""Setup: create admin user and client."""
		self.client = Client()
		self.admin = User.objects.create_superuser(
			username="admin", email="admin@test.local", password="adminpass"
		)

	def test_admin_login(self):
		"""Test admin can login to admin site."""
		# Login using Django's client.login()
		success = self.client.login(username="admin", password="adminpass")
		assert success is True
		
		# Verify admin can access admin dashboard
		response = self.client.get(reverse("admin:index"))
		assert response.status_code == 200

	def test_admin_can_create_role(self):
		"""Test admin can create a role via admin form."""
		self.client.login(username="admin", password="adminpass")

		response = self.client.post(
			reverse("admin:identity_role_add"),
			{
				"key": "owner_admin",
				"name": "Owner / Admin",
				"description": "Full system access",
				"is_system": True,
				"is_active": True,
			},
			follow=True,
		)
		assert response.status_code == 200

		# Verify role was created
		role = Role.objects.get(key="owner_admin")
		assert role.name == "Owner / Admin"
		assert role.is_system is True

	def test_admin_role_list_view(self):
		"""Test admin can view role list."""
		self.client.login(username="admin", password="adminpass")

		role = Role.objects.create(
			key="test_role",
			name="Test Role",
			created_by=self.admin,
			updated_by=self.admin,
		)

		response = self.client.get(reverse("admin:identity_role_changelist"))
		assert response.status_code == 200
		assert b"Test Role" in response.content

	def test_admin_can_change_role(self):
		"""Test admin can modify an existing role."""
		self.client.login(username="admin", password="adminpass")

		role = Role.objects.create(
			key="worker_user",
			name="Worker",
			created_by=self.admin,
			updated_by=self.admin,
		)

		response = self.client.post(
			reverse("admin:identity_role_change", args=[role.id]),
			{
				"key": "worker_user",
				"name": "Worker - Updated",
				"description": "Updated worker role",
				"is_system": True,
				"is_active": True,
			},
			follow=True,
		)
		assert response.status_code == 200

		# Verify change persisted
		role.refresh_from_db()
		assert role.name == "Worker - Updated"


@pytest.mark.django_db
class TestAdminUserRoleWorkflows:
	"""Test admin interface workflows for assigning roles to users."""

	def setup_method(self):
		"""Setup: create admin user, roles, and client."""
		self.client = Client()
		self.admin = User.objects.create_superuser(
			username="admin", email="admin@test.local", password="adminpass"
		)
		self.worker = User.objects.create_user(
			username="worker", password="workerpass"
		)

		self.role_owner = Role.objects.create(
			key="owner_admin",
			name="Owner / Admin",
			created_by=self.admin,
			updated_by=self.admin,
		)
		self.role_worker = Role.objects.create(
			key="worker_user",
			name="Worker",
			created_by=self.admin,
			updated_by=self.admin,
		)

	def test_admin_can_assign_role_to_user(self):
		"""Test admin can assign a role to a user via form."""
		self.client.login(username="admin", password="adminpass")

		response = self.client.post(
			reverse("admin:identity_userrole_add"),
			{
				"user": self.worker.id,
				"role": self.role_worker.id,
				"is_active": True,
			},
			follow=True,
		)
		assert response.status_code == 200

		# Verify assignment was created
		assignment = UserRole.objects.get(user=self.worker, role=self.role_worker)
		assert assignment.is_active is True

	def test_admin_userrole_list_view(self):
		"""Test admin can view list of user role assignments."""
		self.client.login(username="admin", password="adminpass")

		UserRole.objects.create(
			user=self.worker,
			role=self.role_worker,
			created_by=self.admin,
			updated_by=self.admin,
		)

		response = self.client.get(reverse("admin:identity_userrole_changelist"))
		assert response.status_code == 200
		assert b"worker" in response.content or self.worker.username.encode() in response.content

	def test_admin_can_revoke_role(self):
		"""Test admin can revoke a role by deactivating the assignment."""
		self.client.login(username="admin", password="adminpass")

		assignment = UserRole.objects.create(
			user=self.worker,
			role=self.role_worker,
			created_by=self.admin,
			updated_by=self.admin,
		)

		response = self.client.post(
			reverse("admin:identity_userrole_change", args=[assignment.id]),
			{
				"user": self.worker.id,
				"role": self.role_worker.id,
				"is_active": False,
			},
			follow=True,
		)
		assert response.status_code == 200

		# Verify role is now inactive
		assignment.refresh_from_db()
		assert assignment.is_active is False

		# Verify user no longer has the role
		assert user_has_role(self.worker, ["worker_user"]) is False


@pytest.mark.django_db
class TestAdminUserProfileWorkflows:
	"""Test admin interface workflows for user profiles."""

	def setup_method(self):
		"""Setup: create admin user and client."""
		self.client = Client()
		self.admin = User.objects.create_superuser(
			username="admin", email="admin@test.local", password="adminpass"
		)
		self.user = User.objects.create_user(username="alice", password="alicepass")

	def test_admin_can_create_profile(self):
		"""Test admin can create a user profile."""
		self.client.login(username="admin", password="adminpass")

		response = self.client.post(
			reverse("admin:identity_userprofile_add"),
			{
				"user": self.user.id,
				"display_name": "Alice Smith",
				"time_zone": "America/New_York",
				"is_active": True,
			},
			follow=True,
		)
		assert response.status_code == 200

		# Verify profile was created
		profile = UserProfile.objects.get(user=self.user)
		assert profile.display_name == "Alice Smith"
		assert profile.time_zone == "America/New_York"

	def test_admin_can_edit_profile(self):
		"""Test admin can edit an existing user profile."""
		self.client.login(username="admin", password="adminpass")

		profile = UserProfile.objects.create(
			user=self.user,
			display_name="Alice",
			time_zone="UTC",
			created_by=self.admin,
			updated_by=self.admin,
		)

		response = self.client.post(
			reverse("admin:identity_userprofile_change", args=[profile.id]),
			{
				"user": self.user.id,
				"display_name": "Alice M. Smith",
				"time_zone": "America/Los_Angeles",
				"is_active": True,
			},
			follow=True,
		)
		assert response.status_code == 200

		# Verify change persisted
		profile.refresh_from_db()
		assert profile.display_name == "Alice M. Smith"
		assert profile.time_zone == "America/Los_Angeles"

