from django.db import models
from django.core.exceptions import ValidationError

from core.models import BaseModel
from identity.models import Role
from identity.utils import user_has_role


class AppSetting(BaseModel):
	"""
	Simple application setting for UI shell (branding, theme, etc.).
	Uses `key` + `value` with optional description.
	"""

	key = models.CharField(max_length=100, unique=True)
	value = models.CharField(max_length=1000)
	description = models.TextField(blank=True)

	class Meta:
		indexes = [
			models.Index(fields=["key"]),
		]

	def __str__(self) -> str:
		return f"{self.key}"


class NavItem(BaseModel):
	"""
	Navigation item shown in the App Shell.

	Supports role-based visibility and hierarchy via parent/child items.
	"""

	key = models.CharField(max_length=100, unique=True)
	label = models.CharField(max_length=200)
	url_name = models.CharField(max_length=200, help_text="Django URL name")
	icon = models.CharField(max_length=100, blank=True)
	section = models.CharField(max_length=50, default="main", help_text="Nav section grouping")
	order = models.IntegerField(default=0)

	parent = models.ForeignKey(
		"self",
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name="children",
	)

	required_roles = models.ManyToManyField(
		Role,
		blank=True,
		related_name="nav_items",
		help_text="Roles required to see this item (empty = visible to all)",
	)

	class Meta:
		indexes = [
			models.Index(fields=["section", "order"]),
			models.Index(fields=["parent", "order"]),
		]
		ordering = ["section", "parent__id", "order", "label"]

	def __str__(self) -> str:
		return f"{self.label}"

	def is_allowed_for(self, user) -> bool:
		"""Return True if the user can see this item based on roles."""
		if not self.is_active:
			return False
		roles = list(self.required_roles.values_list("key", flat=True))
		if not roles:
			return True
		return user_has_role(user, roles)

