# config/context_processors.py
"""Template context shared across the ServizDesk UI."""

from django.conf import settings
from django.utils import timezone


def _greeting_for_hour(hour):
    """Time-of-day greeting in Title Case. Used in the Dashboard sub-header."""
    if 5 <= hour < 12:
        return 'Good Morning'
    if 12 <= hour < 17:
        return 'Good Afternoon'
    return 'Good Evening'


def _format_datetime_long(dt):
    """Long format: 'Friday, May 1, 2026 · 2:34 PM' (matches the JS tick formatter)."""
    # %-I is platform-specific (Linux/macOS, not Windows). Strip leading zero
    # manually for portability.
    hour_12 = dt.strftime('%I').lstrip('0') or '12'
    return dt.strftime(f'%A, %B %-d, %Y · {hour_12}:%M %p')


def servizdesk_ui(request):
    """Expose theme/asset version and active workspace info to all templates.

    Tenant context resolution mirrors TenantMiddleware (LITE_DECISIONS.md §N):
      - Tenant Users: tenant from request.user.tenant_id.
      - StaffUsers: tenant from session['active_tenant_id'] (workspace
        selected at login).
    """
    from staff.models import StaffUser
    from infrastructure.models import TenantState
    from users.models import TenantPreference

    user = getattr(request, 'user', None)
    is_authenticated = bool(user and user.is_authenticated)
    is_system_user = bool(is_authenticated and isinstance(user, StaffUser))

    # Session may not be present on every request path (e.g. internal API).
    session = getattr(request, 'session', None)

    tenant_id = None
    if is_authenticated:
        tenant_id = getattr(user, 'tenant_id', None)
        if not tenant_id and session is not None:
            tenant_id = session.get('active_tenant_id')

    tenant_name = ''
    workspace_subdomain = ''
    company_logo_url = ''
    tier_label = 'Lite'
    if is_authenticated and session is not None:
        workspace_subdomain = session.get('active_tenant_subdomain', '')
    if tenant_id:
        try:
            prefs = TenantPreference.all_objects.filter(tenant_id=tenant_id).first()
            if prefs and prefs.company_name:
                tenant_name = prefs.company_name
            if prefs and getattr(prefs, 'company_logo', None):
                try:
                    company_logo_url = prefs.company_logo.url
                except Exception:
                    company_logo_url = ''
            ts = TenantState.objects.filter(id=tenant_id).first()
            if ts:
                if not tenant_name:
                    tenant_name = ts.company_name
                if not workspace_subdomain:
                    workspace_subdomain = ts.subdomain
                if ts.tier:
                    tier_label = ts.tier
        except Exception:
            pass
    if not tenant_name:
        tenant_name = 'ServizDesk'

    # Header chrome: live-ticking datetime (server-rendered initial value, JS
    # takes over the per-minute tick) and time-of-day greeting (used by the
    # Dashboard sub-header only — not every page).
    now_local = timezone.localtime()
    current_datetime_long = _format_datetime_long(now_local)
    greeting = _greeting_for_hour(now_local.hour)

    # Display name for greeting: first_name → username fallback.
    user_display_name = ''
    if is_authenticated:
        user_display_name = getattr(user, 'first_name', '') or getattr(user, 'username', '')

    return {
        'SERVIZDESK_UI_ASSET_VERSION': getattr(
            settings,
            'SERVIZDESK_UI_ASSET_VERSION',
            '1',
        ),
        'is_system_user': is_system_user,
        'tenant_name': tenant_name,
        'workspace_subdomain': workspace_subdomain,
        'company_logo_url': company_logo_url,
        'tier_label': tier_label,
        'current_datetime_long': current_datetime_long,
        'greeting': greeting,
        'user_display_name': user_display_name,
    }
