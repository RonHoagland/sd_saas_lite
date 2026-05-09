"""
App Shell utilities: build navigation per user and access roles.
"""

from typing import List, Dict, Optional

from .models import NavItem, AppSetting


def get_setting_value(key: str, default: Optional[str] = None) -> Optional[str]:
	"""Return AppSetting value for key or default."""
	try:
		setting = AppSetting.objects.get(key=key, is_active=True)
		return setting.value
	except AppSetting.DoesNotExist:
		return default


def get_nav_items_for_user(user, section: Optional[str] = None) -> List[NavItem]:
	"""Return NavItems visible to a user, optionally filtered by section."""
	qs = NavItem.objects.filter(is_active=True)
	if section:
		qs = qs.filter(section=section)
	# Filter by role visibility
	items = []
	for item in qs.select_related("parent").prefetch_related("required_roles"):
		if item.is_allowed_for(user):
			items.append(item)
	# Order already defined by Meta.ordering
	return items


def build_navigation_tree(user, section: Optional[str] = None) -> List[Dict]:
	"""
	Build a nested navigation tree for the given user.
	Each node dict contains: id, label, url_name, icon, children.
	"""
	items = get_nav_items_for_user(user, section)
	by_parent = {}
	for item in items:
		parent_id = item.parent_id or None
		by_parent.setdefault(parent_id, []).append(item)
	
	def serialize(item: NavItem) -> Dict:
		return {
			"id": str(item.id),
			"label": item.label,
			"url_name": item.url_name,
			"icon": item.icon,
			"children": [serialize(child) for child in by_parent.get(item.id, [])],
		}
	
	# Top-level items have parent_id None
	top_level = by_parent.get(None, [])
	return [serialize(item) for item in top_level]
