from django.urls import path
from .views import RegisterView, login_view, user_appointments, check_superuser, password_reset_request, custom_password_reset_confirm

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('appointments/', user_appointments, name='user-appointments'),
    path('password-reset/', password_reset_request, name='password_reset_request'),
    path('reset/<uidb64>/<token>/', custom_password_reset_confirm, name='password_reset_confirm'),
    path('check-superuser/', check_superuser, name='check-superuser'),
]
