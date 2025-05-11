from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
import tempfile
from PIL import Image
from rest_framework.authtoken.models import Token
import base64
import uuid

User = get_user_model()


def get_base64_image():
    """Создание временного изображения в формате Base64"""
    image = Image.new('RGB', (100, 100))
    tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
    image.save(tmp_file, 'jpeg')
    tmp_file.seek(0)
    encoded_string = base64.b64encode(tmp_file.read()).decode('utf-8')
    return f"data:image/jpeg;base64,{encoded_string}"


class SubscriptionTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            username="user1",
            password="testpassword"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            username="user2",
            password="testpassword"
        )
        self.token = Token.objects.create(user=self.user1)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_create_subscription(self):
        url = f"/api/users/{self.user2.id}/subscribe/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_self_subscription_prevention(self):
        url = f"/api/users/{self.user1.id}/subscribe/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_avatar_upload(self):
        url = "/api/users/me/avatar/"
        image_data = get_base64_image()
        data = {'avatar': image_data}
        response = self.client.put(
            url, data, format='json')  # Формат JSON для Base64
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserAccountTests(TestCase):
    def test_user_registration(self):
        url = "/api/users/"
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'NewPass123'
        }
        response = self.client.post(url, data)  # Без аутентификации
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
