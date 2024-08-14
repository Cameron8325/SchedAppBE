from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Q

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

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def update_tokens(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        tokens = request.data.get('tokens')

        if tokens is not None:
            try:
                tokens = int(tokens)
                if tokens >= 0:
                    user.profile.tokens = tokens
                    user.profile.save()
                    return Response({'message': 'Tokens updated successfully'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Tokens value must be a non-negative integer'}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({'error': 'Valid tokens value is required'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Tokens value is required'}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_appointments(request):
    user = request.user
    appointments = Appointment.objects.filter(user=user).order_by('-date')
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_users(request):
    username = request.query_params.get('username', None)
    first_name = request.query_params.get('first_name', None)
    last_name = request.query_params.get('last_name', None)

    try:
        # Create an empty Q object
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
        print(f"Error in search_users: {str(e)}")
        return Response({"error": "Internal Server Error"}, status=500)
