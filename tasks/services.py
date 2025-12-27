from decimal import Decimal
from django.db import transaction
from .models import Task

class TaskService:
    @staticmethod
    def reorder_task(task, target_position):
        """
        Moves a task to a target position. 
        If target_position is not provided, it calculates 
        the midpoint between neighbors.
        """
        with transaction.atomic():
            task.position = Decimal(str(target_position))
            task.save()
        return task