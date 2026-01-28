"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.views.static import serve

from apps.blog.presentation.sitemaps import sitemaps

urlpatterns = [
    path('admin/', admin.site.urls),
    # API routes - Clean Architecture bounded contexts
    path('api/contact/', include('apps.contact.presentation.urls')),
    path('api/blog/', include('apps.blog.presentation.urls')),
    # SEO - Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

# Serve robots.txt from frontend build
urlpatterns += [
    path('robots.txt', serve, {
        'path': 'robots.txt',
        'document_root': settings.BASE_DIR / 'staticfiles' / 'frontend',
    }),
]

# Serve static files from frontend build (both dev and production)
# Must be before the SPA catch-all
urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve, {
        'document_root': settings.BASE_DIR / 'staticfiles' / 'frontend',
    }),
]

# Serve React app for all other routes (SPA catch-all) - must be last
urlpatterns += [
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='spa'),
]
