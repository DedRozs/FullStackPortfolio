import pytest
from django.urls import reverse
from ai_services.models import AIService

@pytest.mark.django_db
def test_ai_service_creation(client, test_user):
    client.force_login(test_user)
    url = reverse("aiservice-list")
    data = {
        "user": test_user.id,
        "service_type": "chatbot",
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 201
    assert AIService.objects.count() == 1
