"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

# Initialize PyMySQL as MySQLdb replacement with version patch for Django 6.0
import pymysql
pymysql.install_as_MySQLdb()
# Patch version_info to satisfy Django 6.0's mysqlclient version check
pymysql.version_info = (2, 2, 1, 'final', 0)
# Also patch the MySQLdb module that Django actually checks
import sys
sys.modules['MySQLdb'].version_info = (2, 2, 1, 'final', 0)

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_asgi_application()
