from django.urls import path
from .views import *


urlpatterns = [
    path("create/", AIServiceCreateView.as_view(), name="ai_service_create"),
    path("", AIServiceListView.as_view(), name="ai_service_list"),
    path("<int:pk>/", AIServiceDetailView.as_view(), name="ai_service_detail"),
]
