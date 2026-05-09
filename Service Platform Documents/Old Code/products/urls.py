from django.urls import path
from .views import (
    product_list_view,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView
)

urlpatterns = [
    path('', product_list_view, name='product_list'),
    path('new/', ProductCreateView.as_view(), name='product_create'),
    path('<uuid:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('<uuid:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('<uuid:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
]
