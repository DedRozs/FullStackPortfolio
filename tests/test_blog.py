import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from blog.models import BlogPost

User = get_user_model()

@pytest.mark.django_db
def test_create_blog_post():
    """Test creating a blog post with authentication."""
    client = APIClient()

    test_user = User.objects.create_user(
        username="testuser",
        password="securepassword",
        email="testuser@example.com"  # Ensure unique email
    )
    client.force_authenticate(user=test_user)

    url = reverse("blog_create")
    data = {
        "title": "My First Blog",
        "content": "This is my first blog post.",
        "author": test_user.id  # Ensure author is correctly assigned
    }

    response = client.post(url, data, format="json")

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_unauthenticated_blog_creation():
    """Ensure that blog post creation fails for unauthenticated users."""
    client = APIClient()

    url = reverse("blog_create")  
    data = {
        "title": "Unauthorized Blog",
        "content": "This post should not be created."
    }

    response = client.post(url, data, format="json")

    assert response.status_code == 401  # Unauthorized

@pytest.mark.django_db
def test_retrieve_blog_posts():
    """Test retrieving a list of blog posts."""
    client = APIClient()

    test_user = User.objects.create_user(username="testuser", password="securepassword", email="testuser@example.com")
    client.force_authenticate(user=test_user)

    # Ensure objects are created with unique titles
    BlogPost.objects.create(title="Post 1", content="Content 1", author=test_user)
    BlogPost.objects.create(title="Post 2", content="Content 2", author=test_user)

    # Check that objects were saved
    assert BlogPost.objects.count() == 2, f"Expected 2 blog posts in DB, found {BlogPost.objects.count()}"

    url = reverse("blog_list")
    response = client.get(url)

    assert response.status_code == 200, response.data
    assert len(response.data) == 2, f"Expected 2 blog posts, got {len(response.data)}"


@pytest.mark.django_db
def test_update_blog_post():
    """Test updating a blog post by the author."""
    client = APIClient()

    # Create test user and authenticate
    test_user = User.objects.create_user(username="testuser", password="securepassword", email="testuser@example.com")
    client.force_authenticate(user=test_user)

    # Create a sample blog post
    blog_post = BlogPost.objects.create(title="Old Title", content="Old Content", author=test_user)

    url = reverse("blog_detail", kwargs={"pk": blog_post.id})
    data = {
        "title": "Updated Title",
        "content": "Updated Content",
        "author": test_user.id  # Ensure the author field is passed if required
    }

    response = client.put(url, data, format="json")

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.data}"


@pytest.mark.django_db
def test_delete_blog_post():
    """Test deleting a blog post by the author."""
    client = APIClient()

    # Create test user and authenticate
    test_user = User.objects.create_user(
        username="testuser",
        password="securepassword",
        email="testuser@example.com"  # Ensure unique email
    )
    client.force_authenticate(user=test_user)

    # Create a sample blog post
    blog_post = BlogPost.objects.create(title="To be deleted", content="Delete me", author=test_user)

    url = reverse("blog_detail", kwargs={"pk": blog_post.id})
    response = client.delete(url)

    assert response.status_code == 204
    assert not BlogPost.objects.filter(id=blog_post.id).exists()
