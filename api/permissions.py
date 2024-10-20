from rest_framework import permissions

from api.get_user import authenticate_user


# from api.get_user import authenticate_user


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and (
                    request.user.is_staff or request.user.is_superuser))


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsAuthenticatedUser(permissions.BasePermission):
    def has_permission(self, request, view):
        # user = authenticate_user(request)
        user = request.user
        print(
            f"User in permission.py check: {user}, is_authenticated: {user.is_authenticated}")
        # return bool(user)
        # return request.user.is_authenticated
        return bool(user and user.is_authenticated)


class IsAnyUser(permissions.BasePermission):
    def has_permission(self, request, view):
        # user = authenticate_user(request)
        user = request.user
        return bool(user) or request.method in permissions.SAFE_METHODS


class IsCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.creator == request.user:
            return True