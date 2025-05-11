from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class AccountManager(BaseUserManager):
    """Кастомный менеджер для работы с пользовательскими аккаунтами"""

    def create_user(self, email, username, password=None, **extra):
        """Создание обычного пользовательского аккаунта"""
        extra.setdefault('is_active', True)
        extra.setdefault('is_staff', False)
        extra.setdefault('is_superuser', False)
        return self._create_account(email, username, password, **extra)

    def create_superuser(self, email, username, password, **extra):
        """Создание административного аккаунта"""
        extra.update({
            'is_active': True,
            'is_staff': True,
            'is_superuser': True
        })

        if extra.get('is_staff') is not True:
            raise ValueError('Администратор должен иметь is_staff=True')
        if extra.get('is_superuser') is not True:
            raise ValueError('Администратор должен иметь is_superuser=True')

        return self._create_account(email, username, password, **extra)

    def _create_account(self, email, username, password=None, **extra):
        """Базовый метод создания аккаунта"""

        if not email:
            raise ValueError('Необходимо указать email')
        if not username:
            raise ValueError('Требуется имя пользователя')

        normalized_email = self.normalize_email(email)
        account = self.model(
            email=normalized_email,
            username=username,
            **extra
        )

        account.set_password(password)
        account.save(using=self._db)
        return account
