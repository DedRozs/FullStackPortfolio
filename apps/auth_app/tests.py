import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_register_user():
    client = APIClient()
    response = client.post("/api/auth/register/", {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "securepassword"
    })

    print(response.status_code, response.data)  # Debugging
    assert response.status_code == 201  # Ensure user is created
    assert "id" in response.data

@pytest.mark.django_db
def test_login_with_token():
    user = User.objects.create_user(username="testuser", password="securepassword")
    token, _ = Token.objects.get_or_create(user=user)

    client = APIClient()
    response = client.post("/api/auth/login/", {
        "username": "testuser",
        "password": "securepassword"
    })

    print(response.status_code, response.data)  # Debugging
    assert response.status_code == 200
    assert "token" in response.data
    assert response.data["token"] == token.key


@pytest.mark.django_db
def test_login_with_jwt():
    User.objects.create_user(username="testuser", password="securepassword")

    client = APIClient()
    response = client.post("/api/auth/jwt/login/", {
        "username": "testuser",
        "password": "securepassword"
    })

    print(response.status_code, response.data)  # Debugging
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data

@pytest.mark.django_db
def test_user_profile():
    user = User.objects.create_user(username="testuser", password="securepassword", role="admin")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/auth/me/")
    assert response.status_code == 200
    assert response.data["username"] == "testuser"