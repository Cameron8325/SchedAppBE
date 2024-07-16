from django.urls import path
from .views import AppointmentListCreate, approve_appointment, UnavailableDayListCreate, deny_appointment, remove_unavailable_day, check_superuser

urlpatterns = [
    path('appointments/', AppointmentListCreate.as_view(), name='appointments'),
    path('appointments/<int:pk>/approve/', approve_appointment, name='approve-appointment'),
    path('appointments/<int:pk>/deny/', deny_appointment, name='deny-appointment'),
    path('unavailable-days/', UnavailableDayListCreate.as_view(), name='unavailable-days'),
    path('unavailable-days/<int:pk>/', remove_unavailable_day, name='remove-unavailable-day'),
    path('check-superuser/', check_superuser, name='check-superuser'),
]

