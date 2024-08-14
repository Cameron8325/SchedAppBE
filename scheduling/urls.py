from django.urls import path
from .views import (
    AppointmentListCreate, approve_appointment, deny_appointment,
    flag_appointment, mark_to_completion, AvailableDayListCreate,
    remove_available_days, check_superuser, set_availability, user_flag_appointment
)

urlpatterns = [
    path('appointments/', AppointmentListCreate.as_view(), name='appointments'),
    path('appointments/<int:pk>/approve/', approve_appointment, name='approve-appointment'),
    path('appointments/<int:pk>/deny/', deny_appointment, name='deny-appointment'),
    path('appointments/<int:pk>/flagged/', flag_appointment, name='flag-appointment'),
    path('appointments/<int:pk>/to_completion/', mark_to_completion, name='to-completion-appointment'),
    path('available-days/', AvailableDayListCreate.as_view(), name='available-days'),
    path('remove-availability/', remove_available_days, name='remove-availability'),
    path('check-superuser/', check_superuser, name='check-superuser'),
    path('set-availability/', set_availability, name='set-availability'),
    path('appointments/<int:pk>/flag/', user_flag_appointment, name='user-flag-appointment'),
]
