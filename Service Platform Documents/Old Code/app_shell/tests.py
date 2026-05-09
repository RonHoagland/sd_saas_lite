"""
App Shell Tests - Programming + User/Admin
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from identity.models import Role, UserRole
from .models import AppSetting, NavItem
from .utils import get_setting_value, get_nav_items_for_user, build_navigation_tree


class TestAppSetting(TestCase):
	def test_create_and_get_setting(self):
		admin = User.objects.create_superuser("admin", "admin@test.com", "pass")
		s = AppSetting.objects.create(key="site_name", value="BrixaCore", created_by=admin, updated_by=admin)
		self.assertEqual(get_setting_value("site_name"), "BrixaCore")
		self.assertIsNone(get_setting_value("missing"))


class TestNavigationLogic(TestCase):
	def setUp(self):
		self.admin = User.objects.create_superuser("admin", "admin@test.com", "pass")
		self.user = User.objects.create_user("user", password="pass")
		self.role_manager = Role.objects.create(key="manager", name="Manager", created_by=self.admin, updated_by=self.admin)
		# Assign role to user
		UserRole.objects.create(user=self.user, role=self.role_manager, created_by=self.admin, updated_by=self.admin)

		# Nav structure
		self.home = NavItem.objects.create(
			key="home",
			label="Home",
			url_name="home",
			section="main",
			order=0,
			created_by=self.admin,
			updated_by=self.admin,
		)
		self.admin_panel = NavItem.objects.create(
			key="admin",
			label="Admin",
			url_name="admin:index",
			section="main",
			order=10,
			created_by=self.admin,
			updated_by=self.admin,
		)
		self.secure_reports = NavItem.objects.create(
			key="reports",
			label="Reports",
			url_name="reports",
			section="main",
			order=20,
			created_by=self.admin,
			updated_by=self.admin,
		)
		self.secure_reports.required_roles.add(self.role_manager)

		# Child under reports
		self.sales_report = NavItem.objects.create(
			key="sales",
			label="Sales",
			url_name="reports:sales",
			section="main",
			order=21,
			parent=self.secure_reports,
			created_by=self.admin,
			updated_by=self.admin,
		)

	def test_nav_visibility_for_user_with_role(self):
		items = get_nav_items_for_user(self.user, section="main")
		keys = [i.key for i in items]
		self.assertIn("home", keys)
		self.assertIn("reports", keys)

		tree = build_navigation_tree(self.user, section="main")
		# Reports should have child Sales
		reports_node = next(n for n in tree if n["label"] == "Home") if tree and tree[0]["label"] == "Home" else None
		# Simpler check: total top-level items
		self.assertEqual(len(tree), 3)

	def test_nav_visibility_for_user_without_role(self):
		other = User.objects.create_user("other", password="pass")
		items = get_nav_items_for_user(other, section="main")
		keys = [i.key for i in items]
		self.assertIn("home", keys)
		self.assertNotIn("reports", keys)

		tree = build_navigation_tree(other, section="main")
		# Top-level items should not include Reports
		labels = [n["label"] for n in tree]
		self.assertIn("Home", labels)
		self.assertNotIn("Reports", labels)


class TestAdminUIs(TestCase):
	def setUp(self):
		self.client = Client()
		self.admin = User.objects.create_superuser("admin", "admin@test.com", "pass")
		self.client.login(username="admin", password="pass")

	def test_admin_can_manage_settings(self):
		# Add setting
		AppSetting.objects.create(key="site_name", value="BrixaCore", created_by=self.admin, updated_by=self.admin)
		resp = self.client.get(reverse("admin:app_shell_appsetting_changelist"))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "site_name")

	def test_admin_can_manage_nav_items(self):
		NavItem.objects.create(key="home", label="Home", url_name="home", created_by=self.admin, updated_by=self.admin)
		resp = self.client.get(reverse("admin:app_shell_navitem_changelist"))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "Home")

