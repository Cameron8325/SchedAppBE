from rest_framework import serializers
from .models import Appointment, AvailableDay
from users.serializers import UserSerializer  # Import the UserSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    day_type_display = serializers.SerializerMethodField()

    walk_in_first_name = serializers.CharField(allow_null=True, required=False)
    walk_in_last_name = serializers.CharField(allow_null=True, required=False)
    walk_in_email = serializers.EmailField(allow_null=True, required=False)
    walk_in_phone = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = Appointment
        fields = [
            'id', 'date', 'day_type_display', 'status', 'status_display', 'spots_left',
            'walk_in_first_name', 'walk_in_last_name', 'walk_in_email', 'walk_in_phone'
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_day_type_display(self, obj):
        return obj.get_day_type_display()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request', None)

        if request and request.user.is_authenticated and (request.user.is_staff or 'admin' in request.path):
            # Send all fields for admin or when accessing the admin dashboard
            extra_fields = {
                'user': UserSerializer(instance.user).data if instance.user else None,
                'day_type': instance.day_type,
                'status': instance.status,
                'reason': instance.reason,
            }
            representation.update(extra_fields)

        if instance.status == 'flagged' and request and request.user == instance.user:
            # Include reason for flagged appointments only to the user who owns the appointment
            representation['reason'] = instance.reason

        return representation




class AvailableDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableDay
        fields = '__all__'
