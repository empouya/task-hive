import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache_between_tests(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    cache.clear()
    yield
    cache.clear()