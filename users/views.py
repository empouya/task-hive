from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from .serializers import UserSerializer

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    # BasicAuthentication ensures a 401 is returned instead of 403 
    # when no credentials are provided.
    authentication_classes = [BasicAuthentication, SessionAuthentication]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)