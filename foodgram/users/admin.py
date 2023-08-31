from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Follow, User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        'first_name',
        'last_name',
        'pk',
        'email',
        'username',
        'count_recipes',
        'count_followers',
    )
    list_filter = ('email', 'first_name')

    def count_recipes(self, user):
        return user.recipes.count()

    count_recipes.short_description = "Количество рецептов"

    def count_followers(self, user):
        return user.follower.count()

    count_followers.short_description = "Количество подписок"


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user', 'author')
