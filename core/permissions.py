from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS


def _role_name(user):
    """Helper to safely get role name in uppercase for comparisons."""
    try:
        return getattr(user.role, 'name', None).upper() if user and getattr(user, 'role', None) else None
    except Exception:
        return None


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        role = _role_name(request.user)
        return request.user.is_authenticated and role == 'ADMIN'


class IsDoctorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        role = _role_name(request.user)
        return request.user.is_authenticated and role == 'DOCTOR'


class IsReceptionistOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        role = _role_name(request.user)
        return request.user.is_authenticated and role == 'RECEPTIONIST'


class IsNurse(BasePermission):
    """Allow access only to users with role NURSE (or ADMIN)."""
    def has_permission(self, request, view):
        role = _role_name(request.user)
        # Admins should always be allowed
        if role == 'ADMIN':
            return True
        return request.user.is_authenticated and role == 'NURSE'


class IsPharmacist(BasePermission):
    """Allow access only to users with role PHARMACIST (or ADMIN)."""
    def has_permission(self, request, view):
        role = _role_name(request.user)
        if role == 'ADMIN':
            return True
        return request.user.is_authenticated and role == 'PHARMACIST'


class PatientPortalPermission(permissions.BasePermission):
    """Allow patients to access only their own data."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(user, 'is_staff', False):
            return True
        if hasattr(obj, 'user'):
            return obj.user == user
        if hasattr(obj, 'patient'):
            # patient may or may not have a linked user; handle gracefully
            patient_user = getattr(obj.patient, 'user', None)
            return patient_user == user
        return False
