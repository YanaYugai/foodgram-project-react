from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from recipe.models import Recipe


class IsUserAdminAuthorOrReadOnly(BasePermission):
    """Разрешение редактирования только Админу и Автору."""

    def has_permission(self, request: Request, _) -> bool:
        """Проверка прав пользователя на доступ к запросу.

        Args:
            request: Запрос пользователя.

        Returns:
            True - функция сработала удачно, иначе False.

        """
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request: Request, _, obj: Recipe) -> bool:
        """Проверка прав пользователя на доступ к объекту.

        Args:
            request: Запрос пользователя.
            obj: Экземляр класса `Recipe`.

        Returns:
            True - функция сработала удачно, иначе False.

        """
        return request.method in SAFE_METHODS or (
            obj.author == request.user
            or request.user.is_staff
            or request.user.is_superuser
        )
