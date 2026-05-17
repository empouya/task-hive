from uuid import uuid4


class RequestTraceIdMiddleware:
    """
    Attach a stable trace ID to each request and response.

    Clients may send X-Trace-ID. Otherwise the API generates req-<uuid>.
    """

    header_name = "HTTP_X_TRACE_ID"
    response_header_name = "X-Trace-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.trace_id = request.META.get(self.header_name) or f"req-{uuid4()}"
        response = self.get_response(request)
        response[self.response_header_name] = request.trace_id
        return response
