from django.urls import path
from .views import CommentDetailView

urlpatterns = [
    path('<int:comment_id>/', CommentDetailView.as_view(), name='comment-detail'),
]