"""User-facing URL routes for the CRM app."""

from django.urls import path

from crm.views import customers_list_view, customer_detail_view


urlpatterns = [
    path('customers/', customers_list_view, name='customers'),
    path('customers/<uuid:pk>/', customer_detail_view, name='customer-detail'),
]
