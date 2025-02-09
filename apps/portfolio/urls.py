from django.urls import path
from apps.portfolio.views import *

urlpatterns = [
    path("", home_view, name="home"),
]
