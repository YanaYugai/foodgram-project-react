from django_filters.rest_framework import FilterSet, filters

from recipe.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    """Фильтр для модели `Recipe`."""

    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='get_is_in_shopping_cart',
    )
    is_favorited = filters.NumberFilter(method='get_is_favorited')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_in_shopping_cart', 'is_favorited')

    def get_is_favorited(self, queryset: Recipe, _, value: int) -> Recipe:
        """Получение отфильтрованного по нахождению в избранном queryset.

        Returns:
            Экземпляры модели `Recipe`.

        """
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(
        self,
        queryset: Recipe,
        _,
        number: int,
    ) -> Recipe:
        """Получение отфильтрованного по нахождению в корзине queryset.

        Returns:
            Экземпляры модели `Recipe`.

        """
        if self.request.user.is_authenticated and number:
            return queryset.filter(carts__user=self.request.user)
        return queryset


class IngredientFilter(FilterSet):
    """Фильтр для модели `Ingredient`."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
