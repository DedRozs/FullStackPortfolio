"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
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

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()
