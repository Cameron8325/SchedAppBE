from django.urls import path
from .views import update_tokens  # Import the update_tokens function

urlpatterns = [
    path('update-tokens/<int:user_id>/', update_tokens, name='update-tokens'),
]
