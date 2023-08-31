from typing import Any, Dict, List, OrderedDict

from django.core.validators import MaxValueValidator, MinValueValidator
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.constant import MAX_VALUE, MIN_VALUE
from recipe.models import (
    Cart,
    Favorite,
    Ingredient,
    IngredientsRecipe,
    Recipe,
    Tag,
    User,
)
from users.models import Follow


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
        user = self.context['request'].user
        return (
            user.is_authenticated
            and user != obj
            and user.follower.filter(author=obj).exists()
        )


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

    def get_recipes(self, author: User) -> OrderedDict[str, Any]:
        """Мeтод для получения рецептов автора.

        Args:
            user: Экземляр класса `User`.

        Returns:
            Возвращает данные из сериализатора `RecipeFollowSerializer`.

        """
        recipes = author.recipes.all()
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit',
            None,
        )
        if recipes_limit:
            try:
                recipes = recipes[: int(recipes_limit)]
            except ValueError:
                return serializers.ValidationError('Неверное значение!')
        return RecipeFollowSerializer(recipes, many=True).data

    def get_recipes_count(self, author: User) -> int:
        """Мeтод для подстчета рецептов у автора.

        Args:
            user: Экземляр класса `User`.

        Returns:
            Возвращает количество рецептов.

        """
        return author.recipes.count()


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

    def to_representation(self, instance):
        return FollowResultSerializer(
            instance.author, context=self.context,
        ).data


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
        user = self.context['request'].user
        return (
            user.is_authenticated
            and user.favorites.filter(recipe=recipe).exists()
        )

    def get_is_in_shopping_cart(self, recipe: Recipe) -> bool:
        """Метод для определения рецепта в корзине у пользователя.

        Args:
            recipe: Экземляр класса `Recipe`.

        Returns:
            True - рецепт в корзине у пользователя, иначе False.

        """
        user = self.context['request'].user
        return (
            user.is_authenticated and user.carts.filter(recipe=recipe).exists()
        )


class IngredientsRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели `IngredientsRecipe`."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        validators=[
            MaxValueValidator(
                limit_value=MAX_VALUE,
                message='Превышает максималбное значение',
            ),
            MinValueValidator(
                limit_value=MIN_VALUE, message='Укажите превильное количество',
            ),
        ],
    )

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
    cooking_time = serializers.IntegerField(
        validators=[
            MaxValueValidator(
                limit_value=MAX_VALUE,
                message='Превышает максималбное значение',
            ),
            MinValueValidator(
                limit_value=MIN_VALUE, message='Укажите превильное время',
            ),
        ],
    )

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
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Повторяющиеся тэги!')
        return tags

    def validate(self, data):
        """Валидация ингридиентов.

        При двух одинаковых ингридиетах и их одинаковых количествах,
        сохраняется только один ингридиент.

        Args:
            data: данные, переданные в сериалзатор.

        Returns:
            В случае успешной валидации возвращает ингридиенты.

        Raises:
            ValidationError: Ошибка при валидации.

        """
        ingredients = [
            ingredient['id'] for ingredient in data.get('ingredients')
        ]
        if not ingredients:
            raise serializers.ValidationError('Добавьте ингридиенты!')
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError('Одинаковые ингридиенты')
        return data

    def to_representation(self, instance: Recipe) -> OrderedDict[str, Any]:
        """Преобразует данные для выдачи.

        Args:
            instance: Экземляр класса `Recipe`.

        Returns:
            Возвращает данные из сериализатора `RecipeReadSerializer`.

        """
        return RecipeReadSerializer(
            instance,
            context=self.context,
        ).data

    @staticmethod
    def create_tags_ingredients(
        recipe: Recipe,
        ingredients: List[Dict[str, int]],
        tags: List[int],
    ) -> None:
        """Добавление тегов и ингридиентов в рецепт.

        Args:
            recipe: Экземляр класса `Recipe`.
            ingredients: Массив из данных ингридиентов.
            tags: Массив id-тэгов.

        """
        ingredients = [
            IngredientsRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ]
        IngredientsRecipe.objects.bulk_create(ingredients)
        recipe.tags.set(tags)

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
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data,
        )
        self.create_tags_ingredients(recipe, ingredients, tags)
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
        self.create_tags_ingredients(recipe, ingredients, tags)
        return super().update(recipe, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели `Favorite`."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное',
            ),
        ]

    def to_representation(self, instance: Favorite) -> OrderedDict[str, Any]:
        """Преобразует данные для выдачи.

        Args:
            instance: Экземляр класса `Favorite`.

        Returns:
            Возвращает данные из сериализатора `RecipeFollowSerializer`.

        """
        return RecipeFollowSerializer(
            instance.recipe, context=self.context,
        ).data


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
