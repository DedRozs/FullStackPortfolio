import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.portfolio.models import Project

User = get_user_model()


@pytest.mark.django_db
def test_get_projects_unauthenticated():
    client = APIClient()
    response = client.get("/api/projects/")  # Ensure URL matches core/urls.py
    print(response.status_code, response.data)  # Debugging
    assert response.status_code == 200  # Expect success

@pytest.mark.django_db
def test_get_projects_authenticated():
    user = User.objects.create_user(username="testuser", password="securepassword")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/projects/")
    print(response.status_code, response.data)  # Debugging
    assert response.status_code == 200


@pytest.mark.django_db
def test_create_project():
    user = User.objects.create_user(
        username="testadmin", 
        password="securepassword", 
        is_superuser=True, 
        is_staff=True,
        role='admin'
    )
    client = APIClient()
    client.force_authenticate(user=user)

    print(f"Staff:{user.is_staff}\nSuper User:{user.is_superuser}\nRole:{user.role}")  # Debugging

    response = client.post("/api/projects/", {
        "title": "New Project",
        "description": "A test project",
        "technologies": "Python, Django",
        "github_link": "https://github.com/example/repo"
    })

    print(response.status_code, response.data)  # Debug output
    assert response.status_code == 201  # Ensure project is created

