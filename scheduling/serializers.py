from rest_framework import serializers
from .models import Appointment, AvailableDay
from users.serializers import UserSerializer  # Import the UserSerializer

from rest_framework import serializers
from .models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    day_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = ['id', 'date', 'day_type_display', 'status_display', 'spots_left']

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_day_type_display(self, obj):
        return obj.get_day_type_display()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request', None)
        
        if instance.status == 'flagged' and request:
            user = request.user
            if user.is_authenticated and (user == instance.user or user.is_staff):
                representation['reason'] = instance.reason
                
        return representation


class AvailableDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableDay
        fields = '__all__'
