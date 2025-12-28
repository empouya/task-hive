from django.urls import path
from .views import CommentCreateView, CommentDetailView

urlpatterns = [
    path('<int:task_id>/', CommentCreateView.as_view(), name='create-comment'),
    path('comments/<int:comment_id>/', CommentDetailView.as_view(), name='comment-detail'),
]