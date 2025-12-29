import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_auth_me_unauthorized(api_client):
    # API call
    url = reverse('me')
    response = api_client.get(url)

    # Test
    assert response.status_code == 401
    assert response.data['error_code'] == 'not_authenticated'

@pytest.mark.django_db
def test_auth_me_authorized(api_client):
    # Setup
    user = User.objects.create_user(email="tester@taskhive.com", password="password123")
    api_client.force_authenticate(user=user)

    # API call
    url = reverse('me')
    response = api_client.get(url)
    
    # Test
    assert response.status_code == 200
    assert response.data['email'] == "tester@taskhive.com"

@pytest.mark.django_db
def test_register_user(api_client):
    # API call
    url = reverse('register')
    response = api_client.post(url, {
        "email": "newuser@taskhive.com",
        "password": "StrongPass123",
        "password_confirm": "StrongPass123",
    })

    # Test
    assert response.status_code == 201
    assert User.objects.filter(email="newuser@taskhive.com").exists()


@pytest.mark.django_db
def test_login_success(api_client):
    # Setup
    User.objects.create_user(
        email="tester@taskhive.com",
        password="password123"
    )

    # API call
    url = reverse('login')
    response = api_client.post(url, {
        "email": "tester@taskhive.com",
        "password": "password123",
    })

    # Test
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data

@pytest.mark.django_db
def test_login_fail(api_client):
    # API call
    url = reverse('login')
    response = api_client.post(url, {
        "email": "wrong@taskhive.com",
        "password": "wrongpass",
    })

    # Test
    # TODO: it should return 401 status code
    assert response.status_code == 400
    assert response.data["error_code"] == "invalid"

@pytest.mark.django_db
def test_token_refresh_returns_new_access(api_client):
    # Setup
    User.objects.create_user(
        email="tester@taskhive.com",
        password="password123"
    )

    # API call
    login_url = reverse('login')
    login_response = api_client.post(login_url, {
        "email": "tester@taskhive.com",
        "password": "password123",
    })

    refresh_url = reverse('token-refresh')
    refresh_token = login_response.data["refresh"]

    response = api_client.post(refresh_url, {
        "refresh": refresh_token
    })

    # Test
    assert response.status_code == 200
    assert "access" in response.data

@pytest.mark.django_db
def test_logout_blacklists_refresh_token(api_client):
    # Setup
    User.objects.create_user(
        email="tester@taskhive.com",
        password="password123"
    )

    # API call
    login_url = reverse('login')
    logout_url = reverse('logout')
    refresh_url = reverse('token-refresh')

    login_response = api_client.post(login_url, {
        "email": "tester@taskhive.com",
        "password": "password123",
    })

    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
    )

    logout_response = api_client.post(logout_url, {
        "refresh": login_response.data["refresh"]
    })

    # Test (success)
    assert logout_response.status_code == 204

    # Test (Refresh should fail)
    refresh_response = api_client.post(refresh_url, {
        "refresh": login_response.data["refresh"]
    })

    assert refresh_response.status_code == 401

@pytest.mark.django_db
class TestRegistrationHarden:
    def test_register_password_mismatch(self, api_client):
        """Register should fail if password_confirm doesn't match."""
        url = reverse('register')
        response = api_client.post(url, {
            "email": "fail@taskhive.com",
            "password": "StrongPass123",
            "password_confirm": "WrongPass123",
        })
        assert response.status_code == 400
        assert "password" in str(response.data).lower()

    def test_register_duplicate_email(self, api_client):
        """Should not allow two users with the same email."""
        User.objects.create_user(email="duplicate@taskhive.com", password="password123")
        url = reverse('register')
        response = api_client.post(url, {
            "email": "duplicate@taskhive.com",
            "password": "AnotherPass123",
            "password_confirm": "AnotherPass123",
        })
        assert response.status_code == 400

@pytest.mark.django_db
class TestTokenHarden:
    def test_refresh_token_invalid(self, api_client):
        """Sending a junk string as a refresh token should fail."""
        url = reverse('token-refresh')
        response = api_client.post(url, {"refresh": "not-a-real-token"})
        assert response.status_code == 401

    def test_logout_without_token(self, api_client):
        """Logout should fail if no refresh token is provided."""
        user = User.objects.create_user(email="logout@taskhive.com", password="password123")
        api_client.force_authenticate(user=user)
        url = reverse('logout')
        response = api_client.post(url, {})
        assert response.status_code == 400
