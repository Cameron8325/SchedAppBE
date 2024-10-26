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
    CookieTokenRefreshView,
    account_deletion_request,
    account_deletion_confirm,
    send_verification_email,
    verify_email,
    resend_verification_email,
    update_user
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('send-verification-email/', send_verification_email, name='send_verification_email'),
    path('resend-verification-email/', resend_verification_email, name='resend_verification_email'),
    path('verify/<uidb64>/<token>/', verify_email, name='verify_email'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('appointments/', user_appointments, name='user-appointments'),
    path('password-reset/', password_reset_request, name='password_reset_request'),
    path('reset/<uidb64>/<token>/', custom_password_reset_confirm, name='password_reset_confirm'),
    path('account-deletion-request/', account_deletion_request, name='account_deletion_request'),
    path('account-deletion-confirm/<uidb64>/<token>/', account_deletion_confirm, name='account_deletion_confirm'),
    path('check-user/', check_user, name='check-user'),
    path('check-superuser/', check_superuser, name='check-superuser'),
    path('set-csrf/', ensure_csrf_cookie(set_csrf), name='set_csrf'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('update/', update_user, name='update_user'),
]
