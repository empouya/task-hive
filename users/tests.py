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
        username="tester",
        password="password123"
    )
    url = reverse('me')

    api_client.force_authenticate(user=user)

    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['email'] == "tester@taskhive.com"
