from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
    logout,
    get_user_model,
)
from django.contrib.sessions.models import Session
from django.db import DatabaseError
from django.middleware.csrf import rotate_token
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


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
        user_model = get_user_model()
        username_field = user_model.USERNAME_FIELD
        identifier = request.data.get(username_field)
        password = request.data.get("password")

        if not identifier or not password:
            return Response(
                {"detail": f"{username_field} and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Safe manual auth path: avoid full-model SELECT from authenticate()
        # because schema drift can cause ProgrammingError inside request atomic().
        # Authenticate by username only — not email (email is not a login factor).
        try:
            candidate = (
                user_model.all_objects.only(
                    "id", "username", "email", "password", "tenant_id", "is_active"
                )
                .filter(**{username_field: identifier})
                .first()
            )
        except DatabaseError:
            return Response(
                {"detail": "Authentication unavailable: database schema is out of sync."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not candidate or not candidate.check_password(password):
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user = candidate
        user.backend = "api.backends.SchemaSafeSessionBackend"
        if not user:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {"detail": "User account is disabled."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            if not request.session.session_key:
                request.session.create()
            request.session[SESSION_KEY] = str(user.pk)
            request.session[BACKEND_SESSION_KEY] = user.backend
            request.session[HASH_SESSION_KEY] = user.get_session_auth_hash()
            request.session.modified = True
            rotate_token(request)
            _ = Session.objects.filter(session_key=request.session.session_key).exists()
        except DatabaseError:
            return Response(
                {"detail": "Authentication unavailable: session storage is out of sync."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        csrf_token = get_token(request)
        try:
            # Avoid deferred-field DB fetch here; schema drift can make this query fail
            # and roll back session writes in the surrounding request transaction.
            is_tenant_admin = bool(getattr(user, "__dict__", {}).get("is_tenant_admin", False))
        except Exception:
            is_tenant_admin = False
        return Response(
            {
                "id": str(user.id),
                "username": getattr(user, "username", ""),
                "email": getattr(user, "email", ""),
                "tenant_id": str(getattr(user, "tenant_id", "")),
                "is_tenant_admin": is_tenant_admin,
                "csrfToken": csrf_token,
            },
            status=status.HTTP_200_OK,
        )


class SessionLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            is_tenant_admin = bool(getattr(user, "__dict__", {}).get("is_tenant_admin", False))
        except Exception:
            is_tenant_admin = False
        return Response(
            {
                "id": str(user.id),
                "username": getattr(user, "username", ""),
                "email": getattr(user, "email", ""),
                "tenant_id": str(getattr(user, "tenant_id", "")),
                "is_tenant_admin": is_tenant_admin,
                "is_active": bool(getattr(user, "is_active", False)),
            },
            status=status.HTTP_200_OK,
        )
