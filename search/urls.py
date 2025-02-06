from django.urls import path
from .views import AddTextToIndexView, SearchView

urlpatterns = [
    path("add/", AddTextToIndexView.as_view(), name="add_to_index"),
    path("search/", SearchView.as_view(), name="search"),
]
