import pytest
from django.urls import reverse
from rest_framework import status
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
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
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
    
    assert response.status_code == status.HTTP_200_OK
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
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(email="newuser@taskhive.com").exists()
