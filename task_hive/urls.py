"""
URL configuration for task_hive project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from common.views import TriggerErrorView, TriggerCrashView, ProtectedTestView, HealthCheckView
from teams.views import AcceptInvitationView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/teams/', include('teams.urls')),
    path('api/v1/projects/', include('projects.urls')),
    path('api/v1/tasks/', include('tasks.urls')),
    path('api/v1/comments/', include('comments.urls')),
    path('api/v1/invites/<uuid:token>/accept/', AcceptInvitationView.as_view(), name="invite-accept"),
    path('api/v1/invites/<int:team_id>/<int:invite_id>/', AcceptInvitationView.as_view(), name="invite-delete"),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('test-error/', TriggerErrorView.as_view()),
    path('test-crash/', TriggerCrashView.as_view()),
    path('test-protected/', ProtectedTestView.as_view()),
]
