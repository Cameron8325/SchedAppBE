from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json
from django.contrib.sessions.models import Session
from django.utils import timezone
from rest_framework.permissions import AllowAny
from django.db import transaction

from .serializers import UserSerializer, RegisterSerializer
from scheduling.serializers import AppointmentSerializer
from scheduling.models import Appointment
from scheduling.permissions import IsAdminOrReadOnly
from rest_framework_simplejwt.views import TokenRefreshView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .tokens import email_verification_token
from .models import Profile  # Ensure Profile is imported

class RegisterView(generics.CreateAPIView):
    """
    API view to handle user registration.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        with transaction.atomic():
            user = serializer.save()
            send_verification_email(user)  # Send verification email after registration

def send_verification_email(user):
    """
    Function to send email verification to the user.
    """
    token = email_verification_token.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Determine the base URL based on the environment
    if settings.DEBUG:
        base_url = "http://localhost:3000"  # React frontend
    else:
        base_url = "https://yourproductiondomain.com"  # Replace with your production domain
    
    verification_link = f"{base_url}/verify-email/{uid}/{token}/"

    subject = "Verify your email address"
    message = f"Hi {user.username},\n\nPlease verify your email by clicking the link below:\n{verification_link}\n\nIf you did not sign up for this account, please ignore this email."

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """
    API view to resend verification email using the email or username from the request.
    """
    identifier = request.data.get('email') or request.data.get('username')
    
    if not identifier:
        return Response({'error': 'Email or username is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Attempt to find the user by email first, then by username
        try:
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            user = User.objects.get(username=identifier)
        
        if user.profile.is_verified:
            return Response({'message': 'Your email is already verified.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Resend the verification email
        send_verification_email(user)
        return Response({'message': 'Verification email resent.'}, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        # To prevent user enumeration, respond with a generic message
        return Response({'message': 'If an account with that identifier exists, a verification email has been sent.'}, status=status.HTTP_200_OK)
    except Exception as e:
        # Log the exception (optional)
        return Response({'error': 'An error occurred while processing your request.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, uidb64, token):
    """
    View to verify user's email using a token sent in the email.
    """
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_object_or_404(User, pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return JsonResponse({'error': 'Invalid link'}, status=400)

    if email_verification_token.check_token(user, token):
        # Ensure the Profile exists
        profile, created = Profile.objects.get_or_create(user=user)
        profile.is_verified = True  # Set is_verified to True
        profile.save()
        return JsonResponse({'message': 'Email verified successfully'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid or expired token'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Get the refresh token from the cookie if it's not in the request data
        if 'refresh' not in request.data:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                request.data['refresh'] = refresh_token
            else:
                return Response({'error': 'No refresh token found'}, status=status.HTTP_400_BAD_REQUEST)
        return super().post(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    API view to handle user login.
    """
    username_email = request.data.get('username_email')
    password = request.data.get('password')
    user = User.objects.filter(Q(username=username_email) | Q(email=username_email)).first()

    if user and user.check_password(password):
        if not user.profile.is_verified:
            return Response({'error': 'Email is not verified.'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        user_data = UserSerializer(user).data

        response = Response({
            'user': user_data,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)

        # Set the access and refresh tokens in HttpOnly cookies
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )

        return response

    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    
    # Delete the access and refresh token cookies
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/')
    
    print("Logout: access_token and refresh_token cookies deleted")  # Debugging log
    
    return response

@api_view(['GET'])
@permission_classes([AllowAny])
def set_csrf(request):
    """
    Simple view to set the CSRF token cookie.
    """
    return Response({'message': 'CSRF cookie set'})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_user(request):
    """
    API view to get the authenticated user's profile.
    """
    user = request.user
    user_data = UserSerializer(user).data
    return Response(user_data, status=status.HTTP_200_OK)

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
@permission_classes([AllowAny])
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
                    try:
                        data = session.get_decoded()
                        if data.get('_auth_user_id') == str(user.id):
                            session.delete()
                    except Exception as e:
                        # Optionally log the error
                        pass

                return JsonResponse({'message': 'Password reset successful'}, status=200)
            else:
                return JsonResponse({'error': 'Passwords do not match'}, status=400)
        else:
            return JsonResponse({'error': 'Invalid token or user'}, status=400)
    return JsonResponse({'error': 'POST request required'}, status=400)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def account_deletion_request(request):
    """
    API view to handle account deletion request. Sends a confirmation email.
    """
    password = request.data.get('password')
    user = request.user

    # Verify password
    if not user.check_password(password):
        return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)

    # Generate deletion token
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    # Build deletion link
    deletion_link = f"http://localhost:3000/users/delete-account-confirm/{uidb64}/{token}"

    # Send email
    subject = "Account Deletion Requested"
    email_content = f"Hi {user.username},\n\nClick the link below to permanently delete your account:\n{deletion_link}\n\nIf you did not request this, please ignore this email."

    send_mail(
        subject,
        email_content,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )

    return Response({'message': 'Account deletion email sent'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def account_deletion_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': 'Invalid link'}, status=status.HTTP_400_BAD_REQUEST)

    # Verify token
    if not default_token_generator.check_token(user, token):
        return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

    # Delete related profile explicitly
    Profile.objects.filter(user=user).delete()

    # Delete user account
    user.delete()

    return Response({'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_user(request):
    user = request.user
    data = request.data
    with transaction.atomic():
        try:
            updated_fields = {}

            # Update basic user fields
            if 'first_name' in data and data['first_name'] != user.first_name:
                user.first_name = data['first_name']
                updated_fields['first_name'] = data['first_name']
            
            if 'last_name' in data and data['last_name'] != user.last_name:
                user.last_name = data['last_name']
                updated_fields['last_name'] = data['last_name']

            if 'email' in data and data['email'] != user.email:
                user.email = data['email']
                updated_fields['email'] = data['email']

            if 'username' in data and data['username'] != user.username:
                user.username = data['username']
                updated_fields['username'] = data['username']

            # Handle Profile updates (e.g., phone number)
            if 'profile' in data and 'phone_number' in data['profile']:
                profile, _ = Profile.objects.get_or_create(user=user)
                if data['profile']['phone_number'] != profile.phone_number:
                    profile.phone_number = data['profile']['phone_number']
                    updated_fields['profile_phone_number'] = data['profile']['phone_number']
                    profile.save()  # Save profile changes

            # Save user changes and serialize response
            user.save()
            serializer = UserSerializer(user)
            return Response({'user': serializer.data, 'updated_fields': updated_fields}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': 'Failed to update profile.', 'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
      