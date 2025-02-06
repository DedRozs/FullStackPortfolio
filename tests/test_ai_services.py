import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from ai_services.models import AIService

User = get_user_model()

@pytest.mark.django_db
def test_ai_service_creation():
    """Test AI service creation with authentication."""
    client = APIClient()

    test_user = User.objects.create_user(
        username="testuser",
        password="securepassword",
        email="testuser@example.com"  # Ensure unique email
    )

    client.force_authenticate(user=test_user)

    url = reverse("ai_service_create")
    data = {
        "name": "AI Chatbot",
        "description": "A chatbot powered by AI.",
        "owner": test_user.id  # Ensure this is set if required by the serializer
    }

    response = client.post(url, data, format="json")

    assert response.status_code == 201, response.data



@pytest.mark.django_db
def test_unauthenticated_ai_service_creation():
    """Ensure that AI service creation fails for unauthenticated users."""
    client = APIClient()

    url = reverse("ai_service_create")  
    data = {
        "name": "Unauthorized AI",
        "description": "This service should not be created."
    }

    response = client.post(url, data, format="json")

    assert response.status_code == 401  # Unauthorized


@pytest.mark.django_db
def test_retrieve_ai_services():
    """Test retrieving a list of AI services."""
    client = APIClient()

    test_user = User.objects.create_user(username="testuser", password="securepassword", email="testuser@example.com")
    client.force_authenticate(user=test_user)

    # Ensure objects are created with unique names
    AIService.objects.create(name="AI Service 1", description="Description 1", owner=test_user)
    AIService.objects.create(name="AI Service 2", description="Description 2", owner=test_user)

    # Check that objects were saved
    assert AIService.objects.count() == 2, f"Expected 2 AI services in DB, found {AIService.objects.count()}"

    url = reverse("ai_service_list")
    response = client.get(url)

    assert response.status_code == 200, response.data
    assert len(response.data) == 2, f"Expected 2 services, got {len(response.data)}"




@pytest.mark.django_db
def test_update_ai_service():
    """Test updating an AI service by the owner."""
    client = APIClient()

    test_user = User.objects.create_user(username="testuser", password="securepassword", email="testuser@example.com")
    client.force_authenticate(user=test_user)

    ai_service = AIService.objects.create(name="Old Name", description="Old Description", owner=test_user)

    url = reverse("ai_service_detail", kwargs={"pk": ai_service.id})
    data = {
        "name": "Updated AI Service",
        "description": "Updated Description",
        "owner": test_user.id  # Ensure owner field is included
    }

    response = client.put(url, data, format="json")

    assert response.status_code == 200, response.data



@pytest.mark.django_db
def test_unauthorized_update_ai_service():
    """Ensure that users cannot update an AI service they don't own."""
    client = APIClient()

    # Create two users
    owner_user = User.objects.create_user(username="owner", password="password", email="owner@example.com")
    another_user = User.objects.create_user(username="hacker", password="password", email="hacker@example.com")

    # Create a sample AI service
    ai_service = AIService.objects.create(name="Owner's AI", description="Owned by user1", owner=owner_user)

    # Authenticate another user (not the owner)
    client.force_authenticate(user=another_user)

    url = reverse("ai_service_detail", kwargs={"pk": ai_service.id})
    data = {
        "name": "Hacked AI Service",
        "description": "Unauthorized edit"
    }

    response = client.put(url, data, format="json")

    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}. Response: {response.data}"



@pytest.mark.django_db
def test_unauthorized_delete_ai_service():
    """Ensure that users cannot delete an AI service they don't own."""
    client = APIClient()

    # Create two users
    owner_user = User.objects.create_user(username="owner", password="password", email="owner@example.com")
    another_user = User.objects.create_user(username="hacker", password="password", email="hacker@example.com")

    # Create a sample AI service
    ai_service = AIService.objects.create(name="Owner's AI", description="Owned by user1", owner=owner_user)

    # Authenticate another user (not the owner)
    client.force_authenticate(user=another_user)

    url = reverse("ai_service_detail", kwargs={"pk": ai_service.id})
    response = client.delete(url)

    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"



@pytest.mark.django_db
def test_unauthorized_delete_ai_service():
    """Ensure that users cannot delete an AI service they don't own."""
    client = APIClient()

    # Create two users
    owner_user = User.objects.create_user(username="owner", password="password", email="user1@example.com")
    another_user = User.objects.create_user(username="hacker", password="password", email="user2@example.com")

    # Create a sample AI service
    ai_service = AIService.objects.create(name="Owner's AI", description="Owned by user1", owner=owner_user)

    # Authenticate another user
    client.force_authenticate(user=another_user)

    url = reverse("ai_service_detail", kwargs={"pk": ai_service.id})
    response = client.delete(url)

    assert response.status_code == 403  # Forbidden
    assert AIService.objects.filter(id=ai_service.id).exists()
