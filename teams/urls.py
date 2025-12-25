from django.urls import path
from .views import TeamCreateListView

urlpatterns = [
    path('', TeamCreateListView.as_view(), name='team-list-create'),
]