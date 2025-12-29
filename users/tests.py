import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_me_endpoint_unauthorized(api_client):
    """Anonymous users should get 401."""
    url = reverse('me')
    response = api_client.get(url)
    assert response.status_code == 401
    assert response.data['error_code'] == 'not_authenticated'

@pytest.mark.django_db
def test_me_endpoint_authorized(api_client):
    """Logged in users should get their data."""
    user = User.objects.create_user(
        email="tester@taskhive.com",
        password="password123"
    )
    url = reverse('me')

    api_client.force_authenticate(user=user)

    response = api_client.get(url)
    
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
    User.objects.create_user(
        email="tester@taskhive.com",
        password="password123"
    )

    url = reverse('login')

    response = api_client.post(url, {
        "email": "tester@taskhive.com",
        "password": "password123",
    })

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data

@pytest.mark.django_db
def test_login_fail(api_client):
    url = reverse('login')

    response = api_client.post(url, {
        "email": "wrong@taskhive.com",
        "password": "wrongpass",
    })

    # TODO: it should return 401 status code
    assert response.status_code == 400
    assert response.data["error_code"] == "invalid"
