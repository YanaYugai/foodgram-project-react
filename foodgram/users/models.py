from django.contrib.auth.models import AbstractUser
from django.db import models

from api.constant import MAX_LENGTH_EMAIL, MAX_LENGTH_USER


class User(AbstractUser):
    first_name = models.CharField(
        verbose_name='Имя', max_length=MAX_LENGTH_USER,
    )
    last_name = models.CharField(
        verbose_name='Фамилия', max_length=MAX_LENGTH_USER,
    )
    email = models.EmailField(
        verbose_name='Почта', max_length=MAX_LENGTH_EMAIL, unique=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return f'{self.first_name}-{self.last_name}'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'), name='Подписка сушествует.',
            ),
            models.CheckConstraint(
                name='Подписка на самого себя',
                check=~models.Q(author=models.F("user")),
            ),
        )

    def __str__(self) -> str:
        return f'{self.user} подписан {self.author}'
