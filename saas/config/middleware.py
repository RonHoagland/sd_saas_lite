# config/middleware.py
# Source: Multi-Tenancy Specification V1, Section 5; Technical Architecture V2, Section 4.

import secrets
from django.conf import settings
from django.contrib.auth import logout
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import redirect

from .tenant_context import set_current_tenant_id, clear_current_tenant_id


# ─── TenantMiddleware ─────────────────────────────────────────────────────────

class TenantMiddleware:
    """
    Sets the tenant context for every non-admin, non-internal request.

    Two layers of tenant enforcement:
      1. Python-level: set_current_tenant_id() → TenantManager auto-filters.
      2. PostgreSQL-level: SET LOCAL app.current_tenant_id → RLS policies fire.

    SET LOCAL is used (not SET) so the variable is scoped to the current
    transaction and reset automatically at transaction end. This is required
    for PgBouncer transaction-mode pooling compatibility.

    Must run AFTER AuthenticationMiddleware so request.user is available.
    Must run AFTER AdminBypassMiddleware so /admin/ paths are already excluded.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = None
        is_authenticated = bool(getattr(request.user, "is_authenticated", False))
        is_staff = bool(getattr(request.user, "is_staff", False))
        is_superuser = bool(getattr(request.user, "is_superuser", False))

        if is_authenticated:
            # Tenant Users have a bound tenant_id on the user record.
            tenant_id = getattr(request.user, 'tenant_id', None)

            # StaffUsers have no tenant_id of their own — the session carries
            # which workspace they signed into. Per LITE_DECISIONS.md §N, the
            # workspace is selected at login. StaffUsers retain cross-tenant
            # capability via /admin/; in the tenant app they operate inside
            # the chosen workspace's context like any other user.
            #
            # `request.session` may not exist if SessionMiddleware hasn't run
            # (some test paths, internal API requests, etc.) — guard with
            # hasattr so we degrade gracefully.
            if not tenant_id and hasattr(request, 'session'):
                session_tid = request.session.get("active_tenant_id")
                if session_tid:
                    tenant_id = session_tid

        # Skip context setup for /admin/ (handled by AdminBypassMiddleware) or
        # truly unauthenticated requests.
        if not tenant_id:
            return self.get_response(request)

        set_current_tenant_id(str(tenant_id))

        try:
            # Set DB session variables
            with transaction.atomic():
                with connection.cursor() as cursor:
                    if tenant_id:
                        cursor.execute("SET LOCAL app.current_tenant_id = %s", [str(tenant_id)])
                    if is_authenticated:
                        if is_staff:
                            cursor.execute("SET LOCAL app.is_staff = 'true'")
                        if is_superuser:
                            cursor.execute("SET LOCAL app.is_superuser = 'true'")

                response = self.get_response(request)
            return response
        finally:
            if tenant_id:
                clear_current_tenant_id()


# ─── AdminBypassMiddleware ────────────────────────────────────────────────────

class AdminBypassMiddleware:
    """
    Guards /admin/ so only StaffUser (system users) can access it.

    If a tenant User has an active session and navigates to /admin/, their
    session is flushed and they are redirected to the admin login page.
    This prevents the AttributeError from User lacking PermissionsMixin and
    gives a clear recovery path.

    TenantModelAdmin already targets the 'worker' alias explicitly for reads
    and writes. This middleware also ensures tenant context is never set for
    admin requests (enforced downstream by TenantMiddleware checking is_staff).

    Source: Multi-Tenancy Specification V1, Section 7.
    """

    ADMIN_PREFIX = '/admin/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.ADMIN_PREFIX):
            user = getattr(request, 'user', None)
            if user and user.is_authenticated:
                from staff.models import StaffUser
                if not isinstance(user, StaffUser):
                    # Tenant user trying to access admin — flush session and
                    # redirect to admin login so they can use a system account.
                    from users.session_audit import close_sdta_session_record

                    close_sdta_session_record(request)
                    logout(request)
                    return redirect(f'{self.ADMIN_PREFIX}login/?next={request.path}')
        return self.get_response(request)


# ─── InternalAPIKeyMiddleware ─────────────────────────────────────────────────

class InternalAPIKeyMiddleware:
    """
    Validates the shared secret key on all /internal/api/ requests.

    The key is passed as a Bearer token in the Authorization header.
    Uses secrets.compare_digest to prevent timing-oracle attacks.

    Returns HTTP 401 immediately if the key is missing or incorrect.
    Returns HTTP 503 if INTERNAL_API_KEY is not configured in settings.

    Source: Internal API Specification V1.
    """

    INTERNAL_PREFIX = '/internal/api/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.INTERNAL_PREFIX):
            expected_key = getattr(settings, 'INTERNAL_API_KEY', '')

            if not expected_key:
                return JsonResponse(
                    {'error': 'Internal API key not configured.'},
                    status=503,
                )

            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth_header.startswith('Bearer '):
                return JsonResponse(
                    {'error': 'Authorization header missing or malformed.'},
                    status=401,
                )

            provided_key = auth_header[len('Bearer '):]
            if not secrets.compare_digest(provided_key, expected_key):
                return JsonResponse({'error': 'Invalid API key.'}, status=401)

        return self.get_response(request)
