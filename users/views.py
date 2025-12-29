from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from users.serializers import RegisterSerializer

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
