from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import AIServiceViewSet

router = DefaultRouter()
router.register(r'aiservices', AIServiceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
