import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from search.models import SearchIndex

User = get_user_model()

@pytest.mark.django_db
def test_add_text_to_index():
    """Test adding text to FAISS search index."""
    client = APIClient()
    
    test_user = User.objects.create_user(
        username="testuser",
        password="securepassword",
        email="testuser@example.com"  # Ensure unique email
    )
    client.force_authenticate(user=test_user)

    url = reverse("add_to_index")
    data = {"text": "AI-powered search system"}

    response = client.post(url, data, format="json")

    assert response.status_code == 201
    assert SearchIndex.objects.count() == 1
