from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed
from users.serializers import RegisterSerializer, LoginSerializer, LogoutSerializer
from django.contrib.auth import get_user_model


User = get_user_model()


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

            # Set refresh token in HttpOnly cookie
            cookie_max_age = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
            response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                secure=False,            # True in production (HTTPS)
                samesite="Lax",          # 'Strict' or 'Lax' depending on behavior you want
                max_age=cookie_max_age,
                path="/",  # cookie accessible for refresh endpoint
            )

            return response
        except AuthenticationFailed as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                
                cookie_max_age = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
                response = Response(payload, status=status.HTTP_200_OK)
                response.set_cookie(
                    "refresh_token",
                    value=str(new_refresh),
                    httponly=True,
                    secure=False,  # True in production
                    samesite="Lax",
                    max_age=cookie_max_age,
                    path="/",
                )
                return response

            return Response(payload, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Refresh token is invalid or expired."}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
