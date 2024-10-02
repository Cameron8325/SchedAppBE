from django.urls import path
from . import views

urlpatterns = [
    path('update-tokens/<int:user_id>/', views.update_tokens, name='update-tokens'),
    path('appointments/<int:pk>/approve/', views.approve_appointment, name='approve-appointment'),
    path('appointments/<int:pk>/deny/', views.deny_appointment, name='deny-appointment'),
    path('appointments/<int:pk>/to_completion/', views.mark_to_completion, name='to-completion-appointment'),
    path('set-availability/', views.set_availability, name='set-availability'),
    path('remove-availability/', views.remove_available_days, name='remove-availability'),
    path('search/', views.search_users, name='search-users'),
]
