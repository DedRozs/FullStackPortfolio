from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

User = get_user_model()

@pytest.mark.django_db
def test_create_blog_post():
    client = APIClient()
    test_user = User.objects.create_user(username="testuser", password="testpassword")
    client.force_authenticate(user=test_user)
    url = reverse("blogpost-list")
    data = {
        "title": "AI in Full-Stack Development",
        "content": "Exploring AI integrations in Django.",
        "author": test_user.id,
        "tags": "AI, Django",
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 201
    assert response.data["title"] == "AI in Full-Stack Development"
