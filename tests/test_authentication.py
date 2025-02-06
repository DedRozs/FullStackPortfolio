import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

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


@pytest.mark.django_db
def test_user_login():
    """Test if a user can obtain a JWT token."""
    client = APIClient()
    
    # Create test user
    user = User.objects.create_user(username="testuser", password="securepassword")
    
    url = reverse("token_obtain")
    data = {"username": "testuser", "password": "securepassword"}
    
    response = client.post(url, data, format="json")
    
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_protected_route_requires_authentication():
    """Test that accessing a protected API requires authentication."""
    client = APIClient()
    url = reverse("project-list")  # Adjust this to match your API endpoint
    
    response = client.get(url)
    
    assert response.status_code == 401  # Unauthorized


@pytest.mark.django_db
def test_authenticated_access_to_protected_route():
    """Test that an authenticated user can access a protected API."""
    client = APIClient()
    
    # Create test user
    user = User.objects.create_user(username="testuser", password="securepassword")
    
    # Obtain JWT token
    token_url = reverse("token_obtain")
    token_response = client.post(token_url, {"username": "testuser", "password": "securepassword"}, format="json")
    
    assert "access" in token_response.data
    token = token_response.data["access"]
    
    # Authenticate client
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    
    # Access protected route
    url = reverse("project-list")  # Adjust this to match your API endpoint
    response = client.get(url)
    
    assert response.status_code == 200
