from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and getattr(request.user.role, 'name', None) == 'Admin'

class IsDoctorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and getattr(request.user.role, 'name', None) == 'Doctor'

class IsReceptionistOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and getattr(request.user.role, 'name', None) == 'Receptionist'

class PatientPortalPermission(permissions.BasePermission):
    """Allow patients to access only their own data."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True
        if hasattr(obj, 'user'):
            return obj.user == user
        if hasattr(obj, 'patient'):
            return obj.patient.user == user
        return False
