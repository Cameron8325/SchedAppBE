from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import Appointment, AvailableDay
from .serializers import AppointmentSerializer, AvailableDaySerializer
from .permissions import IsAdminOrReadOnly


class AppointmentListCreate(generics.ListCreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow anyone to view available appointments
            return [permissions.AllowAny()]
        # Only authenticated users can create appointments (POST)
        return [permissions.IsAuthenticated()]

def create(self, request, *args, **kwargs):
    try:
        date = request.data.get('date')
        user = request.user

        if not date:
            return Response({'error': 'Date is required'}, status=status.HTTP_400_BAD_REQUEST)

        parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
        existing_appointments_count = Appointment.objects.filter(date=parsed_date).count()

        if existing_appointments_count >= 4:
            return Response({'error': 'No slots left for this day'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the day type from AvailableDay
        try:
            available_day = AvailableDay.objects.get(date=parsed_date)
            day_type = available_day.type
        except AvailableDay.DoesNotExist:
            return Response({'error': 'This day is not available for appointments'}, status=status.HTTP_400_BAD_REQUEST)

        spots_left = 4 - existing_appointments_count

        walk_in_first_name = request.data.get('walk_in_first_name')
        walk_in_last_name = request.data.get('walk_in_last_name')
        walk_in_email = request.data.get('walk_in_email')
        walk_in_phone = request.data.get('walk_in_phone')

        if walk_in_first_name and walk_in_last_name and walk_in_email and walk_in_phone:
            # Only admins or superusers can create walk-in appointments
            if not user.is_superuser:
                return Response({'error': 'Unauthorized to create walk-in appointments'}, status=status.HTTP_403_FORBIDDEN)

            # Create appointment for walk-in
            appointment = Appointment.objects.create(
                walk_in_first_name=walk_in_first_name,
                walk_in_last_name=walk_in_last_name,
                walk_in_email=walk_in_email,
                walk_in_phone=walk_in_phone,
                date=parsed_date,
                day_type=day_type,
                status='pending',
                spots_left=spots_left
            )
        else:
            # Normal flow for registered users
            appointment = Appointment.objects.create(
                user=user,
                date=parsed_date,
                day_type=day_type,
                status='pending',
                spots_left=spots_left
            )

        send_mail(
            'Appointment Request',
            f'Your appointment on {appointment.date} ({appointment.get_day_type_display()}) is pending approval.',
            'your-email@gmail.com',
            [appointment.walk_in_email] if appointment.walk_in_email else [appointment.user.email],
            fail_silently=False,
        )

        serializer = self.get_serializer(appointment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        print("Error in create appointment:", str(e))
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AvailableDayListCreate(generics.ListCreateAPIView):
    queryset = AvailableDay.objects.all()
    serializer_class = AvailableDaySerializer
    permission_classes = [IsAdminOrReadOnly]  # Apply the custom permission class

    def perform_create(self, serializer):
        serializer.save()



