from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from api.constant import MAX_LENGTH, MAX_LENGTH_COLOR, MAX_VALUE, MIN_VALUE
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(verbose_name='Ингридиент', max_length=MAX_LENGTH)
    measurement_unit = models.CharField(
        verbose_name='Единица измерения', max_length=MAX_LENGTH,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='Ингридиент уже существует!',
            ),
        )

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название тэга', max_length=MAX_LENGTH,
    )
    color = ColorField(verbose_name='Цвет тэга', max_length=MAX_LENGTH_COLOR)
    slug = models.SlugField(
        verbose_name='Слаг тэга', max_length=MAX_LENGTH, unique=True,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientsRecipe',
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Тэги', related_name='recipes',
    )
    image = models.ImageField(
        verbose_name='Изображение', upload_to='recipe/images/',
    )
    name = models.CharField(
        verbose_name='Название рецепта', max_length=MAX_LENGTH,
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(MIN_VALUE),
            MaxValueValidator(MAX_VALUE),
        ),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    pub_date = models.DateTimeField(verbose_name='Описание', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return self.name


class IngredientsRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='ingredientsrecipe',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='ingredientsrecipe',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(MIN_VALUE),
            MaxValueValidator(MAX_VALUE),
        ),
    )

    class Meta:
        verbose_name = 'Количество ингридиента'
        verbose_name_plural = 'Количества ингридиентов'

    def __str__(self) -> str:
        return f'{self.ingredient} - {self.amount}'


class DefaultModel(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f'{self.user} add {self.recipe}'


class Cart(DefaultModel):
    class Meta:
        verbose_name = 'Корзине'
        verbose_name_plural = 'Корзина'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='Рецепт уже добавлен',
            ),
        )
        default_related_name = 'carts'


class Favorite(DefaultModel):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='Рецепт уже добавлен в избранное',
            ),
        )
        default_related_name = 'favorites'
