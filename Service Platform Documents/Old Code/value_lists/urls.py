from django.urls import path
from . import views

urlpatterns = [
    path("", views.ValueListListView.as_view(), name="value_list_list"),
    path("create/", views.ValueListCreateView.as_view(), name="value_list_create"),
    path("<slug:slug>/", views.ValueListDetailView.as_view(), name="value_list_detail"),
    path("<slug:slug>/edit/", views.ValueListUpdateView.as_view(), name="value_list_update"),
    path("<slug:slug>/item/add/", views.ValueItemCreateView.as_view(), name="value_item_create"),
    path("<slug:slug>/item/<int:pk>/edit/", views.ValueItemUpdateView.as_view(), name="value_item_update"),
    path("<slug:slug>/delete/", views.ValueListDeleteView.as_view(), name="value_list_delete"),
    path("<slug:slug>/item/<int:pk>/delete/", views.ValueItemDeleteView.as_view(), name="value_item_delete"),
]
