from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to allow read-only access for unauthenticated users,
    and restrict write access to admin users.
    """
    def has_permission(self, request, view):
        # Allow read-only (GET, HEAD, OPTIONS) access to anyone, including unauthenticated users
        if request.method in SAFE_METHODS:
            return True
        # Restrict write operations (POST, PUT, DELETE) to staff (admin) users
        return request.user and request.user.is_staff
