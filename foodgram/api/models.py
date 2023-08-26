from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7)
    slug = models.SlugField(max_length=200, unique=True)


class Recipe(models.Model):
    ingredients = models.ManyToManyField(Ingredient, through='IngredientsRecipe')
    tags = models.ManyToManyField(Tag)
    image = models.ImageField(
        upload_to='recipe/images/'
    )
    name = models.CharField(max_length=200)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField(validators=(MinValueValidator(1),))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')

    class Meta:
        ordering= ['-id']



class IngredientsRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='ingredientsrecipe')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredientsrecipe')
    amount = models.PositiveIntegerField(validators=(MinValueValidator(1),))


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='carts')


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorites')


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
