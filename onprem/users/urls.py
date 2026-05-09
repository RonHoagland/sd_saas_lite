# users/urls.py
from django.urls import path
from users.views import (
    employees_list_view, employee_detail_view, tenant_preferences_view,
    departments_view, positions_view, roles_view,
)

urlpatterns = [
    path('employees/', employees_list_view, name='employees'),
    path('employees/<uuid:pk>/', employee_detail_view, name='employee-detail'),
    path('settings/company/', tenant_preferences_view, name='tenant-preferences'),
    path('settings/departments/', departments_view, name='departments'),
    path('settings/positions/', positions_view, name='positions'),
    path('settings/roles/', roles_view, name='roles'),
]
