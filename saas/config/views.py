from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from infrastructure.models import TenantState
from staff.models import StaffUser
from users.models import User
from users.session_audit import close_sdta_session_record, register_sdta_session_record
from service.models import ServiceRequest, WorkOrder, Quote, Invoice

# Generic login error — never disclose which field was wrong.
# Per Security Features Spec V1, login UX must not reveal whether the
# workspace, username, or password was at fault.
_LOGIN_ERROR = "Invalid workspace, username, or password."


_ANNOUNCEMENTS = [
    (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Sed velit diem, viverra at enim sit amet, mattis convallis urna. "
        "In hoc habitasse platea dictumst. Etiam vel molestie orci. Aenean "
        "vestibulum sem sem, eu varius velit dictum eu. Vestibulum congue "
        "eleifend. Nunc at lorem vitae turpis dictum mollis malesuada "
        "laoreet neque. Pellentesque lectus enim, vehicula convallis felis "
        "sit amet, aliquam vulputate ipsum."
    ),
    (
        "Curabitur a tempor ex, at porttitor orci. Nam quis ultricies justo. "
        "Sed pulvinar, nibh at tincidunt fringilla, nunc ipsum vulputate leo, "
        "id interdum lorem augue sit amet mi. Pellentesque habitant morbi "
        "tristique senectus et netus et malesuada fames ac turpis egestas. "
        "Proin in fringilla libero. Vivamus varius faucibus ipsum quis luctus. "
        "Mauris gravida pulvinar eros eget blandit."
    ),
    (
        "Sed eu euismod libero. Nunc elementum lobortis erat. Maecenas at "
        "consequat neque. Vivamus sed neque vulputate justo dapibus ultricies "
        "et ut leo. Fusce eu lectus a lorem ullamcorper posuere. Nullam "
        "sagittis venenatis nibh et bibendum. Aliquam euismod sed metus eu "
        "consectetur. Proin egestas tellus nec odio maximus rutrum vel augue."
    ),
]


def _splash_context():
    return {
        "tenant_name": "{Tenant Name}",
        "announcements": _ANNOUNCEMENTS,
        "current_date": timezone.now().strftime("%A: %m/%d/%Y"),
        "app_version": settings.SERVIZDESK_VERSION,
    }


