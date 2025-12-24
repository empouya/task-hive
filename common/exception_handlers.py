from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger('django.request')

def taskhive_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
        return Response({
            "error_code": "server_error",
            "message": "An unexpected error occurred on the server.",
            "details": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    data = {
        "error_code": getattr(exc, 'default_code', 'validation_error'),
        "message": response.data.get('detail', 'Validation failed'),
        "details": response.data
    }
    
    if isinstance(data['details'], dict):
        data['details'].pop('detail', None)

    response.data = data
    return response