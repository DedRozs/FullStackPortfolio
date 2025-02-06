import pytest
from django.urls import reverse
from portfolio_app.models import Project

@pytest.mark.django_db
def test_create_project(client, test_user):
    client.force_login(test_user)
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
    assert Project.objects.count() == 1
