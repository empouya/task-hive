from django.urls import path
from .views import MeView, RegisterView, LoginView, SocialLoginView, RefreshTokenView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('social/<str:provider>/', SocialLoginView.as_view(), name='social-login'),
]