from django.urls import path
from .views import RegisterView, LoginView, update_tokens

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('update-tokens/<int:user_id>/', update_tokens, name='update-tokens'),
]