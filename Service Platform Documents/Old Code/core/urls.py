from django.urls import path, include
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("admin-area/", views.admin_home_view, name="admin_home"),
    path("preferences/", views.preference_list_view, name="preference_list"),
    path("preferences/<uuid:pk>/", views.preference_update_view, name="preference_update"),
    path("identity/", include("identity.urls")),
    path("backup/", include("backup.urls")),
    path("audit/", include("audit.urls")),
    path("value-lists/", include("value_lists.urls")),
]
