"""User-facing URL routes for the maintenance app."""

from django.urls import path

from maintenance.views import assets_list_view, asset_detail_view


urlpatterns = [
    path('assets/', assets_list_view, name='assets'),
    path('assets/<uuid:pk>/', asset_detail_view, name='asset-detail'),
]
