from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny

from .serializers import UserSerializer, RegisterSerializer
from scheduling.serializers import AppointmentSerializer
from scheduling.models import Appointment
from scheduling.permissions import IsAdminOrReadOnly


class RegisterView(generics.CreateAPIView):
    """
    API view to handle user registration.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@csrf_exempt  # Disable CSRF protection for login for now
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username_email = request.data.get('username_email')
    password = request.data.get('password')
    user = User.objects.filter(Q(username=username_email) | Q(email=username_email)).first()

    if user and user.check_password(password):
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data  # Serialize user data

        # Add access and refresh token directly to the response body
        response = Response({
            'user': user_data,
            'access': str(refresh.access_token),  # Add access token to the response body
            'refresh': str(refresh)  # Optionally add the refresh token as well
        }, status=status.HTTP_200_OK)

        return response

    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_superuser(request):
    is_superuser = request.user.is_superuser
    return Response({'is_superuser': is_superuser})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_appointments(request):
    """
    API view to get authenticated user's appointments.
    """
    user = request.user
    appointments = Appointment.objects.filter(user=user).order_by('-date')
    serializer = AppointmentSerializer(appointments, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])  # Password reset does not require authentication
def password_reset_request(request):
    """
    API view to handle password reset request. Sends a reset email.
    """
    email = request.data.get('email')
    if email:
        associated_users = User.objects.filter(email=email)
        if associated_users.exists():
            for user in associated_users:
                subject = "Password Reset Requested"
                reset_link = f"http://localhost:3000/reset/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}"
                
                email_content = f"Hi {user.username},\nClick the link below to reset your password:\n{reset_link}\nIf you did not request this, please ignore this email."
                
                send_mail(
                    subject,
                    email_content,
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
        return Response({'error': 'User with this email not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt  # Disable CSRF for custom password reset
def custom_password_reset_confirm(request, uidb64, token):
    """
    Custom view to confirm password reset from the link in the email.
    """
    if request.method == 'POST':
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_object_or_404(User, pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return JsonResponse({'error': 'Invalid user or token'}, status=400)

        if default_token_generator.check_token(user, token):
            try:
                data = json.loads(request.body)
                new_password = data.get('new_password1')
                confirm_password = data.get('new_password2')
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)

            if new_password and confirm_password and new_password == confirm_password:
                user.set_password(new_password)
                user.save()

                # Invalidate all sessions for the user
                sessions = Session.objects.filter(expire_date__gte=timezone.now())
                for session in sessions:
                    data = session.get_decoded()
                    if data.get('_auth_user_id') == str(user.id):
                        session.delete()

                return JsonResponse({'message': 'Password reset successful'}, status=200)
            else:
                return JsonResponse({'error': 'Passwords do not match'}, status=400)
        else:
            return JsonResponse({'error': 'Invalid token or user'}, status=400)
    return JsonResponse({'error': 'POST request required'}, status=400)
