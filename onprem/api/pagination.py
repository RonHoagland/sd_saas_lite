# api/pagination.py
# Standard pagination for all SDTA API endpoints.

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    Default pagination: 25 items per page, max 100.

    Query params:
        ?page=2          — page number
        ?page_size=50    — items per page (max 100)
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargePagination(PageNumberPagination):
    """
    Large pagination for bulk-read endpoints: 100 items per page, max 500.
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500


class SmallPagination(PageNumberPagination):
    """
    Small pagination for nested/lightweight endpoints: 10 items per page, max 50.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
