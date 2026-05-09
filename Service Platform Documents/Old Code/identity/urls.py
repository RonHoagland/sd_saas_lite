from django.urls import path
from . import views

urlpatterns = [
    path("users/", views.user_list_view, name="user_list"),
    path("users/export/", views.user_export_view, name="user_export"),
    path("profile/", views.my_profile_view, name="my_profile"),
    path("users/add/", views.user_create_view, name="user_create"),
    path("users/<int:pk>/", views.user_detail_view, name="user_detail"),
    path("users/<int:pk>/edit/", views.user_edit_view, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete_view, name="user_delete"),
    path("roles/", views.role_list_view, name="role_list"),
    path("roles/create/", views.role_create_view, name="role_create"),
    path("users/<int:user_id>/roles/<str:role_id>/remove/", views.role_delete_confirm_view, name="role_delete_confirm"),
    path("roles/<str:pk>/delete/", views.role_delete_view, name="role_delete"),
]
