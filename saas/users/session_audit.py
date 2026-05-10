# users/session_audit.py
# SessionLog (audit session record) lifecycle tied to Django session auth.
#
# The browser keeps the standard Django session cookie (opaque session key).
# SessionLog.id (UUID, TenantModel primary key) is the ServizDesk session record
# id — stored server-side in the Django session payload for audit linkage.

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import logout
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone

from config.tenant_context import clear_current_tenant_id, set_current_tenant_id
from infrastructure.models import TenantState

SESSION_RECORD_SESSION_KEY = 'sdta_session_record_id'
SESSION_IDLE_SECONDS_KEY = 'sdta_session_idle_seconds'
SESSION_IDLE_DEADLINE_TS_KEY = 'sdta_idle_deadline_ts'


def resolve_idle_seconds_for_tenant(tenant_id) -> int:
    """Idle allowance for sliding timeout; TenantPreference overrides global default."""
    from users.models import TenantPreference

    pref = TenantPreference.all_objects.filter(tenant_id=tenant_id).first()
    if pref is not None and pref.session_timeout_minutes:
        return int(pref.session_timeout_minutes) * 60
    return int(getattr(settings, 'SDTA_SESSION_IDLE_TIMEOUT_SECONDS', 1800))


def _client_ip(request) -> str:
    xfwd = request.META.get('HTTP_X_FORWARDED_FOR')
    if xfwd:
        return xfwd.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or '127.0.0.1'


def register_sdta_session_record(request, tenant: TenantState, django_user) -> None:
    """
    Inserts SessionLog and stores session-record UUID plus idle deadline keys.

    Expects an authenticated Django session (after login()). Caller must set
    active_tenant_id / active_tenant_subdomain on the session when applicable.
    """
    from staff.models import StaffUser
    from users.models import SessionLog, User

    idle_seconds = resolve_idle_seconds_for_tenant(tenant.id)
    now = timezone.now()

    user_fk = django_user if isinstance(django_user, User) else None
    snapshot: dict = {}
    if isinstance(django_user, StaffUser):
        snapshot = {
            'staff_user_id': str(django_user.pk),
            'staff_email': getattr(django_user, 'email', '') or '',
        }

    ip = _client_ip(request)
    ua = (request.META.get('HTTP_USER_AGENT') or '').strip()
    if not ua:
        ua = '-'
    ua = ua[:2048]

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                'SET LOCAL app.current_tenant_id = %s',
                [str(tenant.id)],
            )
        set_current_tenant_id(str(tenant.id))
        try:
            sl = SessionLog.objects.create(
                tenant_id=tenant.id,
                user=user_fk,
                tier_at_login=tenant.tier,
                login_at=now,
                expiration_at=now + timedelta(seconds=idle_seconds),
                ip_address=ip,
                user_agent=ua,
                permission_snapshot=snapshot,
            )
            record_id = str(sl.id)
        finally:
            clear_current_tenant_id()

    request.session[SESSION_RECORD_SESSION_KEY] = record_id
    request.session[SESSION_IDLE_SECONDS_KEY] = idle_seconds
    request.session[SESSION_IDLE_DEADLINE_TS_KEY] = (
        now + timedelta(seconds=idle_seconds)
    ).timestamp()
    request.session.modified = True


def close_sdta_session_record(request) -> None:
    """Sets logout_at on the open SessionLog row if present (login/logout/idle)."""
    from users.models import SessionLog

    record_id = request.session.get(SESSION_RECORD_SESSION_KEY)
    tenant_id = request.session.get('active_tenant_id')
    if not record_id or not tenant_id:
        return

    now = timezone.now()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                'SET LOCAL app.current_tenant_id = %s',
                [str(tenant_id)],
            )
        set_current_tenant_id(str(tenant_id))
        try:
            sl = SessionLog.all_objects.filter(
                pk=record_id,
                tenant_id=tenant_id,
                logout_at__isnull=True,
            ).first()
            if sl is None:
                return
            sl.logout_at = now
            sl.save(update_fields=['logout_at', 'updated_on'])
        finally:
            clear_current_tenant_id()


def extend_idle_deadline(request) -> None:
    """Advances sliding idle deadline after an authenticated request."""
    idle_sec = request.session.get(SESSION_IDLE_SECONDS_KEY)
    if not idle_sec:
        return
    request.session[SESSION_IDLE_DEADLINE_TS_KEY] = (
        timezone.now() + timedelta(seconds=int(idle_sec))
    ).timestamp()
    request.session.modified = True


def idle_timeout_response(request):
    if request.path.startswith('/api/'):
        return JsonResponse({'detail': 'Session expired due to inactivity.'}, status=401)
    return redirect('splash-login')


class SessionIdleTimeoutMiddleware:
    """
    Enforces per-tenant sliding idle timeout using keys set at login.

    Runs after AuthenticationMiddleware. Uses standard Django session cookie;
    idle limits are stricter than SESSION_COOKIE_AGE when TenantPreference says so.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        should_check_idle = (
            user
            and user.is_authenticated
            and hasattr(request, 'session')
            and request.session.get(SESSION_IDLE_DEADLINE_TS_KEY) is not None
        )
        if should_check_idle:
            deadline_ts = float(request.session[SESSION_IDLE_DEADLINE_TS_KEY])
            now_ts = timezone.now().timestamp()
            if now_ts >= deadline_ts:
                close_sdta_session_record(request)
                logout(request)
                return idle_timeout_response(request)

        response = self.get_response(request)

        if (
            user
            and user.is_authenticated
            and hasattr(request, 'session')
            and request.session.get(SESSION_IDLE_SECONDS_KEY)
        ):
            extend_idle_deadline(request)

        return response