def splash_login_view(request):
    """Public splash/login landing page.

    Workspace-based login per LITE_DECISIONS.md §N. The form takes:
      - workspace: tenant subdomain (e.g. `acme`)
      - username:  tenant user's username, OR StaffUser email (contains '@')
      - password

    Resolution order:
      1. Look up the tenant by `workspace` (must exist and be Active).
      2. Try a tenant User scoped to (tenant_id, username).
      3. Fall back to a StaffUser by email (when username contains '@').
      4. On either success, store `active_tenant_id` in the session so
         middleware can establish tenant context on subsequent requests.

    Errors are deliberately generic ("Invalid workspace, username, or password.")
    to avoid revealing which field was wrong.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        workspace = request.POST.get("workspace", "").strip().lower()
        username = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password", "")

        # Echo entered workspace + username back on error so the user only
        # has to retype the password.
        ctx = _splash_context()
        ctx["workspace"] = workspace
        ctx["username"] = username

        if not workspace or not username or not password:
            ctx["error"] = "Workspace, username, and password are required."
            return render(request, "splash_login.html", ctx)

        # 1. Resolve the workspace.
        try:
            tenant = TenantState.objects.get(
                subdomain=workspace,
                status=TenantState.StatusChoices.ACTIVE,
            )
        except TenantState.DoesNotExist:
            ctx["error"] = _LOGIN_ERROR
            return render(request, "splash_login.html", ctx)

        # 2. Try tenant User.
        # Tenant usernames cannot contain '@' (UserManager enforces this on
        # create), so a username like "alex@company.com" will never match a
        # tenant User and we fall through to the StaffUser path.
        tenant_user = (
            User.all_objects
            .filter(tenant_id=tenant.id, username=username)
            .first()
        )
        if tenant_user and tenant_user.is_active and tenant_user.check_password(password):
            login(
                request, tenant_user,
                backend="django.contrib.auth.backends.ModelBackend",
            )
            request.session["active_tenant_id"] = str(tenant.id)
            request.session["active_tenant_subdomain"] = tenant.subdomain
            register_sdta_session_record(request, tenant, tenant_user)
            return redirect(request.GET.get("next", "home"))

        # 3. Fall back to StaffUser. Accepts either email (contains '@') or
        #    the optional StaffUser.username handle (no '@'). StaffUsers can
        #    sign into any tenant by selecting the workspace at login.
        staff = None
        if "@" in username:
            staff = StaffUser.objects.filter(email=username, is_active=True).first()
        else:
            staff = StaffUser.objects.filter(username=username, is_active=True).first()

        if staff and staff.check_password(password):
            login(
                request, staff,
                backend="staff.backends.StaffUserBackend",
            )
            # StaffUser has no tenant_id of its own; the session carries
            # which tenant they're working in for this session.
            request.session["active_tenant_id"] = str(tenant.id)
            request.session["active_tenant_subdomain"] = tenant.subdomain
            register_sdta_session_record(request, tenant, staff)
            return redirect(request.GET.get("next", "home"))

        ctx["error"] = _LOGIN_ERROR
        return render(request, "splash_login.html", ctx)

    return render(request, "splash_login.html", _splash_context())


@login_required(login_url="/")
def home_view(request):
    """Authenticated home/dashboard page.

    KPI counts are tenant-scoped via TenantManager (the request middleware
    sets the current tenant_id; queries auto-filter). With no tenant context
    set (e.g. local dev without subdomain), TenantManager returns the unfiltered
    queryset — fine for single-tenant dev databases.

    Status filters follow Lite UI Spec §17–§20:
      Requests : non-terminal ServiceRequest (exclude Resolved/Closed/Cancelled)
      Quotes   : Draft + Sent
      Jobs     : non-terminal WorkOrder (exclude Completed/Cancelled)
      Invoices : Draft + Sent + Overdue
    """
    user = request.user
    is_admin = getattr(user, "is_tenant_admin", False)

    role_label = "User"
    try:
        roles = user.employee_roles.select_related("role").all()
        if roles:
            role_label = ", ".join(r.role.name for r in roles)
    except Exception:
        pass

    today = timezone.localdate()

    sr_terminal = [
        ServiceRequest.StatusChoices.RESOLVED,
        ServiceRequest.StatusChoices.CLOSED,
        ServiceRequest.StatusChoices.CANCELLED,
    ]
    wo_terminal = [
        WorkOrder.StatusChoices.COMPLETED,
        WorkOrder.StatusChoices.CANCELLED,
    ]

    stats = {
        "service_requests": ServiceRequest.objects.exclude(status__in=sr_terminal).count(),
        "open_quotes": Quote.objects.filter(
            status__in=[Quote.StatusChoices.DRAFT, Quote.StatusChoices.SENT]
        ).count(),
        "open_work_orders": WorkOrder.objects.exclude(status__in=wo_terminal).count(),
        "unpaid_invoices": Invoice.objects.filter(
            status__in=[
                Invoice.StatusChoices.DRAFT,
                Invoice.StatusChoices.SENT,
                Invoice.StatusChoices.OVERDUE,
            ]
        ).count(),
    }

    todays_jobs_qs = (
        WorkOrder.objects
        .filter(scheduled_date=today)
        .exclude(status__in=wo_terminal)
        .select_related("customer")
        .order_by("scheduled_time")[:10]
    )

    # Today's Schedule — compact List Block contract per BLOCK_REFERENCE.md §3.2.
    schedule_columns = [
        {"key": "customer_name", "label": "Customer", "is_primary": True, "sortable": True},
        {"key": "description",   "label": "Description",                    "sortable": True},
        {"key": "scheduled_time","label": "Time",                            "sortable": True, "align": "end"},
    ]
    schedule_rows = [
        {
            "customer_name": (j.customer.company_name or str(j.customer)) if j.customer_id else "—",
            "description": j.subject,
            "scheduled_time": j.scheduled_time.strftime("%I:%M %p") if j.scheduled_time else "—",
            # TODO(Phase 4): wire to actual /jobs/<id>/ once Job detail page exists.
            "_href": "#",
        }
        for j in todays_jobs_qs
    ]
    schedule_empty_action = {
        "label": "Schedule a Job", "href": "#", "icon": "calendar-plus",
    }

    # Business Performance — Metric Data Block contract per §3.3.
    # Values are placeholder until Phase 6+ wires real receivables / revenue queries.
    business_metrics = [
        {"label": "Receivables",    "caption": "0 clients owe you", "href": "#"},
        {"label": "Upcoming Jobs",  "caption": "This week",         "href": "#"},
        {"label": "Revenue",        "caption": "This month",        "value": "$0", "href": "#"},
    ]

    context = {
        "role": role_label,
        "is_admin": is_admin,
        "active_nav": "dashboard",
        "stats": stats,
        "schedule_columns": schedule_columns,
        "schedule_rows": schedule_rows,
        "schedule_empty_action": schedule_empty_action,
        "business_metrics": business_metrics,
    }
    return render(request, "home.html", context)


def logout_view(request):
    """Log out and redirect back to the splash page."""
    close_sdta_session_record(request)
    logout(request)
    return redirect("splash-login")
