import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_health_check_endpoint(client):
    response = client.get(reverse("health-check"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "healthy"
    assert "database" in response.data["components"]