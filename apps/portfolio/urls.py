from django.urls import path
from apps.portfolio.views import *

urlpatterns = [
    path("", home_view, name="home"),
    path("about/", about_view, name="about"),
    path("projects/", projects_view, name="projects"),
    path("contact/", contact_view, name="contact"),
]
