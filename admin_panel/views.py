from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import User
from users.models import Profile  # Import Profile model
from rest_framework.permissions import IsAdminUser

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
