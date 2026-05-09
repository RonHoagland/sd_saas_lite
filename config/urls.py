# config/urls.py

from django.contrib import admin
from django.urls import path, include
from config.views import (
    home_view,
    logout_view,
    splash_login_view,
)

urlpatterns = [
    path('', splash_login_view, name='splash-login'),
    path('home/', home_view, name='home'),
    path('logout/', logout_view, name='logout'),

    # Users app — employees list and tenant preferences.
    path('', include('users.urls')),

    # Entity scaffolding — list + detail views for the Lite primary navigation.
    # Each app holds its own user-facing views.py + urls.py; mounted at root
    # so URLs read like /customers/, /assets/, /jobs/, etc.
    path('', include('crm.urls')),
    path('', include('maintenance.urls')),
    path('', include('service.urls')),

    # Django built-in admin — ServizDesk staff only (StaffUser authentication).
    path('admin/', admin.site.urls),

    # REST API — versioned, tenant-scoped, DRF-powered.
    # Source: Internal API Specification V1.
    path('api/v1/', include('api.urls')),

    # Internal API — SDP ↔ SDTA communication, key-authenticated.
    # Source: Internal API Specification V1.
    # Endpoint implementations are intentionally deferred in the current
    # stabilization phase (see infrastructure/internal_urls.py).
    path('internal/api/v1/', include('infrastructure.internal_urls')),
]
