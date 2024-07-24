from rest_framework import generics, status, permissions
from rest_framework.response import Response
from django.core.mail import send_mail
from .models import Appointment, UnavailableDay
from .serializers import AppointmentSerializer, UnavailableDaySerializer
from rest_framework.decorators import api_view, permission_classes
from datetime import datetime
from .permissions import IsAdminOrReadOnly  # Import the custom permission

class AppointmentListCreate(generics.ListCreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            date = request.data.get('date')
            user_id = request.data.get('user')
            
            if not date or not user_id:
                return Response({'error': 'Date and user are required'}, status=status.HTTP_400_BAD_REQUEST)
            
            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
            existing_appointments_count = Appointment.objects.filter(date=parsed_date).count()
            
            if existing_appointments_count >= 4:
                return Response({'error': 'No slots left for this day'}, status=status.HTTP_400_BAD_REQUEST)
            
            spots_left = 4 - existing_appointments_count

            appointment = Appointment.objects.create(
                user_id=user_id,
                date=parsed_date,
                status='pending',
                spots_left=spots_left
            )
            
            send_mail(
                'Appointment Request',
                f'Your appointment on {appointment.date} is pending approval.',
                'your-email@gmail.com',
                [appointment.user.email],
                fail_silently=False,
            )

            serializer = self.get_serializer(appointment)
            response_data = serializer.data
            response_data['spots_left'] = spots_left

            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print("Error in create appointment:", str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def approve_appointment(request, pk):
    try:
        appointment = Appointment.objects.get(pk=pk)
        appointment.status = 'confirmed'
        appointment.save()
        send_mail(
            'Appointment Confirmed',
            f'Your appointment on {appointment.date} has been confirmed.',
            'your-email@gmail.com',
            [appointment.user.email],
            fail_silently=False,
        )
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Appointment.DoesNotExist:
        return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def deny_appointment(request, pk):
    try:
        appointment = Appointment.objects.get(pk=pk)
        date = appointment.date
        appointment.delete()
        
        # Update the spots left
        existing_appointments_count = Appointment.objects.filter(date=date).count()
        spots_left = 4 - existing_appointments_count
        
        # Update remaining appointments' spots_left
        Appointment.objects.filter(date=date).update(spots_left=spots_left)

        send_mail(
            'Appointment Denied',
            f'Your appointment on {date} has been denied.',
            'your-email@gmail.com',
            [appointment.user.email],
            fail_silently=False,
        )
        
        return Response({'message': 'Appointment denied'}, status=status.HTTP_200_OK)
    except Appointment.DoesNotExist:
        return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def flag_appointment(request, pk):
    try:
        appointment = Appointment.objects.get(pk=pk)
        appointment.status = 'flagged'
        appointment.save()
        send_mail(
            'Appointment Flagged',
            f'Your appointment on {appointment.date} has been flagged for review.',
            'your-email@gmail.com',
            [appointment.user.email],
            fail_silently=False,
        )
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Appointment.DoesNotExist:
        return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def mark_to_completion(request, pk):
    try:
        appointment = Appointment.objects.get(pk=pk)
        appointment.status = 'to_completion'
        appointment.save()
        send_mail(
            'Appointment Completed',
            f'Your appointment on {appointment.date} has been marked as completed.',
            'your-email@gmail.com',
            [appointment.user.email],
            fail_silently=False,
        )
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Appointment.DoesNotExist:
        return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

class UnavailableDayListCreate(generics.ListCreateAPIView):
    queryset = UnavailableDay.objects.all()
    serializer_class = UnavailableDaySerializer
    permission_classes = [IsAdminOrReadOnly]  # Apply the custom permission class

    def perform_create(self, serializer):
        serializer.save()

@api_view(['DELETE'])
@permission_classes([permissions.IsAdminUser])
def remove_unavailable_day(request, pk):
    try:
        unavailable_day = UnavailableDay.objects.get(pk=pk)
        unavailable_day.delete()
        return Response({'message': 'Unavailable day removed'}, status=status.HTTP_200_OK)
    except UnavailableDay.DoesNotExist:
        return Response({'error': 'Unavailable day not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_superuser(request):
    return Response({'is_superuser': request.user.is_superuser})
