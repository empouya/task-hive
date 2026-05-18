import pytest
from rest_framework import status


@pytest.mark.django_db
def test_metrics_endpoint_is_available(client):
    response = client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
    assert b"django_" in response.content