# users/views.py
import uuid as _uuid
from datetime import date as _date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from config.tenant_context import get_current_tenant_id
from users.models import User, TenantPreference, Department, Position, Role, EmployeeRole


def _require_admin(request):
    return (getattr(request.user, 'is_tenant_admin', False) or
            getattr(request.user, 'is_staff', False))


def _get_tenant_id(user):
    """Return the tenant_id for this user; falls back to middleware context for StaffUsers."""
    return getattr(user, 'tenant_id', None) or get_current_tenant_id()


@login_required(login_url='/')
def employees_list_view(request):
    """List of all tenant employees."""
    if not _require_admin(request):
        return redirect('home')

    employees = (
        User.objects
        .select_related('person', 'department', 'position')
        .order_by('person__last_name', 'person__first_name')
    )

    return render(request, 'users/employees.html', {
        'employees': employees,
        'active_nav': 'employees',
        'breadcrumb': [('Employees', None)],
    })


@login_required(login_url='/')
def employee_detail_view(request, pk):
    """Employee detail page."""
    if not _require_admin(request):
        return redirect('home')

    emp = get_object_or_404(
        User.objects.select_related('person', 'department', 'position')
                    .prefetch_related('employee_roles__role'),
        pk=pk,
    )

    all_roles = Role.objects.order_by('name')
    assigned_role_ids = set(emp.employee_roles.values_list('role_id', flat=True))

    if request.method == 'POST' and 'update_account' in request.POST:
        new_username = request.POST.get('username', '').strip()
        new_email = request.POST.get('email', '').strip()
        errors = []
        if new_username and new_username != emp.username:
            if User.all_objects.filter(username=new_username).exclude(pk=emp.pk).exists():
                errors.append('Username already taken.')
        if new_email and new_email != emp.email:
            if User.all_objects.filter(email=new_email).exclude(pk=emp.pk).exists():
                errors.append('Email already in use.')
        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            if new_username:
                emp.username = new_username
            if new_email:
                emp.email = new_email
            emp.employee_number = request.POST.get('employee_number', '').strip()
            emp.status = request.POST.get('status', emp.status)
            emp.is_tenant_admin = 'is_tenant_admin' in request.POST
            hire_date_str = request.POST.get('hire_date', '').strip()
            if hire_date_str:
                try:
                    emp.hire_date = _date.fromisoformat(hire_date_str)
                except ValueError:
                    pass
            else:
                emp.hire_date = None
            emp.updated_by = request.user.username
            emp.save()
            messages.success(request, 'Account updated.')
        return redirect('employee-detail', pk=pk)

    if request.method == 'POST' and 'update_roles' in request.POST:
        # Convert POST string IDs to UUIDs to match assigned_role_ids type
        selected_ids = set()
        for rid in request.POST.getlist('roles'):
            try:
                selected_ids.add(_uuid.UUID(str(rid)))
            except (ValueError, AttributeError):
                pass
        # Add newly selected
        for role_id in selected_ids - assigned_role_ids:
            EmployeeRole.objects.get_or_create(
                tenant_id=emp.tenant_id,
                employee=emp,
                role_id=role_id,
                defaults={'created_by': request.user.username,
                          'updated_by': request.user.username},
            )
        # Remove deselected
        EmployeeRole.objects.filter(
            employee=emp, role_id__in=assigned_role_ids - selected_ids
        ).delete()
        messages.success(request, 'Roles updated.')
        return redirect('employee-detail', pk=pk)

    is_admin = _require_admin(request)
    return render(request, 'users/employee_detail.html', {
        'emp': emp,
        'active_nav': 'employees',
        'is_admin': is_admin,
        'status_choices': User.StatusChoices.choices,
        'all_roles': all_roles,
        'assigned_role_ids': assigned_role_ids,
    })


