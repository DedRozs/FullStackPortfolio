from django.contrib import admin
from django.urls import include, path, re_path

from apps.react_app.views import index as spa_index

urlpatterns = [
    path('admin/', admin.site.urls),
    # Blog (server-side rendered; must appear before the SPA catch-all)
    path('blog/', include('apps.blog.urls', namespace='blog')),
    path('markdownx/', include('markdownx.urls')),
    # REST API endpoints
    path('api/contact/', include('apps.contact.urls')),
    path('api/ai/', include('apps.ai_assistant.urls')),
    # Catch-all: serve the React SPA for every non-API route.
    # React Router handles client-side navigation.
    re_path(r'^.*$', spa_index, name='spa'),
]
