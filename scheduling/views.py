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
            user = request.user  # Automatically assign the authenticated user

            if not date:
                return Response({'error': 'Date is required'}, status=status.HTTP_400_BAD_REQUEST)

            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
            existing_appointments_count = Appointment.objects.filter(date=parsed_date).count()

            if existing_appointments_count >= 4:
                return Response({'error': 'No slots left for this day'}, status=status.HTTP_400_BAD_REQUEST)

            # Get the day type from the AvailableDay model
            try:
                available_day = AvailableDay.objects.get(date=parsed_date)
                day_type = available_day.type
            except AvailableDay.DoesNotExist:
                return Response({'error': 'This day is not available for appointments'}, status=status.HTTP_400_BAD_REQUEST)

            spots_left = 4 - existing_appointments_count

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
                [appointment.user.email],
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

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def flag_appointment(request, pk):
    try:
        user = request.user
        reason = request.data.get('reason', '').strip()

        if user.is_staff or user.is_superuser:
            # Admin can flag any appointment
            appointment = Appointment.objects.get(pk=pk)
            if not reason:
                return Response({'error': 'Reason for flagging is required'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Regular user can only flag their own appointment
            appointment = Appointment.objects.get(pk=pk, user=user)
            if not reason:
                return Response({'error': 'Reason for flagging is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Update appointment status and reason
        appointment.status = 'flagged'
        appointment.reason = reason
        appointment.save()

        # Send notification emails
        if user.is_staff or user.is_superuser:
            # Notify the appointment's user
            send_mail(
                'Appointment Flagged by Admin',
                f'Your appointment on {appointment.date} has been flagged by an administrator for the following reason:\n\n{reason}',
                'admin@example.com',
                [appointment.user.email],
                fail_silently=False,
            )
        else:
            # Notify the admins
            admin_emails = [admin.email for admin in User.objects.filter(is_staff=True)]
            send_mail(
                f'Appointment Flagged by User {user.username}',
                f'User {user.username} has flagged their appointment on {appointment.date}.\n\nReason:\n{reason}',
                'no-reply@example.com',
                admin_emails,
                fail_silently=False,
            )

        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Appointment.DoesNotExist:
        return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

