import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_user_detail_view(client, test_user):
    client.login(username="testuser", password="testpassword")
    url = reverse("user-detail", args=[test_user.id])
    response = client.get(url)
    assert response.status_code == 200
    assert response.data["username"] == "testuser"
