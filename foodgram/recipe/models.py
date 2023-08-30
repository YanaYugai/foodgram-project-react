from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientsRecipe',
    )
    tags = models.ManyToManyField(Tag, related_name='recipes')
    image = models.ImageField(upload_to='recipe/images/')
    name = models.CharField(max_length=200)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField(
        validators=(MinValueValidator(1),),
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-id']


class IngredientsRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='ingredientsrecipe',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredientsrecipe',
    )
    amount = models.PositiveIntegerField(validators=(MinValueValidator(1),))

    class Meta:
        verbose_name = 'Количество ингридиента'
        verbose_name_plural = 'Количества ингридиентов'


class Cart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='carts',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='carts',
    )

    class Meta:
        verbose_name = 'Корзине'
        verbose_name_plural = 'Корзина'


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
