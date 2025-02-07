import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_user_registration():
    """Test if a new user can register successfully."""
    client = APIClient()
    url = reverse("register")
    data = {"username": "testuser", "password": "securepassword"}

    response = client.post(url, data, format="json")

    assert response.status_code == 200
    assert response.data["message"] == "User created successfully"
    assert User.objects.filter(username="testuser").exists()
