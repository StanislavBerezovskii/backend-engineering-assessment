from rest_framework import permissions


class IsAdminOrSuperuser(permissions.BasePermission):
    """Permissions for admins and superusers only."""
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.is_admin_or_superuser)


class IsAdminSuperuserOrReadOnly(permissions.BasePermission):
    """Permission for admins, superusers and read-only access."""
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated
                and request.user.is_admin_or_superuser)


class IsStaffAdminOrReadOnly(permissions.BasePermission):
    """"Permission for superusers, admins, staff, and read-only access."""
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_admin_or_superuser
                or request.user.is_moderator)
