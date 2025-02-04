import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
class TestAuthentication:

    def setup_method(self):
        """Setup method to initialize test client and create test user."""
        self.client = APIClient()
        self.test_user = User.objects.create_user(username="testuser", password="securepass", role="user")

    def test_register_user(self):
        """Test user registration endpoint."""
        response = self.client.post('/auth/register/', {
            'username': 'newuser',
            'password': 'newsecurepass',
            'role': 'user'
        }, format='json')
        assert response.status_code == 200
        assert response.data['message'] == 'User created successfully'

    def test_register_duplicate_user(self):
        """Test that duplicate user registration fails."""
        User.objects.create_user(username="duplicateuser", password="testpass")
        response = self.client.post('/auth/register/', {
            'username': 'duplicateuser',
            'password': 'testpass'
        }, format='json')
        assert response.status_code == 400
        assert 'User already exists' in response.data['error']

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post('/auth/login/', {
            'username': 'testuser',
            'password': 'securepass'
        }, format='json')
        assert response.status_code == 200
        assert 'token' in response.data
        assert response.data['role'] == 'user'

    def test_login_failure(self):
        """Test login with incorrect credentials."""
        response = self.client.post('/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        }, format='json')
        assert response.status_code == 401
        assert 'error' in response.data

    def test_logout(self):
        """Test user logout."""
        login_response = self.client.post('/auth/login/', {
            'username': 'testuser',
            'password': 'securepass'
        }, format='json')
        token = login_response.data['token']

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.post('/auth/logout/')

        assert response.status_code == 200
        assert response.data['message'] == 'Logged out successfully'
