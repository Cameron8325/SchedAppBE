from rest_framework import generics, status, permissions
from rest_framework.response import Response
from django.core.mail import send_mail
from .models import Appointment, AvailableDay
from .serializers import AppointmentSerializer, AvailableDaySerializer
from rest_framework.decorators import api_view, permission_classes
from datetime import datetime, timedelta
from .permissions import IsAdminOrReadOnly

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

class AvailableDayListCreate(generics.ListCreateAPIView):
    queryset = AvailableDay.objects.all()
    serializer_class = AvailableDaySerializer
    permission_classes = [IsAdminOrReadOnly]  # Apply the custom permission class

    def perform_create(self, serializer):
        serializer.save()

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def set_availability(request):
    try:
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        reason = request.data.get('reason', '')

        if not start_date_str or not end_date_str:
            return Response({'error': 'Start date and end date are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Parse the date string into a date object
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if start_date > end_date:
            return Response({'error': 'Start date must be before end date'}, status=status.HTTP_400_BAD_REQUEST)

        current_date = start_date
        while current_date <= end_date:
            AvailableDay.objects.update_or_create(
                date=current_date,
                defaults={'reason': reason}
            )
            current_date += timedelta(days=1)

        return Response({'message': f'Availability set for range {start_date_str} - {end_date_str}'}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error in set_availability: {e}")
        return Response({'error': f'Internal Server Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([permissions.IsAdminUser])
def remove_available_days(request):
    try:
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')

        if not start_date_str or not end_date_str:
            return Response({'error': 'Start date and end date are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if start_date > end_date:
            return Response({'error': 'Start date must be before end date'}, status=status.HTTP_400_BAD_REQUEST)

        # Delete all AvailableDay records in the date range
        AvailableDay.objects.filter(date__gte=start_date, date__lte=end_date).delete()

        return Response({'message': f'Available days removed for range {start_date_str} - {end_date_str}'}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error in remove_available_days: {e}")
        return Response({'error': f'Internal Server Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_superuser(request):
    return Response({'is_superuser': request.user.is_superuser})
