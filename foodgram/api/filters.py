from django_filters.rest_framework import FilterSet, filters
from api.models import Tag, User, Recipe, Ingredient


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all(), field_name='tags__slug', to_field_name='slug')
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_in_shopping_cart = filters.NumberFilter(method='get_is_in_shopping_cart')
    is_favorited = filters.NumberFilter(method='get_is_favorited')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_in_shopping_cart', 'is_favorited')

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, number):
        if self.request.user.is_authenticated and number:
            return queryset.filter(carts__user=self.request.user)
        return queryset


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='istartwith')

    class Meta:
        model = Ingredient
        fields = ('name', )
