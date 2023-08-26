import io

from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import mixins, status, viewsets
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
from api.utils import get_obj, post_instance
from recipe.models import (
    Cart,
    Favorite,
    Ingredient,
    IngredientsRecipe,
    Recipe,
    Tag,
)
from users.models import Follow

User = get_user_model()


class FollowApiView(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Вьюсет для модели `Follow`."""

    serializer_class = FollowsSerializer
    pagination_class = LimitPagination
    permission_classes = (IsAuthenticated,)

    def create(self, request: WSGIRequest, user_id: int) -> Response:
        """Метод для создания подписки.

        Args:
            request: Объект запроса.
            user_id: id-автора.

        Returns:
            Возвращает статус об успешном создании объекта/плохой реквест.

        """
        serializer = self.get_serializer(
            data={
                'user': request.user.id,
                'author': get_obj(user_id, User).pk,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        author = User.objects.get(pk=serializer.validated_data['author'].id)
        result = FollowResultSerializer(author, context={'request': request})
        return Response(result.data, status=status.HTTP_200_OK)

    def destroy(self, request: WSGIRequest, *args, **kwargs) -> Response:
        """Метод для удаления подписки.

        Args:
            request: Объект запроса.
            *args: Массив аргументов.
            **kwargs: Словарь именнованных аргументов.

        Returns:
            Возвращает статус об цспешном удалении контента/плохой реквест.

        """
        author = get_obj(self.kwargs['user_id'], User)
        if Follow.objects.filter(
            user=request.user.id,
            author=author.id,
        ).exists():
            self.perform_destroy(
                Follow.objects.get(user=request.user.id, author=author.id),
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def list(self, request: WSGIRequest, *args, **kwargs) -> Response:
        """Метод для получения всех подписок.

        Args:
            request: Объект запроса.
            *args: Массив аргументов.
            **kwargs: Словарь именнованных аргументов.

        Returns:
            Возвращает статус об успешном выполнении.

        """
        queryset = User.objects.filter(following__user=request.user.id)
        pages = self.paginate_queryset(queryset)
        serializer = FollowResultSerializer(
            pages,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)


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

    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    permission_classes = (IsUserAdminAuthorOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer: RecipeCreateSerializer) -> None:
        """Cохранение нового экземпляра объекта.

        Args:
            serializer: Сериализатор `RecipeCreateSerializer`.

        """
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
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
        if request.method == "POST":
            return post_instance(request, FavoriteSerializer, pk)
        recipe = get_obj(pk, Recipe)
        if Favorite.objects.filter(
            user=request.user.id,
            recipe=recipe.id,
        ).exists():
            self.perform_destroy(
                Favorite.objects.get(user=request.user.id, recipe=recipe.id),
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def shopping_cart(self, request: WSGIRequest, pk: int) -> Response:
        """Метод для добавления/удаления рецепта в/из корзину/ы.

        Args:
            request: Объект запроса.
            pk: id-рецепта.

        Returns:
            Возвращает статус об успешном удалении контента/создании
            контента/плохой реквест.

        """
        if request.method == "POST":
            return post_instance(request, CartSerializer, pk)
        recipe = get_obj(pk, Recipe)
        if Cart.objects.filter(
            user=request.user.id,
            recipe=recipe.id,
        ).exists():
            self.perform_destroy(
                Cart.objects.get(user=request.user.id, recipe=recipe.id),
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

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
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter, bottomup=0)
        text_obj = c.beginText()
        text_obj.setTextOrigin(inch, inch)
        pdfmetrics.registerFont(TTFont('Verdana', 'Verdana.ttf', 'UTF-8'))
        text_obj.setFont('Verdana', 17)
        ingredients = (
            IngredientsRecipe.objects.filter(recipe__carts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(ing_amount=Sum('amount'))
        )
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
        return FileResponse(
            buf,
            as_attachment=True,
            filename='ingredients.pdf',
        )
