import pytest
from django.urls import reverse
from blog.models import BlogPost

@pytest.mark.django_db
def test_create_blog_post(client, test_user):
    client.force_login(test_user)
    url = reverse("blogpost-list")
    data = {
        "title": "AI in Full-Stack Development",
        "content": "Exploring AI integrations in Django.",
        "author": test_user.id,
        "tags": "AI, Django",
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 201
    assert BlogPost.objects.count() == 1
