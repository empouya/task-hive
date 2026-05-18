import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from teams.models import Team, TeamMembership
from users.tokens import revoke_access_token

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_idempotency_replays_same_mutation_response(api_client):
    user = User.objects.create_user(email="idem@taskhive.com", password="pw")
    api_client.force_authenticate(user=user)

    response_1 = api_client.post(
        reverse("team-list-create"),
        {"name": "Idempotent Team"},
        HTTP_IDEMPOTENCY_KEY="11111111-1111-4111-8111-111111111111",
    )
    response_2 = api_client.post(
        reverse("team-list-create"),
        {"name": "Idempotent Team"},
        HTTP_IDEMPOTENCY_KEY="11111111-1111-4111-8111-111111111111",
    )

    assert response_1.status_code == status.HTTP_201_CREATED
    assert response_2.status_code == status.HTTP_201_CREATED
    assert response_2["Idempotency-Replayed"] == "true"
    assert Team.objects.filter(name="Idempotent Team").count() == 1


@pytest.mark.django_db
def test_idempotency_rejects_same_key_with_different_body(api_client):
    user = User.objects.create_user(email="idem-conflict@taskhive.com", password="pw")
    api_client.force_authenticate(user=user)

    api_client.post(
        reverse("team-list-create"),
        {"name": "First Team"},
        HTTP_IDEMPOTENCY_KEY="22222222-2222-4222-8222-222222222222",
    )
    response = api_client.post(
        reverse("team-list-create"),
        {"name": "Second Team"},
        HTTP_IDEMPOTENCY_KEY="22222222-2222-4222-8222-222222222222",
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["type"] == "https://taskhive.com/errors/idempotency-conflict"
    assert Team.objects.filter(name="Second Team").count() == 0


@pytest.mark.django_db
def test_revoked_access_token_is_rejected(api_client):
    user = User.objects.create_user(email="revoked@taskhive.com", password="password123")
    login_response = api_client.post(reverse("login"), {
        "email": "revoked@taskhive.com",
        "password": "password123",
    })
    access_token = login_response.data["access"]

    revoke_access_token(access_token)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    response = client.get(reverse("team-list-create"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_authenticated_throttle_eventually_limits_requests(api_client, settings):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"] = "2/min"
    cache.clear()

    user = User.objects.create_user(email="throttle@taskhive.com", password="pw")
    team = Team.objects.create(name="Throttle Team")
    TeamMembership.objects.create(user=user, team=team)
    api_client.force_authenticate(user=user)

    url = reverse("team-list-create")

    assert api_client.get(url).status_code == status.HTTP_200_OK
    assert api_client.get(url).status_code == status.HTTP_200_OK
    assert api_client.get(url).status_code == status.HTTP_429_TOO_MANY_REQUESTS