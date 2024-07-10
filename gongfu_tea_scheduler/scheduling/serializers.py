from rest_framework import serializers
from .models import Appointment, UnavailableDay
from users.serializers import UserSerializer  # Import the UserSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Include the full UserSerializer

    class Meta:
        model = Appointment
        fields = '__all__'

class UnavailableDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = UnavailableDay
        fields = '__all__'
