"""
REST session-cookie auth endpoints for SDTA.

The login flow mirrors `config.views.splash_login_view` and is the
authoritative implementation of LITE_DECISIONS §N (workspace-based
login). Both endpoints serve the same product behaviour — one for the
server-rendered splash page, this one for REST/SPA clients.

Request shape for POST /api/v1/auth/login/:
    {"workspace": "<subdomain>", "username": "<handle>", "password": "<pw>"}

Resolution order:
    1. Resolve TenantState by `workspace` (must be ACTIVE).
    2. Try tenant User scoped to (tenant_id, username). Tenant usernames
       are unique per (tenant_id, username) — see users.User.Meta — so
       global lookups would let a username from tenant A authenticate
       into tenant B.
    3. Fall back to StaffUser: by email when '@' in username, else by
       StaffUser.username.
    4. On success, store `active_tenant_id` and `active_tenant_subdomain`
       in the session so TenantMiddleware can establish tenant context on
       subsequent requests (StaffUsers have no tenant_id of their own).
       A `users.SessionLog` row is created with `tier_at_login` from the
       workspace tenant; its UUID primary key is stored in the session under
       `sdta_session_record_id` (browser keeps the standard Django session id
       cookie only).

All credential failures return HTTP 401 with a single generic message,
per Security Features Spec V1 — never disclose which field was wrong.
"""

from django.contrib.auth import login, logout, get_user_model
from django.db import DatabaseError
from django.middleware.csrf import rotate_token, get_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from infrastructure.models import TenantState
from staff.models import StaffUser
from users.session_audit import close_sdta_session_record, register_sdta_session_record


_GENERIC_CRED_ERROR = "Invalid workspace, username, or password."
_DB_UNAVAILABLE = "Authentication unavailable: database is out of sync."
_SESSION_UNAVAILABLE = "Authentication unavailable: session storage is out of sync."


class CSRFTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        token = get_token(request)
        return Response({"csrfToken": token})


class SessionLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        workspace = (request.data.get("workspace") or "").strip().lower()
        identifier = (request.data.get("username") or "").strip().lower()
        password = request.data.get("password") or ""

        if not workspace or not identifier or not password:
            return Response(
                {"detail": "workspace, username, and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = TenantState.objects.get(
                subdomain=workspace,
                status=TenantState.StatusChoices.ACTIVE,
            )
        except TenantState.DoesNotExist:
            return Response(
                {"detail": _GENERIC_CRED_ERROR},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except DatabaseError:
            return Response(
                {"detail": _DB_UNAVAILABLE},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Tenant usernames cannot contain '@' (UserManager enforces this on
        # create), so identifiers like "alex@company.com" never match a
        # tenant User and we fall through to the StaffUser path.
        user_model = get_user_model()
        try:
            tenant_user = (
                user_model.all_objects.only(
                    "id", "username", "email", "password",
                    "tenant_id", "is_active", "is_tenant_admin",
                )
                .filter(tenant_id=tenant.id, username=identifier)
                .first()
            )
        except DatabaseError:
            return Response(
                {"detail": _DB_UNAVAILABLE},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if tenant_user is not None:
            if tenant_user.is_active and tenant_user.check_password(password):
                tenant_user.backend = "api.backends.SchemaSafeSessionBackend"
                return self._establish_session(
                    request,
                    user=tenant_user,
                    tenant=tenant,
                    is_tenant_admin=bool(
                        getattr(tenant_user, "__dict__", {}).get(
                            "is_tenant_admin", False
                        )
                    ),
                )
            # Match found but credentials/state failed. Do NOT proceed to
            # the StaffUser path — the username is owned by a tenant user
            # in this workspace, and we should not silently authenticate
            # a same-named staff account.
            return Response(
                {"detail": _GENERIC_CRED_ERROR},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            if "@" in identifier:
                staff = StaffUser.objects.filter(
                    email=identifier, is_active=True
                ).first()
            else:
                staff = StaffUser.objects.filter(
                    username=identifier, is_active=True
                ).first()
        except DatabaseError:
            return Response(
                {"detail": _DB_UNAVAILABLE},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if staff is not None and staff.check_password(password):
            staff.backend = "staff.backends.StaffUserBackend"
            return self._establish_session(
                request,
                user=staff,
                tenant=tenant,
                # Staff acting in a tenant context receive tenant-admin
                # capability for that session, mirroring TenantModelAdmin's
                # worker-alias bypass and the splash login flow.
                is_tenant_admin=True,
            )

        return Response(
            {"detail": _GENERIC_CRED_ERROR},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    @staticmethod
    def _establish_session(request, *, user, tenant, is_tenant_admin):
        try:
            login(request, user, backend=user.backend)
            request.session["active_tenant_id"] = str(tenant.id)
            request.session["active_tenant_subdomain"] = tenant.subdomain
            register_sdta_session_record(request, tenant, user)
            request.session.modified = True
            rotate_token(request)
        except DatabaseError:
            return Response(
                {"detail": _SESSION_UNAVAILABLE},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        csrf_token = get_token(request)
        return Response(
            {
                "id": str(user.pk),
                "username": getattr(user, "username", "") or "",
                "email": getattr(user, "email", "") or "",
                "tenant_id": str(tenant.id),
                "workspace": tenant.subdomain,
                "is_tenant_admin": bool(is_tenant_admin),
                "csrfToken": csrf_token,
            },
            status=status.HTTP_200_OK,
        )


class SessionLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        close_sdta_session_record(request)
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            raw_admin_flag = getattr(user, "__dict__", {}).get(
                "is_tenant_admin", False
            )
        except Exception:
            raw_admin_flag = False
        is_tenant_admin = bool(raw_admin_flag)

        # Tenant Users carry their own tenant_id; StaffUsers operate in
        # the tenant chosen at login (stored on the session).
        raw_tenant = getattr(user, "tenant_id", None)
        if raw_tenant:
            tenant_id = str(raw_tenant)
        else:
            tenant_id = request.session.get("active_tenant_id", "")
        workspace = request.session.get("active_tenant_subdomain", "")

        if not is_tenant_admin and isinstance(user, StaffUser):
            is_tenant_admin = True

        return Response(
            {
                "id": str(user.pk),
                "username": getattr(user, "username", "") or "",
                "email": getattr(user, "email", "") or "",
                "tenant_id": tenant_id,
                "workspace": workspace,
                "is_tenant_admin": is_tenant_admin,
                "is_active": bool(getattr(user, "is_active", False)),
            },
            status=status.HTTP_200_OK,
        )
