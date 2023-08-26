
from api. serializers import TagSerializer, RecipeReadSerializer, RecipeCreateSerializer, FavoriteSerializer, CartSerializer, IngredientSerializer, FollowsSerializer, FollowResultSerializer
from api.models import Tag, Recipe, Favorite, Cart, Ingredient, IngredientsRecipe
from rest_framework import viewsets, status, mixins
from django.http import Http404, FileResponse
from rest_framework.response import Response
from rest_framework.decorators import action
from api.paginators import LimitPagination
import io
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from django.db.models import Sum
from rest_framework.permissions import AllowAny, IsAuthenticated
from api.permissions import IsUserAdminAuthorOrReadOnly
from api.filters import RecipeFilter, IngredientFilter
from django_filters.rest_framework import DjangoFilterBackend
from api.utils import get_obj, post_instance
from django.contrib.auth import get_user_model
from users.models import Follow


User = get_user_model()


class FollowApiView(mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FollowsSerializer
    pagination_class = LimitPagination
    permission_classes = (IsAuthenticated, )

    def create(self, request, user_id):
        serializer = self.get_serializer(data={'user': request.user.id, 'author': get_obj(user_id, User).pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        author = User.objects.get(pk=serializer.validated_data['author'].id)
        result = FollowResultSerializer(author, context={'request': request})
        return Response(result.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        author = get_obj(self.kwargs['user_id'], User)
        if Follow.objects.filter(user=request.user.id, author=author.id).exists():
            self.perform_destroy(Follow.objects.get(user=request.user.id, author=author.id))
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = User.objects.filter(following__user=request.user.id)
        pages = self.paginate_queryset(queryset)
        serializer = FollowResultSerializer(pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class TagReadView(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientReadView(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    permission_classes = (IsUserAdminAuthorOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated, ]
    )
    def favorite(self, request, pk):
        if request.method == "POST":
            return post_instance(request, FavoriteSerializer, pk)
        recipe = get_obj(pk, Recipe)
        if Favorite.objects.filter(user=request.user.id, recipe=recipe.id).exists():
            self.perform_destroy(Favorite.objects.get(user=request.user.id, recipe=recipe.id))
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, pk):
        if request.method == "POST":
            return post_instance(request, CartSerializer, pk)
        recipe = get_obj(pk, Recipe)
        if Cart.objects.filter(user=request.user.id, recipe=recipe.id).exists():
            self.perform_destroy(Cart.objects.get(user=request.user.id, recipe=recipe.id))
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated, ]
    )
    def download_shopping_cart(self, request):
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter, bottomup=0)
        text_obj = c.beginText()
        text_obj.setTextOrigin(inch, inch)
        pdfmetrics.registerFont(TTFont('Verdana', 'Verdana.ttf', 'UTF-8'))
        text_obj.setFont('Verdana', 17)
        ingredients = IngredientsRecipe.objects.filter(recipe__carts__user=request.user).values('ingredient__name', 'ingredient__measurement_unit').annotate(ing_amount=Sum('amount'))
        ing_list = [
            f'{ing["ingredient__name"]} ({ing["ingredient__measurement_unit"]}) - {ing["ing_amount"]}'
            for ing in ingredients
        ]
        text_obj.textLines(ing_list)
        c.drawText(text_obj)
        c.showPage()
        c.save()
        buf.seek(0)
        return FileResponse(buf, as_attachment=True, filename='ingredients.pdf')
