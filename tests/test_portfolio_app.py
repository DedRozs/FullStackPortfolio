from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

User = get_user_model()

@pytest.mark.django_db
def test_create_project():
    client = APIClient()
    test_user = User.objects.create_user(username="testuser", password="testpassword")
    client.force_authenticate(user=test_user)
    url = reverse("project-list")
    data = {
        "title": "AI Portfolio",
        "description": "An AI-powered full-stack portfolio",
        "technologies": "Django, AI, TailwindCSS",
        "github_link": "https://github.com/DedRozs/FullStackPortfolio",
        "completion_date": "2025-02-10",
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 201
    assert response.data["title"] == "AI Portfolio"
