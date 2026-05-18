from rest_framework.renderers import JSONRenderer


class JSendJSONRenderer(JSONRenderer):
    """
    Wrap successful V2 responses in the JSend success envelope.

    Error responses are handled by the V2 exception handler and should pass
    through unchanged as RFC 7807 Problem Details.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        if response is not None and response.status_code == 204:
            return super().render(data, accepted_media_type, renderer_context)

        if response is not None and 200 <= response.status_code < 300:
            data = {
                "status": "success",
                "data": data,
            }

        return super().render(data, accepted_media_type, renderer_context)
