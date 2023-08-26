from djoser.serializers import UserSerializer, UserCreateSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from api.models import Follow, Recipe
from rest_framework.validators import UniqueTogetherValidator


User = get_user_model()


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed')
        read_only_fields = '__all__',

    def get_is_subscribed(self, obj):
        return (self.context['request'].user.is_authenticated and Follow.objects.filter(user=self.context['request'].user, author=obj).exists())


class CustomCreateUserSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', "password",)

    def validate_username(self, username):
        if username == "me":
            raise serializers.ValidationError('Имя `me` нельзя использовать!')
        return username


class RecipeFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowResultSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields=('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, user):
        recipes = user.recipes.all()
        recipes_limit = self.context['request'].query_params.get('recipes_limit', False)
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeFollowSerializer(recipes, many=True).data

    def get_recipes_count(self, user):
        return user.recipes.count()


class FollowsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Нельзя подписаться на одного автора дважды!'
            ),
        ]

    def validate_author(self, data):
        if data == self.context['request'].user:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        return data
