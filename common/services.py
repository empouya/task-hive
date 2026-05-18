from django.db import transaction


class BaseService:
    atomic = staticmethod(transaction.atomic)