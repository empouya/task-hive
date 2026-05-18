import logging
from uuid import uuid4

from django.utils.text import slugify
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("django.request")


def _problem_type(code):
    return f"https://taskhive.com/errors/{slugify(str(code)) or 'error'}"


def _flatten_invalid_params(details, prefix=""):
    invalid_params = []

    if isinstance(details, dict):
        for field, value in details.items():
            name = f"{prefix}.{field}" if prefix else str(field)
            invalid_params.extend(_flatten_invalid_params(value, name))
        return invalid_params

    if isinstance(details, list):
        for item in details:
            if isinstance(item, (dict, list)):
                invalid_params.extend(_flatten_invalid_params(item, prefix))
            else:
                invalid_params.append({
                    "name": prefix or "non_field_errors",
                    "reason": str(item),
                })
        return invalid_params

    invalid_params.append({
        "name": prefix or "non_field_errors",
        "reason": str(details),
    })
    return invalid_params


def taskhive_exception_handler(exc, context):
    trace_id = getattr(context.get("request"), "trace_id", None) or f"req-{uuid4()}"
    response = exception_handler(exc, context)

    if response is None:
        logger.error("Unhandled API exception", exc_info=True, extra={"trace_id": trace_id})
        return Response(
            {
                "type": "https://taskhive.com/errors/server-error",
                "title": "Internal Server Error",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "An unexpected error occurred on the server.",
                "instance": context["request"].path,
                "trace_id": trace_id,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    error_code = getattr(exc, "default_code", "error")
    title = getattr(exc, "default_detail", response.status_text)

    problem = {
        "type": _problem_type(error_code),
        "title": str(title),
        "status": response.status_code,
        "detail": response.data.get("detail", response.status_text)
        if isinstance(response.data, dict)
        else response.status_text,
        "instance": context["request"].path,
        "trace_id": trace_id,
    }

    if isinstance(exc, ValidationError):
        problem["type"] = "https://taskhive.com/errors/validation-error"
        problem["title"] = "Invalid Request Parameters"
        problem["detail"] = "One or more request parameters failed validation."
        problem["invalid_params"] = _flatten_invalid_params(response.data)

    response.data = problem
    return response
