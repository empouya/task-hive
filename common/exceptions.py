from rest_framework.exceptions import APIException
from rest_framework import status

class TaskHiveException(APIException):
    """Base Exception for TaskHive"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A server error occurred."
    default_code = "error"

class BusinessLogicError(TaskHiveException):
    """Thrown when a user tries to do something forbidden by business rules"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "This action is not allowed by business rules."
    default_code = "business_logic_violation"