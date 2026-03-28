"""
Custom DRF permissions for role-based access control.
"""
from rest_framework.permissions import BasePermission


class IsBuyer(BasePermission):
    """Allow access only to users with role='buyer'."""
    message = "Only buyers can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'buyer')


class IsSupplier(BasePermission):
    """Allow access only to users with role='supplier'."""
    message = "Only suppliers can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'supplier')


class IsBuyerOrReadOnly(BasePermission):
    """Buyers can write; authenticated users can read."""

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user and request.user.is_authenticated
        return bool(request.user and request.user.is_authenticated and request.user.role == 'buyer')
