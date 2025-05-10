from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
import tempfile
from PIL import Image

User = get_user_model()


class SubscriptionTests(TestCase):
    """Тесты функционала подписок"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user1)

    def test_create_subscription(self):
        """Тест создания подписки"""
        url = reverse('user-follow', kwargs={'pk': self.user2.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            self.user1.subscriptions.filter(
                author=self.user2).exists())

    def test_self_subscription_prevention(self):
        """Тест защиты от самоподписки"""
        url = reverse('user-follow', kwargs={'pk': self.user1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ImageUploadTests(TestCase):
    """Тесты загрузки изображений"""

    @staticmethod
    def get_temporary_image():
        """Создание временного изображения для тестов"""
        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file, 'jpeg')
        tmp_file.seek(0)
        return tmp_file

    def test_avatar_upload(self):
        """Тест загрузки аватара"""
        url = reverse('user-profile-image')
        with self.get_temporary_image() as image:
            data = {'avatar': image}
            response = self.client.put(url, data, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('avatar_url', response.data)

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)


class UserAccountTests(TestCase):
    """Тесты для функционала пользователей"""

    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPass123'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='AdminPass123'
        )

    def test_user_registration(self):
        """Тест регистрации нового пользователя"""
        url = reverse('user-list')
        data = {
            'email': 'new@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'NewPass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='new@example.com').exists())

    def test_authentication(self):
        """Тест аутентификации пользователя"""
        url = reverse('token-auth')
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)

    def test_password_change(self):
        """Тест изменения пароля"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-change-password')
        data = {
            'current_password': self.user_data['password'],
            'new_password': 'NewSecurePass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(self.user.check_password('NewSecurePass123'))
