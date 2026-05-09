"""
Identity utilities: role lookups and checks.
"""

from typing import Iterable

from django.contrib.auth import get_user_model

from .models import Role

User = get_user_model()


def user_has_role(user: User, role_keys: Iterable[str]) -> bool:
    """Return True if the user has at least one of the specified role keys."""
    if not user or not user.is_authenticated:
        return False
    keys = set(role_keys)
    return user.user_roles.filter(role__key__in=keys, is_active=True, role__is_active=True).exists()
