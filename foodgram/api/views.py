import io

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import generics, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import LimitPagination
from api.permissions import IsUserAdminAuthorOrReadOnly
from api.serializers import (
    CartSerializer,
    FavoriteSerializer,
    FollowResultSerializer,
    FollowsSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeReadSerializer,
    TagSerializer,
)
from recipe.models import (
    Cart,
    Favorite,
    Ingredient,
    IngredientsRecipe,
    Recipe,
    Tag,
)
from users.models import Follow, User


class FollowApiView(views.APIView):
    serializer_class = FollowsSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request: WSGIRequest, user_id: int) -> Response:
        """Метод для создания подписки.

        Args:
            request: Объект запроса.
            user_id: id-автора.

        Returns:
            Возвращает статус об успешном создании объекта/плохой реквест.

        """
        serializer = self.serializer_class(
            data={
                'user': request.user.id,
                'author': get_object_or_404(User, id=user_id).pk,
            },
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: WSGIRequest, user_id: int) -> Response:
        """Метод для удаления подписки.

        Args:
            request: Объект запроса.
            *args: Массив аргументов.
            **kwargs: Словарь именнованных аргументов.

        Returns:
            Возвращает статус об цспешном удалении контента/плохой реквест.

        """
        author = get_object_or_404(User, id=user_id)
        user = request.user
        if Follow.objects.filter(user=user.id, author=author.id).delete():
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class FollowListApiView(generics.ListAPIView):
    serializer_class = FollowResultSerializer
    pagination_class = LimitPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class TagReadView(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели `Tag`."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientReadView(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели `Ingredient`."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели `Recipe`."""

    queryset = (
        Recipe.objects.select_related('author')
        .prefetch_related('tags', 'ingredients')
        .all()
    )
    pagination_class = LimitPagination
    permission_classes = (IsUserAdminAuthorOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @staticmethod
    def create_instance(request, pk, serializer):
        """Добавление рецепта в избранное или в корзину.

        Args:
            request: Объект запроса.
            serializer: `FollowSErializer` или `CartSerializer`.
            pk: id-рецепта.

        Returns:
            Возвращает статус о создании объекта.

        """
        serializer = serializer(
            data={'user': request.user.id, 'recipe': pk},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def favorite(self, request: WSGIRequest, pk: int) -> Response:
        """Метод для добавления/удаления рецепта в/из избранное/ого.

        Args:
            request: Объект запроса.
            pk: id-рецепта.

        Returns:
            Возвращает статус об цспешном удалении контента/создании
            контента/плохой реквест.

        """
        return self.create_instance(request, pk, FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request: WSGIRequest, pk: int) -> Response:
        get_object_or_404(Favorite, user=request.user.id, recipe=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def shopping_cart(self, request: WSGIRequest, pk: int) -> Response:
        """Метод для добавления рецепта в корзину.

        Args:
            request: Объект запроса.
            pk: id-рецепта.

        Returns:
            Возвращает статус об успешном удалении контента/создании
            контента/плохой реквест.

        """
        return self.create_instance(request, pk, CartSerializer)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request: WSGIRequest, pk: int) -> Response:
        """Метод для удаления рецепта из корзины.

        Args:
            request: Объект запроса.
            pk: id-рецепта.

        Returns:
            Возвращает статус об успешном удалении контента/создании
            контента/плохой реквест.

        """
        get_object_or_404(Cart, user=request.user.id, recipe=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def create_shopping_list(ingredients):
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter, bottomup=0)
        text_obj = c.beginText()
        text_obj.setTextOrigin(inch, inch)
        pdfmetrics.registerFont(TTFont('Verdana', 'data/Verdana.ttf', 'UTF-8'))
        text_obj.setFont('Verdana', 17)
        ing_list = [
            f'{ing["ingredient__name"]} '
            f'({ing["ingredient__measurement_unit"]}) - {ing["ing_amount"]}'
            for ing in ingredients
        ]
        text_obj.textLines(ing_list)
        c.drawText(text_obj)
        c.showPage()
        c.save()
        buf.seek(0)
        return buf

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def download_shopping_cart(self, request: WSGIRequest) -> FileResponse:
        """Метод для загрузки pdf-файла со списком покупок.

        Args:
            request: Объект запроса.

        Returns:
            Возвращает PDF-файл.

        """
        ingredients = (
            IngredientsRecipe.objects.filter(recipe__carts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(ing_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        return FileResponse(
            self.create_shopping_list(ingredients),
            as_attachment=True,
            filename='ingredients.pdf',
        )
