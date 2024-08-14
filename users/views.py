from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .serializers import UserSerializer, RegisterSerializer
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
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=400)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def update_tokens(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        tokens = request.data.get('tokens')
        
        if tokens is not None:
            if isinstance(tokens, int) and tokens >= 0:
                user.profile.tokens = tokens
                user.profile.save()
                return Response({'message': 'Tokens updated successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Tokens value must be a non-negative integer'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Tokens value is required'}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
