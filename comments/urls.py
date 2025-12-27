from django.urls import path
from .views import CommentCreateView

urlpatterns = [
    path('<int:task_id>/', CommentCreateView.as_view(), name='create-comment'),
]