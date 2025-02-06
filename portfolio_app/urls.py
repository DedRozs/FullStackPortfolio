from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import *

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)

urlpatterns = [
    path("", home_view, name="home"),
    path('', include(router.urls)),
]
