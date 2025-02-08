import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.portfolio.models import Project

User = get_user_model()
