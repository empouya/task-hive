import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_health_check_endpoint(client):
    """
    Verify that the health check returns 200 and the correct status keys.
    """
    url = reverse('health-check')
    response = client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'healthy'
    assert 'database' in response.data['components']