from django.urls import path
from .views import RegisterView, LoginView, update_tokens, user_appointments, search_users

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('update-tokens/<int:user_id>/', update_tokens, name='update-tokens'),
    path('appointments/', user_appointments, name='user-appointments'),
    path('search/', search_users, name='search-users'),
]
