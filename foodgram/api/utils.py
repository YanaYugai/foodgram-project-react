from api.models import IngredientsRecipe, Ingredient, Recipe
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.response import Response
from rest_framework import generics, status


def create_tags_ingredients(recipe, ingredients, tags):
    for ingredient in ingredients:
        current_ingredient = get_object_or_404(Ingredient, pk=ingredient['id'].pk)
        IngredientsRecipe.objects.create(ingredient=current_ingredient, recipe=recipe, amount=ingredient['amount'])
    recipe.tags.set(tags)


def get_obj(pk, model):
        try:
            obj = model.objects.get(pk=pk)
        except model.DoesNotExist:
            raise Http404(
                "Не найден объект или неверный запрос!",
            )
        return obj


def post_instance(request, serializer, pk):
    serializer = serializer(
        data={'user': request.user.id, 'recipe': get_obj(pk, Recipe).pk}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)

