from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import *

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)

urlpatterns = [
    path("", home_view, name="home"),
    path("projects/", projects_view, name="projects"),
    path("contact/", contact_view, name="contact"),
    path("about/", about_view, name="about"),
    path('', include(router.urls)),
]
