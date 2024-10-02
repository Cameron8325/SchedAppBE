from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('appointments/', views.user_appointments, name='user-appointments'),
    # Password reset URLs
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    
    # Custom password reset confirm view for handling React password reset
    path('reset/<uidb64>/<token>/', views.custom_password_reset_confirm, name='password_reset_confirm'),
    
]
