from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsManager(BasePermission):
    message = 'Only managers may perform this action!'

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True

        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.groups.filter(name='Managers').exists()
        )
