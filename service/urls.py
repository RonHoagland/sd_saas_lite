"""User-facing URL routes for the service app."""

from django.urls import path

from service.views import (
    jobs_list_view, job_detail_view,
    requests_list_view, request_detail_view,
    schedule_view,
    quotes_list_view, quote_detail_view,
    invoices_list_view, invoice_detail_view,
    payments_list_view, payment_detail_view,
)


urlpatterns = [
    path('jobs/', jobs_list_view, name='jobs'),
    path('jobs/<uuid:pk>/', job_detail_view, name='job-detail'),

    path('requests/', requests_list_view, name='requests'),
    path('requests/<uuid:pk>/', request_detail_view, name='request-detail'),

    path('schedule/', schedule_view, name='schedule'),

    path('quotes/', quotes_list_view, name='quotes'),
    path('quotes/<uuid:pk>/', quote_detail_view, name='quote-detail'),

    path('invoices/', invoices_list_view, name='invoices'),
    path('invoices/<uuid:pk>/', invoice_detail_view, name='invoice-detail'),

    path('payments/', payments_list_view, name='payments'),
    path('payments/<uuid:pk>/', payment_detail_view, name='payment-detail'),
]
