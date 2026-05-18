from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from users.tokens import revoke_access_token, revoke_refresh_token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed
from users.serializers import RegisterSerializer, LoginSerializer, SocialLoginSerializer
from users.social_auth import SocialAuthError, authenticate_social_user
from django.contrib.auth import get_user_model


User = get_user_model()

def set_refresh_cookie(response, refresh):
    cookie_max_age = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
    response.set_cookie(
        key="refresh_token",
        value=str(refresh),
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=cookie_max_age,
        path="/",
    )
    return response

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    # BasicAuthentication ensures a 401 is returned instead of 403 
    # when no credentials are provided.
    authentication_classes = [BasicAuthentication, SessionAuthentication]

    def get(self, request):
        serializer = RegisterSerializer(request.user)
        return Response(serializer.data)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"id": user.id, "email": user.email},
            status=status.HTTP_201_CREATED,
        )

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated = serializer.validated_data
            refresh = validated[0]
            payload = validated[1]
            response = Response(payload, status=status.HTTP_200_OK)

            set_refresh_cookie(response, refresh)

            return response
        except AuthenticationFailed as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SocialLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, provider):
        if provider not in {"google", "github"}:
            return Response({"detail": "Unsupported social provider."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user, refresh, payload = authenticate_social_user(
                provider=provider,
                access_token=serializer.validated_data["access_token"],
            )
        except SocialAuthError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response(payload, status=status.HTTP_200_OK)
        set_refresh_cookie(response, refresh)
        return response


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)
            user = User.objects.get(id=refresh["user_id"])

            payload = {
                    "access": str(new_access),
            }

            # If ROTATE_REFRESH_TOKENS is True, SimpleJWT issues a new refresh token on rotation.
            if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False):
                new_refresh = refresh
                user_id = refresh["user_id"]
                user = User.objects.get(id=refresh["user_id"])
                new_refresh = RefreshToken.for_user(user)
                
                # Blacklist old token (if blacklist app enabled)
                try:
                    refresh.blacklist()
                except Exception:
                    pass
                
                response = Response(payload, status=status.HTTP_200_OK)
                set_refresh_cookie(response, new_refresh)
                return response

            return Response(payload, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Refresh token is invalid or expired."}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        auth_header = request.headers.get("Authorization", "")

        if not refresh_token and not auth_header.startswith("Bearer "):
            return Response({"error": "Token is not provided"}, status=status.HTTP_400_BAD_REQUEST)

        resp = Response(status=status.HTTP_204_NO_CONTENT)
        resp.delete_cookie("refresh_token", path="/")

        if auth_header.startswith("Bearer "):
            try:
                revoke_access_token(auth_header.split(" ", 1)[1])
            except Exception:
                pass

        if refresh_token:
            try:
                revoke_refresh_token(refresh_token)
            except Exception:
                pass

        return resp