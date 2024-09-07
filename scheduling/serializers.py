from rest_framework import serializers
from .models import Appointment, AvailableDay
from users.serializers import UserSerializer  # Import the UserSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Include the full UserSerializer
    status_display = serializers.SerializerMethodField()
    day_type_display = serializers.SerializerMethodField()
    reason = serializers.CharField(allow_blank=True, allow_null=True, required=False)


    class Meta:
        model = Appointment
        fields = '__all__'

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_day_type_display(self, obj):
        return obj.get_day_type_display()

class AvailableDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableDay
        fields = '__all__'
