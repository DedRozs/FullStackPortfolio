import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from search.models import SearchIndex
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_add_text_to_index():
    client = APIClient()
    test_user = User.objects.create_user(username="testuser", password="testpassword")
    client.force_authenticate(user=test_user)  # Authenticate user

    url = reverse("add_to_index")
    data = {"text": "AI-powered search system"}

    response = client.post(url, data, format="json")
    assert response.status_code == 201
    assert SearchIndex.objects.count() == 1
@pytest.mark.django_db
def test_search_query():
    client = APIClient()
    url = reverse("search") + "?query=AI"

    response = client.get(url)
    assert response.status_code == 200
    assert isinstance(response.data["results"], list)
