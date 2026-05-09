from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.backup_dashboard_view, name='backup_dashboard'),
    path('trigger/', views.trigger_backup_view, name='trigger_backup'),
    path('restore/<str:backup_id>/', views.restore_backup_view, name='restore_backup'),
    path('delete/<str:backup_id>/', views.delete_backup_view, name='delete_backup'),
    path('settings/update/', views.update_settings_view, name='update_backup_settings'),
]
