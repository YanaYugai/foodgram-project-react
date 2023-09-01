from django.contrib import admin

from recipe.models import (
    Cart,
    Favorite,
    Ingredient,
    IngredientsRecipe,
    Recipe,
    Tag,
)


class IngredientsRecipeInLine(admin.TabularInline):
    model = IngredientsRecipe
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite', 'ingredients_name')
    search_fields = ('name',)
    list_filter = ('author', 'name', 'tags')
    filter_horizontal = ('tags',)
    inlines = (IngredientsRecipeInLine,)

    def ingredients_name(self, recipe):
        return ', '.join(
            [ingredient.name for ingredient in recipe.ingredients.all()],
        )

    ingredients_name.short_description = 'Ингредиенты'

    def favorite(self, recipe):
        return recipe.favorites.count()

    favorite.short_description = 'Количество в избранном'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    list_filter = ('color', 'name')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(IngredientsRecipe)
class IngredientsRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'ingredient', 'recipe', 'amount')
    list_filter = ('ingredient', 'recipe')
    search_fields = ('ingredient', 'recipe')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('recipe', 'user')
    search_fields = ('user', 'recipe')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('recipe', 'user')
    search_fields = ('user', 'recipe')
