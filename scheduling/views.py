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
            return [permissions.AllowAny()]  # Allow anyone to view appointments
        return [permissions.IsAuthenticated()]  # Only authenticated users can create appointments

    def create(self, request, *args, **kwargs):
        try:
            # Parse date and user information
            date = request.data.get('date')
            if not date:
                return Response({'error': 'Date is required'}, status=status.HTTP_400_BAD_REQUEST)

            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
            existing_appointments_count = Appointment.objects.filter(date=parsed_date).count()

            # Check if there are available slots
            if existing_appointments_count >= 4:
                return Response({'error': 'No slots left for this day'}, status=status.HTTP_400_BAD_REQUEST)

            # Get the available day type
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

            # Walk-in appointment logic
            if walk_in_first_name and walk_in_last_name and walk_in_email and walk_in_phone:
                if not request.user.is_superuser:
                    return Response({'error': 'Unauthorized to create walk-in appointments'}, status=status.HTTP_403_FORBIDDEN)

                # Create a walk-in appointment with null user
                appointment = Appointment.objects.create(
                    walk_in_first_name=walk_in_first_name,
                    walk_in_last_name=walk_in_last_name,
                    walk_in_email=walk_in_email,
                    walk_in_phone=walk_in_phone,
                    date=parsed_date,
                    day_type=day_type,
                    status='pending',
                    spots_left=spots_left,
                    user=None  # Explicitly set user to None for walk-ins
                )
            else:
                # Regular appointment creation for logged-in users
                user = request.user
                appointment = Appointment.objects.create(
                    user=user,
                    date=parsed_date,
                    day_type=day_type,
                    status='pending',
                    spots_left=spots_left
                )

            # Send confirmation email
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
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class AvailableDayListCreate(generics.ListCreateAPIView):
    queryset = AvailableDay.objects.all()
    serializer_class = AvailableDaySerializer

    def get(self, request, *args, **kwargs):
        available_days = AvailableDay.objects.all()
        updated_days = []

        for available_day in available_days:
            # Fetch the appointments for this specific date
            appointments_for_day = Appointment.objects.filter(date=available_day.date)

            # Serialize appointments using the AppointmentSerializer
            serialized_appointments = AppointmentSerializer(appointments_for_day, many=True).data

            # Calculate spots left based on the number of appointments
            spots_left = max(4 - appointments_for_day.count(), 0)

            # Return the necessary data, including serialized appointments
            available_day_data = {
                "date": available_day.date,
                "type": available_day.type,
                "spots_left": spots_left,
                "appointments": serialized_appointments,  # Include serialized appointments
            }
            updated_days.append(available_day_data)

        return Response(updated_days)

