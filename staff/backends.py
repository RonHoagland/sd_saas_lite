# staff/backends.py
# Custom authentication backend for Django admin.
# Authenticates ServizDesk staff (StaffUser) independently of the tenant
# User model (AUTH_USER_MODEL = 'users.User').
#
# Django's login() stores the backend path in the session alongside the user PK.
# get_user() is called by Django's AuthenticationMiddleware on every subsequent
# request to retrieve the user from session — StaffUser instances are returned
# here, not tenant User instances.
#
# Source: Multi-Tenancy Specification V1 (staff access section).

from staff.models import StaffUser


class StaffUserBackend:

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Resolve the supplied identifier to a StaffUser.

        The `username` parameter accepts either:
          - an email address (contains '@') → matched against StaffUser.email
          - a short handle (no '@')         → matched against StaffUser.username

        Both at /admin/login/ (Django's admin form labels this field "Email")
        and at the tenant workspace login (config.views.splash_login_view).
        """
        if not username or not password:
            return None

        identifier = str(username).strip().lower()
        if '@' in identifier:
            user = StaffUser.objects.filter(email=identifier).first()
        else:
            user = StaffUser.objects.filter(username=identifier).first()

        if user is None:
            return None
        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        """
        Called by Django's session middleware on every admin request to
        reconstruct the user from the session-stored PK.
        """
        try:
            return StaffUser.objects.get(pk=user_id)
        except StaffUser.DoesNotExist:
            return None
