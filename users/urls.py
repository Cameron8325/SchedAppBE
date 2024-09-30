from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('update-tokens/<int:user_id>/', views.update_tokens, name='update-tokens'),
    path('appointments/', views.user_appointments, name='user-appointments'),
    path('search/', views.search_users, name='search-users'),

    # Password reset URLs
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    
    # Custom password reset confirm view for handling React password reset
path('reset/<uidb64>/<token>/', views.custom_password_reset_confirm, name='password_reset_confirm'),
    
    # path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
    #     template_name="registration/password_reset_complete.html"
    # ), name="password_reset_complete"),
]
