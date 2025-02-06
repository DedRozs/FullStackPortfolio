from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

User = get_user_model()

@pytest.mark.django_db
def test_ai_service_creation():
    client = APIClient()
    test_user = User.objects.create_user(username="testuser", password="testpassword")
    client.force_authenticate(user=test_user)
    url = reverse("aiservice-list")
    data = {
        "user": test_user.id,
        "service_type": "chatbot",
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 201
