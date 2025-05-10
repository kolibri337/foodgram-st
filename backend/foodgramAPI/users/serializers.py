from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from .models import CustomUser, Subscription
from utils.validators import validate_user_identifier as validate_username


class UserAuthSerializer(serializers.Serializer):
    """Сериализатор для аутентификации"""
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, data):
        user = authenticate(
            email=data.get('email'),
            password=data.get('password')
        )
        if not user:
            raise ValidationError("Неверные учетные данные")
        if not user.is_active:
            raise ValidationError("Учетная запись неактивна")
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    """Основной сериализатор пользователя"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.subscribers.filter(subscriber=request.user).exists()
        )


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации"""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'username',
            'password',
            'first_name',
            'last_name']

    def validate_email(self, value):
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise ValidationError("Пользователь с таким email уже существует")
        return value

    def validate_username(self, value):
        validate_username(value)
        if CustomUser.objects.filter(username__iexact=value).exists():
            raise ValidationError("Пользователь с таким именем уже существует")
        return value

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок"""
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'recipes_count'
        ]

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_is_subscribed(self, obj):
        return True
