import pytest
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
def test_google_social_login_creates_user_and_returns_tokens(api_client, monkeypatch):
    def fake_authenticate_social_user(*, provider, access_token):
        user = User.objects.create_user(email="google@taskhive.com", password=None)
        SocialAccount.objects.create(user=user, provider=provider, uid="google-123")
        refresh = RefreshToken.for_user(user)
        return user, refresh, {
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
            },
        }

    monkeypatch.setattr("users.views.authenticate_social_user", fake_authenticate_social_user)

    response = api_client.post(reverse("social-login", kwargs={"provider": "google"}), {
        "access_token": "valid-google-token",
    })

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert response.data["user"]["email"] == "google@taskhive.com"
    assert "refresh_token" in response.cookies
    assert SocialAccount.objects.filter(provider="google", uid="google-123").exists()


@pytest.mark.django_db
def test_github_social_login_links_existing_user(api_client, monkeypatch):
    existing_user = User.objects.create_user(email="dev@taskhive.com", password="password123")

    def fake_authenticate_social_user(*, provider, access_token):
        SocialAccount.objects.update_or_create(
            user=existing_user,
            provider=provider,
            uid="github-123",
        )
        refresh = RefreshToken.for_user(existing_user)
        return existing_user, refresh, {
            "access": str(refresh.access_token),
            "user": {
                "id": existing_user.id,
                "email": existing_user.email,
            },
        }

    monkeypatch.setattr("users.views.authenticate_social_user", fake_authenticate_social_user)

    response = api_client.post(reverse("social-login", kwargs={"provider": "github"}), {
        "access_token": "valid-github-token",
    })

    assert response.status_code == status.HTTP_200_OK
    assert User.objects.filter(email="dev@taskhive.com").count() == 1
    assert SocialAccount.objects.filter(user=existing_user, provider="github").exists()


@pytest.mark.django_db
def test_social_login_requires_access_token(api_client):
    response = api_client.post(reverse("social-login", kwargs={"provider": "google"}), {})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["type"] == "https://taskhive.com/errors/validation-error"


@pytest.mark.django_db
def test_social_login_rejects_unknown_provider(api_client):
    response = api_client.post(reverse("social-login", kwargs={"provider": "facebook"}), {
        "access_token": "token",
    })

    assert response.status_code == status.HTTP_404_NOT_FOUND