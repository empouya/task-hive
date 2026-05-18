import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_success_responses_use_jsend_envelope(client):
    response = client.get(reverse("health-check"))
    payload = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert payload["status"] == "success"
    assert payload["data"]["status"] == "healthy"
    assert response["X-Trace-ID"].startswith("req-")


@pytest.mark.django_db
def test_errors_use_problem_details(client):
    response = client.get("/test-error/")
    payload = response.json()

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert payload["type"] == "https://taskhive.com/errors/business_logic_violation"
    assert payload["status"] == status.HTTP_403_FORBIDDEN
    assert payload["instance"] == "/test-error/"
    assert payload["trace_id"].startswith("req-")


@pytest.mark.django_db
def test_trace_id_accepts_client_header(client):
    response = client.get(
        reverse("health-check"),
        HTTP_X_TRACE_ID="req-test-trace",
    )
    payload = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response["X-Trace-ID"] == "req-test-trace"
    assert payload["data"]["status"] == "healthy"
