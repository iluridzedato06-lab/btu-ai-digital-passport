from rest_framework.permissions import BasePermission

from apps.accounts.roles import role_of


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) == "student" or hasattr(request.user, "student")


class IsStaffRole(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) in ("staff", "admin")


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) == "admin"
