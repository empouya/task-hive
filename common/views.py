from django.db import connections
from django.db.utils import OperationalError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from common.exceptions import BusinessLogicError

class TriggerErrorView(APIView):
    def get(self, request):
        # test mapping of custom exceptions
        raise BusinessLogicError("This is a test of the TaskHive error system.")

class TriggerCrashView(APIView):
    def get(self, request):
        # test (500) internal error logic
        return 1 / 0

class ProtectedTestView(APIView):
    # test auth config
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "If you see this, you are authenticated!"})

class HealthCheckView(APIView):
    """
    Endpoint to check if the API and Database are functional.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        health_status = {
            "status": "healthy",
            "components": {
                "django": "ok",
                "database": "unhealthy"
            }
        }
        
        try:
            db_conn = connections['default']
            db_conn.cursor()
            health_status["components"]["database"] = "ok"
        except OperationalError:
            health_status["status"] = "unhealthy"
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(health_status, status=status.HTTP_200_OK)