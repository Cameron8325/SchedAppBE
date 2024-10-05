from django.urls import path
from . import views

urlpatterns = [
    path('appointments/', views.AppointmentListCreate.as_view(), name='appointments'),
    path('available-days/', views.AvailableDayListCreate.as_view(), name='available-days'),
]
