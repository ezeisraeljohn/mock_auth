from rest_framework.permissions import BasePermission
from .models import App, Developer


class IsAppOwner(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        developer_id = request.auth.get("developer_id", None)

        if developer_id:
            return Developer.objects.filter(user=request.user, id=developer_id).exists()

        return False


class IsDeveloper(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        dev_id = request.auth.get("developer_id", None)

        if dev_id:
            return Developer.objects.filter(id=dev_id, user=request.user).exists()

        return False
