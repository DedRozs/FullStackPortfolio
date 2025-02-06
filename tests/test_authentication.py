from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

User = get_user_model()

@pytest.mark.django_db
def test_user_detail_view():
    client = APIClient()
    test_user = User.objects.create_user(username="testuser", password="testpassword")
    client.force_authenticate(user=test_user)
    url = reverse("user-detail", args=[test_user.id])
    response = client.get(url)
    assert response.status_code == 200
    assert response.data["username"] == "testuser"
