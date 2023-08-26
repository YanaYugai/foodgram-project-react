from rest_framework import serializers
from api.models import Tag, Recipe, Ingredient, IngredientsRecipe, Favorite, Cart
from users.serializers import CustomUserSerializer
from django.core.files.base import ContentFile
import base64
from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator
from api.utils import create_tags_ingredients


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit', 'id')
        read_only_fields = ('name', 'measurement_unit', 'id')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('name', 'color', 'slug', 'id')
        read_only_fields = ('name', 'color', 'slug', 'id')


class IngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.pk')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientsRecipe
        fields = ('name', 'id', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer()
    tags = TagSerializer(
        many=True,
    )
    ingredients = IngredientReadSerializer(many=True, source='ingredientsrecipe', read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('name', 'id', 'image', 'text', 'cooking_time', 'author', 'tags', 'ingredients', 'is_in_shopping_cart', 'is_favorited')

    def get_is_favorited(self, recipe):
        return (self.context['request'].user.is_authenticated and Favorite.objects.filter(user=self.context['request'].user, recipe=recipe).exists())

    def get_is_in_shopping_cart(self, recipe):
        return (self.context['request'].user.is_authenticated and Cart.objects.filter(user=self.context['request'].user, recipe=recipe).exists())


class IngredientsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientsRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientsRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('name', 'image', 'text', 'cooking_time', 'tags', 'ingredients', 'author')
        read_only_fields = ('author',)

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError('Выберите тэги')
        return tags

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Добавьте ингридиенты!')
        ingredients = [dict(_) for _ in set(frozenset(ingredient.items()) for ingredient in ingredients)]
        new_ing = []
        for ingredient in ingredients:
            if ingredient['id'] in new_ing:
                raise serializers.ValidationError('Ингридиенты повторяются!')
            new_ing.append(ingredient['id'])
        return ingredients

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context={'request': self.context['request']}).data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        create_tags_ingredients(recipe, ingredients, tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        IngredientsRecipe.objects.filter(recipe=recipe).delete()
        recipe.tags.clear()
        create_tags_ingredients(recipe, ingredients, tags)
        return super().update(recipe, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.pk', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(source='recipe.cooking_time', read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное'
            ),
        ]
        extra_kwargs = {
            'user': {'write_only': True},
            'recipe': {'write_only': True}
        }


class CartSerializer(FavoriteSerializer):
    class Meta(FavoriteSerializer.Meta):
        model = Cart
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в корзину'
            ),
        ]