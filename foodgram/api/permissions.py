from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request


class IsUserAdminAuthorOrReadOnly(BasePermission):
    """Разрешение редактирования только Админу, Автору и Модератору."""

    def has_permission(self, request: Request, view: None) -> bool:
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request: Request, view: None, obj) -> bool:
        return request.method in SAFE_METHODS or (
            obj.author == request.user
            or request.user.is_staff
            or request.user.is_superuser
        )
