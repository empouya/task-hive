from rest_framework.views import APIView

from common.api.exception_handlers import taskhive_exception_handler
from common.api.renderers import JSendJSONRenderer


class TaskHiveAPIView(APIView):
    renderer_classes = [JSendJSONRenderer]

    def get_exception_handler(self):
        return taskhive_exception_handler
