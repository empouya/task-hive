import requests
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


class SocialAuthError(Exception):
    pass


def authenticate_social_user(*, provider, access_token):
    if provider == "google":
        profile = _fetch_google_profile(access_token)
    elif provider == "github":
        profile = _fetch_github_profile(access_token)
    else:
        raise SocialAuthError("Unsupported social provider.")

    email = profile["email"].lower()
    uid = str(profile["uid"])

    with transaction.atomic():
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"is_active": True},
        )

        SocialAccount.objects.update_or_create(
            provider=provider,
            uid=uid,
            defaults={
                "user": user,
                "extra_data": profile.get("extra_data", {}),
            },
        )

    refresh = RefreshToken.for_user(user)
    return user, refresh, {
        "access": str(refresh.access_token),
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }


def _fetch_google_profile(access_token):
    response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )

    if response.status_code != 200:
        raise SocialAuthError("Google token is invalid.")

    payload = response.json()
    email = payload.get("email")
    email_verified = payload.get("email_verified")

    if not email or not email_verified:
        raise SocialAuthError("Google account email must be verified.")

    return {
        "uid": payload["sub"],
        "email": email,
        "extra_data": payload,
    }


def _fetch_github_profile(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }

    user_response = requests.get(GITHUB_USER_URL, headers=headers, timeout=10)
    if user_response.status_code != 200:
        raise SocialAuthError("GitHub token is invalid.")

    emails_response = requests.get(GITHUB_EMAILS_URL, headers=headers, timeout=10)
    if emails_response.status_code != 200:
        raise SocialAuthError("GitHub email lookup failed.")

    emails = emails_response.json()
    primary_email = next(
        (
            item["email"]
            for item in emails
            if item.get("primary") and item.get("verified")
        ),
        None,
    )

    if not primary_email:
        raise SocialAuthError("GitHub account must have a verified primary email.")

    user_payload = user_response.json()

    return {
        "uid": user_payload["id"],
        "email": primary_email,
        "extra_data": user_payload,
    }