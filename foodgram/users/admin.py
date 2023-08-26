from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'pk', 'email', 'username')
    list_filter = ('email', 'first_name')
