from django.urls import path
from .views import AppointmentListCreate, approve_appointment, UnavailableDayListCreate, deny_appointment, check_superuser

urlpatterns = [
    path('appointments/', AppointmentListCreate.as_view(), name='appointments'),
    path('appointments/<int:pk>/approve/', approve_appointment, name='approve-appointment'),
    path('appointments/<int:pk>/deny/', deny_appointment, name='deny-appointment'),
    path('unavailable-days/', UnavailableDayListCreate.as_view(), name='unavailable-days'),
    path('check-superuser/', check_superuser, name='check-superuser'),
]