@login_required(login_url='/')
def tenant_preferences_view(request):
    """View and edit tenant-level company preferences."""
    if not _require_admin(request):
        return redirect('home')

    prefs, _ = TenantPreference.objects.get_or_create(
        tenant_id=_get_tenant_id(request.user),
        defaults={'company_name': '', 'created_by': request.user.username,
                  'updated_by': request.user.username},
    )

    is_admin = _require_admin(request)
    if request.method == 'POST':
        fields = [
            'company_name', 'address', 'city', 'state', 'zip', 'country',
            'phone', 'fax', 'email', 'website',
            'default_currency', 'currency_symbol', 'decimal_precision',
            'timezone', 'date_format', 'phone_country_code',
            'default_tax_rate', 'tax_label', 'default_payment_terms',
            'default_quote_expiration_days', 'fiscal_year_start_month',
            'mfa_required', 'session_timeout_minutes',
        ]
        for field in fields:
            val = request.POST.get(field)
            if val is not None:
                if prefs._meta.get_field(field).get_internal_type() == 'BooleanField':
                    setattr(prefs, field, field in request.POST)
                else:
                    setattr(prefs, field, val)
        prefs.updated_by = request.user.username
        try:
            prefs.save()
            messages.success(request, 'Preferences saved.')
        except Exception as exc:
            messages.error(request, f'Could not save preferences: {exc}')
        return redirect('tenant-preferences')

    return render(request, 'users/tenant_preferences.html', {
        'prefs': prefs,
        'active_nav': 'tenant-preferences',
        'active_group': 'settings',
        'is_admin': is_admin,
        'breadcrumb': [('Settings', None), ('Company Preferences', None)],
    })


# ─── Organisation settings ────────────────────────────────────────────────────

@login_required(login_url='/')
def departments_view(request):
    """List and create Departments."""
    if not _require_admin(request):
        return redirect('home')

    is_admin = _require_admin(request)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Department name is required.')
        else:
            try:
                Department.objects.create(
                    tenant_id=_get_tenant_id(request.user),
                    name=name,
                    created_by=request.user.username,
                    updated_by=request.user.username,
                )
                messages.success(request, f'Department "{name}" created.')
            except Exception as exc:
                messages.error(request, f'Could not create department: {exc}')
        return redirect('departments')

    departments = Department.objects.order_by('name')
    return render(request, 'users/departments.html', {
        'departments': departments,
        'active_nav': 'departments',
        'active_group': 'settings',
        'is_admin': is_admin,
    })


@login_required(login_url='/')
def positions_view(request):
    """List and create Positions."""
    if not _require_admin(request):
        return redirect('home')

    is_admin = _require_admin(request)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        dept_id = request.POST.get('department', '').strip()
        if not title:
            messages.error(request, 'Position title is required.')
        elif not dept_id:
            messages.error(request, 'Please select a department.')
        else:
            try:
                Position.objects.create(
                    tenant_id=_get_tenant_id(request.user),
                    title=title,
                    department_id=dept_id,
                    created_by=request.user.username,
                    updated_by=request.user.username,
                )
                messages.success(request, f'Position "{title}" created.')
            except Exception as exc:
                messages.error(request, f'Could not create position: {exc}')
        return redirect('positions')

    positions = Position.objects.select_related('department').order_by('department__name', 'title')
    departments = Department.objects.order_by('name')
    return render(request, 'users/positions.html', {
        'positions': positions,
        'departments': departments,
        'active_nav': 'positions',
        'active_group': 'settings',
        'is_admin': is_admin,
    })


@login_required(login_url='/')
def roles_view(request):
    """List and create Roles."""
    if not _require_admin(request):
        return redirect('home')

    is_admin = _require_admin(request)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Role name is required.')
        else:
            try:
                Role.objects.create(
                    tenant_id=_get_tenant_id(request.user),
                    name=name,
                    is_custom=True,
                    created_by=request.user.username,
                    updated_by=request.user.username,
                )
                messages.success(request, f'Role "{name}" created.')
            except Exception as exc:
                messages.error(request, f'Could not create role: {exc}')
        return redirect('roles')

    roles = Role.objects.order_by('name')
    return render(request, 'users/roles.html', {
        'roles': roles,
        'active_nav': 'roles',
        'active_group': 'settings',
        'is_admin': is_admin,
    })
