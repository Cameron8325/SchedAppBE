from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser  # Fix: Import permissions
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail
from datetime import datetime, timedelta
from scheduling.permissions import *  # Assuming you need this import for custom permissions

from users.models import Profile
from users.serializers import UserSerializer
from scheduling.models import Appointment, AvailableDay
from scheduling.serializers import AppointmentSerializer


@api_view(['POST'])
@permission_classes([IsAdminUser])
def update_tokens(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        tokens = request.data.get('tokens')

        if tokens is not None and isinstance(tokens, int):
            user.profile.tokens = tokens
            user.profile.save()
            return Response({'message': 'Tokens updated successfully'}, status=status.HTTP_200_OK)
        return Response({'error': 'Valid tokens value is required'}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_appointment(request, pk):
    try:
        appointment = Appointment.objects.get(pk=pk)
        appointment.status = 'confirmed'
        appointment.reason = ''  # Clear the reason field
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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAuthenticated])
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

@api_view(['POST'])
@permission_classes([IsAdminUser])
def mark_to_completion(request, pk):
    try:
        appointment = Appointment.objects.get(pk=pk)
        if appointment.status != 'to_completion':
            appointment.status = 'to_completion'
            appointment.save()

        profile = appointment.user.profile
        profile.tokens += 1
        profile.save()

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


@api_view(['POST'])
@permission_classes([IsAdminUser])
def set_availability(request):
    try:
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        day_type = request.data.get('type')

        if not start_date_str or not day_type:
            return Response({'error': 'Start date and type are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else start_date
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if start_date > end_date:
            return Response({'error': 'Start date must be before end date'}, status=status.HTTP_400_BAD_REQUEST)

        current_date = start_date
        while current_date <= end_date:
            AvailableDay.objects.update_or_create(
                date=current_date,
                defaults={'type': day_type}
            )
            current_date += timedelta(days=1)

        return Response({'message': f'Availability set for range {start_date_str} - {end_date_str}'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'Internal Server Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def remove_available_days(request):
    try:
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not start_date_str or not end_date_str:
            return Response({'error': 'Start date and end date are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if start_date > end_date:
            return Response({'error': 'Start date must be before end date'}, status=status.HTTP_400_BAD_REQUEST)

        AvailableDay.objects.filter(date__gte=start_date, date__lte=end_date).delete()

        return Response({'message': f'Available days removed for range {start_date_str} - {end_date_str}'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'Internal Server Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def search_users(request):
    username = request.query_params.get('username', None)
    first_name = request.query_params.get('first_name', None)
    last_name = request.query_params.get('last_name', None)

    try:
        filters = Q()

        if username:
            filters &= Q(username__icontains=username)
        if first_name:
            filters &= Q(first_name__icontains=first_name)
        if last_name:
            filters &= Q(last_name__icontains=last_name)

        if filters:
            users = User.objects.filter(filters)
        else:
            return Response({"error": "Please provide a search term."}, status=400)

        if users.exists():
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No users found."}, status=404)

    except Exception as e:
        return Response({"error": "Internal Server Error"}, status=500)
