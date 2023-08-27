from typing import Dict, List, Union

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipe.models import Ingredient, IngredientsRecipe, Recipe, User


def create_tags_ingredients(
    recipe: Recipe, ingredients: List[Dict[str, int]], tags: List[int],
) -> None:
    """Добавление тегов и ингридиентов в рецепт.

    Args:
        recipe: Экземляр класса `Recipe`.
        ingredients: Массив из данных ингридиентов.
        tags: Массив id-тэгов.

    """
    for ingredient in ingredients:
        current_ingredient = get_object_or_404(
            Ingredient,
            pk=ingredient['id'].pk,
        )
        IngredientsRecipe.objects.create(
            ingredient=current_ingredient,
            recipe=recipe,
            amount=ingredient['amount'],
        )
    recipe.tags.set(tags)


def get_obj(pk: int, model: Union[User, Recipe]) -> Union[User, Recipe]:
    """Получение инстанса по id.

    Args:
        pk: id-требуемого объекта.
        model: Модель требуемого обхекта.

    Returns:
        Возвращает требуемый экземпляр.

    """
    try:
        obj = model.objects.get(pk=pk)
    except model.DoesNotExist:
        raise Http404(
            "Не найден объект или неверный запрос!",
        )
    return obj


def post_instance(request, serializer, pk: int) -> Response:
    """Добавление рецепта в избранное или в корзину.

    Args:
        request: Объект запроса.
        serializer: `FollowSErializer` или `CartSerializer`.
        pk: id-рецепта.

    Returns:
        Возвращает статус о создании объекта.

    """
    serializer = serializer(
        data={'user': request.user.id, 'recipe': get_obj(pk, Recipe).pk},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)
