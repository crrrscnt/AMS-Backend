from rest_framework import permissions


#class IsAuthenticatedUser(permissions.BasePermission):
#    """
#    Разрешение для авторизованных пользователей.
#    """
#
#    def has_permission(self, request, view):
#        return request.user and request.user.is_authenticated
#
#
#class IsAnyUser(permissions.BasePermission):
#    """
#    Разрешение для всех пользователей (авторизованных и неавторизованных).
#    """
#
#    def has_permission(self, request, view):
#        return True
#
#
#class IsManager(permissions.BasePermission):
#    def has_permission(self, request, view):
#        return bool(request.user and (
#                request.user.is_staff or request.user.is_superuser))
#
#
#class IsAdmin(permissions.BasePermission):
#    def has_permission(self, request, view):
#        return bool(request.user and request.user.is_superuser)

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)