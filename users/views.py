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

from .serializers import UserSerializer, RegisterSerializer
from scheduling.serializers import AppointmentSerializer
from scheduling.models import Appointment
from scheduling.permissions import IsAdminOrReadOnly


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class LoginView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        username_email = request.data.get('username_email')
        password = request.data.get('password')
        user = User.objects.filter(username=username_email).first() or User.objects.filter(email=username_email).first()

        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data  # Include tokens in the user data
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data
            })
        return Response({'error': 'Invalid credentials'}, status=400)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_appointments(request):
    user = request.user
    appointments = Appointment.objects.filter(user=user).order_by('-date')
    serializer = AppointmentSerializer(appointments, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['POST'])
def password_reset_request(request):
    email = request.data.get('email')
    if email:
        associated_users = User.objects.filter(email=email)
        if associated_users.exists():
            for user in associated_users:
                subject = "Password Reset Requested"
                # Adjust the link to point to the frontend in local development
                reset_link = f"http://localhost:3000/reset/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}"
                
                email_content = f"Hi {user.username},\nClick the link below to reset your password:\n{reset_link}\nIf you did not request this, please ignore this email."
                
                send_mail(
                    subject,
                    email_content,
                    settings.EMAIL_HOST_USER,  # Use the email from your settings
                    [user.email],
                    fail_silently=False,
                )
            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
        return Response({'error': 'User with this email not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)


def custom_password_reset_confirm(request, uidb64, token):
    if request.method == 'POST':
        try:
            # Decode the uidb64 to get the user's ID
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_object_or_404(User, pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return JsonResponse({'error': 'Invalid user or token'}, status=400)

        # Check if the token is valid for the user
        if default_token_generator.check_token(user, token):
            try:
                # Parse the JSON data from the request body
                data = json.loads(request.body)
                new_password = data.get('new_password1')
                confirm_password = data.get('new_password2')
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)

            # Validate the passwords
            if new_password and confirm_password and new_password == confirm_password:
                # Set the new password
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
    else:
        return JsonResponse({'error': 'POST request required'}, status=400)