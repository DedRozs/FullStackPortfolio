from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework.throttling import AnonRateThrottle
from dj_rest_auth.views import LoginView

from apps.react_app.views import index as spa_index


class LoginRateThrottle(AnonRateThrottle):
    rate = '10/hour'


LoginView.throttle_classes = [LoginRateThrottle]

urlpatterns = [
    path('admin/', admin.site.urls),
    # Blog RSS feed (server-side; must appear before the SPA catch-all)
    path('blog/', include('apps.blog.urls', namespace='blog')),
    path('markdownx/', include('markdownx.urls')),
    # REST API endpoints
    path('api/blog/', include('apps.blog.api_urls', namespace='blog_api')),
    path('api/contact/', include('apps.contact.urls')),
    path('api/ai/', include('apps.ai_assistant.urls')),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/portal/', include('apps.client_portal.api_urls')),
    path('api/dashboard/', include('apps.ops_dashboard.api_urls')),
    # Catch-all: serve the React SPA for every non-API route.
    # React Router handles client-side navigation.
    re_path(r'^.*$', spa_index, name='spa'),
]
