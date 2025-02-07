from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, JWTLoginView

urlpatterns = [
    # User Registration
    path('register/', RegisterView.as_view(), name='register'),

    # Token Authentication Login
    path('login/', LoginView.as_view(), name='token_login'),

    # JWT Authentication Login
    path('jwt/login/', JWTLoginView.as_view(), name='jwt_login'),
    path('jwt/refresh/', TokenRefreshView.as_view(), name='jwt_refresh'),
]
