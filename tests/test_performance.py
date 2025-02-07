import pytest
import time
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from blog.models import BlogPost

User = get_user_model()


@pytest.mark.django_db
def test_blog_list_performance():
    """Ensure the blog list API responds within acceptable time limits."""
    client = APIClient()

    user = User.objects.create_user(
        username="testuser", password="password", email="testuser@example.com"
    )
    client.force_authenticate(user=user)

    # Create test blog posts
    for i in range(50):
        BlogPost.objects.create(title=f"Post {i}", content="Test Content", author=user)

    url = reverse("blog_list")

    start_time = time.time()
    response = client.get(url)
    end_time = time.time()

    assert response.status_code == 200
    assert (
        end_time - start_time
    ) < 0.5, f"API took too long: {end_time - start_time} seconds"
