from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie

from .views import (
    RegisterView,
    login_view,
    logout_view,
    check_user,
    check_superuser,
    user_appointments,
    password_reset_request,
    custom_password_reset_confirm,
    set_csrf,
    CookieTokenRefreshView  # Ensure this is imported
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('appointments/', user_appointments, name='user-appointments'),
    path('password-reset/', password_reset_request, name='password_reset_request'),
    path('reset/<uidb64>/<token>/', custom_password_reset_confirm, name='password_reset_confirm'),
    path('check-user/', check_user, name='check-user'),
    path('check-superuser/', check_superuser, name='check-superuser'),
    path('set-csrf/', ensure_csrf_cookie(set_csrf), name='set_csrf'),
    # Use your custom CookieTokenRefreshView here
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
]
