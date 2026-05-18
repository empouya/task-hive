from rest_framework import status
from rest_framework.exceptions import APIException


class TaskHiveException(APIException):
    """Base exception for Task-Hive domain errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A server error occurred."
    default_code = "error"


class BusinessLogicError(TaskHiveException):
    """Raised when a user tries to do something forbidden by business rules."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "This action is not allowed by business rules."
    default_code = "business_logic_violation"


class PermissionDeniedError(TaskHiveException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "permission_denied"


class NotFoundError(TaskHiveException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The requested resource was not found."
    default_code = "not_found"


class ConflictError(TaskHiveException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current resource state."
    default_code = "conflict"