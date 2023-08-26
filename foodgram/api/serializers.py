import base64
from typing import Any, Dict, List, OrderedDict

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api import utils
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


class CustomUserSerializer(UserSerializer):
    """Сериализатор для модели `User` для просмотра пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        read_only_fields = ('__all__',)

    def get_is_subscribed(self, obj: User) -> bool:
        """Метод для определения подписки пользователя на данного автора.

        Args:
            data: Экземляр класса `User`.

        Returns:
            True - пользователь подписан на автора, иначе False.

        """
        return (
            self.context['request'].user.is_authenticated
            and Follow.objects.filter(
                user=self.context['request'].user,
                author=obj,
            ).exists()
        )


class CustomCreateUserSerializer(UserCreateSerializer):
    """Сериализатор для модели `User` для создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            "password",
        )

    def validate_username(self, username: str) -> str:
        """Валидация запроса на использование me в качестве username.

        Args:
            username: логин.

        Returns:
            В случае успешной валидации возвращает username.

        Raises:
            ValidationError: Ошибка при валидации.

        """
        if username == "me":
            raise serializers.ValidationError('Имя `me` нельзя использовать!')
        return username


class RecipeFollowSerializer(serializers.ModelSerializer):
    """Сериализатор для модели `Recipe` для урезанной выдачи данных."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowResultSerializer(CustomUserSerializer):
    """Сериализатор для отображения подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, user: User) -> OrderedDict[str, Any]:
        """Мeтод для получения рецептов автора.

        Args:
            user: Экземляр класса `User`.

        Returns:
            Возвращает данные из сериализатора `RecipeFollowSerializer`.

        """
        recipes = user.recipes.all()
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit',
            False,
        )
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        return RecipeFollowSerializer(recipes, many=True).data

    def get_recipes_count(self, user: User) -> int:
        """Мeтод для подстчета рецептов у автора.

        Args:
            user: Экземляр класса `User`.

        Returns:
            Возвращает количество рецептов.

        """
        return user.recipes.count()


class FollowsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели `Follows`."""

    class Meta:
        model = Follow
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Нельзя подписаться на одного автора дважды!',
            ),
        ]

    def validate_author(self, data: User) -> User:
        """Валидация запроса на подписку на самого себя.

        Args:
            data: Экземляр класса `User`.

        Returns:
            В случае успешной валидации возвращает экземляр класса `User`.

        Raises:
            ValidationError: Ошибка при валидации.

        """
        if data == self.context['request'].user:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        return data


class Base64ImageField(serializers.ImageField):
    """Кастомный тип поля для картинки."""

    def to_internal_value(self, data: str) -> Any:
        """Декодирует строку base64.

        Args:
            data: Экземляр класса `User`.

        Returns:
            Возвращает файл картинки.

        """
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели `Ingredient`."""

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit', 'id')
        read_only_fields = ('name', 'measurement_unit', 'id')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели `Tag`."""

    class Meta:
        model = Tag
        fields = ('name', 'color', 'slug', 'id')
        read_only_fields = ('name', 'color', 'slug', 'id')


class IngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра ингридиентов в рецепте."""

    id = serializers.IntegerField(source='ingredient.pk')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = IngredientsRecipe
        fields = ('name', 'id', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецептов."""

    author = CustomUserSerializer()
    tags = TagSerializer(
        many=True,
    )
    ingredients = IngredientReadSerializer(
        many=True,
        source='ingredientsrecipe',
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'name',
            'id',
            'image',
            'text',
            'cooking_time',
            'author',
            'tags',
            'ingredients',
            'is_in_shopping_cart',
            'is_favorited',
        )

    def get_is_favorited(self, recipe: Recipe) -> bool:
        """Метод для определения рецепта в избранном у пользователя.

        Args:
            recipe: Экземляр класса `Recipe`.

        Returns:
            True - рецепт в избранном у пользователя, иначе False.

        """
        return (
            self.context['request'].user.is_authenticated
            and Favorite.objects.filter(
                user=self.context['request'].user,
                recipe=recipe,
            ).exists()
        )

    def get_is_in_shopping_cart(self, recipe: Recipe) -> bool:
        """Метод для определения рецепта в корзине у пользователя.

        Args:
            recipe: Экземляр класса `Recipe`.

        Returns:
            True - рецепт в корзине у пользователя, иначе False.

        """
        return (
            self.context['request'].user.is_authenticated
            and Cart.objects.filter(
                user=self.context['request'].user,
                recipe=recipe,
            ).exists()
        )


class IngredientsRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели `IngredientsRecipe`."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientsRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    ingredients = IngredientsRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'name',
            'image',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
            'author',
        )
        read_only_fields = ('author',)

    def validate_tags(self, tags: List[int]) -> List[int]:
        """Валидация запроса на наличие тэгов.

        Args:
            tags: массив id-тэгов.

        Returns:
            В случае успешной валидации возвращает тэги.

        Raises:
            ValidationError: Ошибка при валидации.

        """
        if not tags:
            raise serializers.ValidationError('Выберите тэги')
        return tags

    def validate_ingredients(
        self,
        ingredients: List[Dict[str, int]],
    ) -> List[Dict[str, int]]:
        """Валидация ингридиентов.

        При двух одинаковых ингридиетах и их одинаковых количествах,
        сохраняется только один ингридиент.

        Args:
            ingredients: массив из данных ингридиентов.

        Returns:
            В случае успешной валидации возвращает ингридиенты.

        Raises:
            ValidationError: Ошибка при валидации.

        """
        if not ingredients:
            raise serializers.ValidationError('Добавьте ингридиенты!')
        ingredients = [
            dict(_)
            for _ in set(
                frozenset(ingredient.items()) for ingredient in ingredients
            )
        ]
        new_ing = []
        for ingredient in ingredients:
            if ingredient['id'] in new_ing:
                raise serializers.ValidationError('Ингридиенты повторяются!')
            new_ing.append(ingredient['id'])
        return ingredients

    def to_representation(self, instance: Recipe) -> OrderedDict[str, Any]:
        """Преобразует данные для выдачи.

        Args:
            instance: Экземляр класса `Recipe`.

        Returns:
            Возвращает данные из сериализатора `RecipeReadSerializer`.

        """
        return RecipeReadSerializer(
            instance,
            context={'request': self.context['request']},
        ).data

    def create(self, validated_data: Dict[str, Any]) -> Recipe:
        """Метод для создания рецепта.

        Args:
            validated_data: словарь, доступный после вызова метода
            сериализатора is_valid().

        Returns:
            Экземляр класса `Recipe`.

        """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        utils.create_tags_ingredients(recipe, ingredients, tags)
        return recipe

    def update(self, recipe: Recipe, validated_data: Dict[str, Any]) -> Recipe:
        """Метод для обновления рецепта.

        Args:
            validated_data: словарь, доступный после вызова метода
            сериализатора is_valid().
            recipe: Экземляр класса `Recipe`.

        Returns:
            Экземляр класса `Recipe`.

        """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        IngredientsRecipe.objects.filter(recipe=recipe).delete()
        recipe.tags.clear()
        utils.create_tags_ingredients(recipe, ingredients, tags)
        return super().update(recipe, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели `Favorite`."""

    id = serializers.IntegerField(source='recipe.pk', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True,
    )

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное',
            ),
        ]
        extra_kwargs = {
            'user': {'write_only': True},
            'recipe': {'write_only': True},
        }


class CartSerializer(FavoriteSerializer):
    """Сериализатор для модели `Cart`."""

    class Meta(FavoriteSerializer.Meta):
        model = Cart
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в корзину',
            ),
        ]
