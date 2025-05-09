from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from .managers import AccountManager

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя с email в качестве идентификатора"""
    
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
        help_text='Обязательное поле. Максимум 254 символа.',
        error_messages={
            'unique': "Пользователь с таким email уже зарегистрирован.",
        },
    )
    username = models.CharField(
        'Логин',
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Недопустимые символы в имени пользователя'
            )
        ],
        help_text='Обязательное поле. До 150 символов. Только буквы, цифры и @/./+/-/_',
    )
    first_name = models.CharField('Имя', max_length=150, blank=True)
    last_name = models.CharField('Фамилия', max_length=150, blank=True)
    date_joined = models.DateTimeField('Дата регистрации', default=timezone.now)
    is_active = models.BooleanField('Активный', default=True)
    is_staff = models.BooleanField('Персонал', default=False)
    
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars/%Y/%m/%d/',
        blank=True,
        null=True,
    )
    
    objects = AccountManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-date_joined',)
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'username'],
                name='unique_auth'
            )
        ]
    
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()
    
    def clean(self):
        super().clean()
        if self.username.lower() == 'me':
            raise ValidationError("Имя пользователя 'me' не разрешено.")


class Subscription(models.Model):
    """Модель подписки пользователей друг на друга"""
    
    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )
    created_at = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F('author')),
                name='prevent_self_subscription'
            )
        ]
    
    def __str__(self):
        return f'{self.subscriber} -> {self.author}'
