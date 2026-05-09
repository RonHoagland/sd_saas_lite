# staff/models.py
# Internal ServizDesk staff accounts — used exclusively for Django /admin/ access.
# These are NOT tenant users. StaffUser has no tenant_id and does not subclass TenantModel.
# Authentication is handled by StaffUserBackend (staff/backends.py).
# Source: Multi-Tenancy Specification V1 (staff access section).

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class StaffUserManager(BaseUserManager):

    def create_user(self, email, password=None, username=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        if username:
            username = str(username).strip().lower()
            if '@' in username:
                raise ValueError("StaffUser username must not contain '@' — use the email field for that.")
        user = self.model(email=email, username=username or None, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, username=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, username=username, **extra_fields)


class StaffUser(AbstractBaseUser, PermissionsMixin):
    """
    Internal ServizDesk staff account.

    Grants access to the Django /admin/ interface via AdminBypassMiddleware
    and the worker DB alias (BYPASSRLS=TRUE). Staff can view and modify all
    tenant data for support and operations purposes.

    Completely separate from the tenant User model (users/models.py).
    No tenant_id field — staff accounts are global to the ServizDesk platform.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    # Optional short username for staff (e.g. "wizjr101"). Lets staff log in
    # at /admin/ and at the tenant workspace login with a friendly handle
    # instead of a full email. Nullable for backward compatibility — existing
    # StaffUsers continue to authenticate by email until a username is set.
    username = models.CharField(
        max_length=150, unique=True, null=True, blank=True,
        help_text='Optional short login handle (alternative to email).',
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)       # Required for /admin/ access.
    is_superuser = models.BooleanField(default=True)   # All system users are full admins.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = StaffUserManager()

    # USERNAME_FIELD remains 'email' for Django's auth machinery (admin login
    # form labels it "Email"). The custom StaffUserBackend additionally
    # accepts the optional `username` field — see staff/backends.py.
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'Staff User'
        verbose_name_plural = 'Staff Users'

    def __str__(self):
        return f"{self.name} <{self.email}>"
