# Импорт необходимых модулей
from django.db.models import Count
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
import base64
import uuid
import logging

# Локальные импорты
from .models import CustomUser, Subscription
from .serializers import (
    UserAuthSerializer,
    UserSerializer,
    UserCreateSerializer,
    SubscriptionSerializer
)
from recipes.models import Recipe
from .pagination import AccountPagination

logger = logging.getLogger(__name__)


class TokenAuthView(viewsets.ViewSet):
    """Управление токенами аутентификации"""

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Получение токена аутентификации"""
        serializer = UserAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token, _ = Token.objects.get_or_create(
            user=serializer.validated_data['user'])
        return Response({'auth_token': token.key})

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Удаление токена аутентификации"""
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserAccountViewSet(viewsets.ModelViewSet):
    """Контроллер для управления пользовательскими аккаунтами"""
    queryset = CustomUser.objects.all().order_by('-date_joined')
    pagination_class = AccountPagination
    serializer_class = UserSerializer

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        return UserCreateSerializer if self.action == 'create' else super().get_serializer_class()

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def current_user(self, request):
        """Получение данных текущего пользователя"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Изменение пароля пользователя"""
        user = request.user
        current_pass = request.data.get('current_password')
        new_pass = request.data.get('new_password')

        if not all([current_pass, new_pass]):
            return Response(
                {'detail': 'Необходимо указать текущий и новый пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not check_password(current_pass, user.password):
            return Response(
                {'detail': 'Неверный текущий пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_pass)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'],
            permission_classes=[IsAuthenticated])
    def profile_image(self, request):
        """Управление аватаром пользователя"""
        if request.method == 'PUT':
            try:
                image_data = request.data.get('avatar')
                if not image_data:
                    return Response(
                        {'detail': 'Необходимо предоставить изображение'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                filename = f'{uuid.uuid4()}.{ext}'

                request.user.avatar.save(
                    filename,
                    ContentFile(base64.b64decode(imgstr)),
                    save=True
                )
                return Response(
                    {'avatar_url': request.user.avatar.url},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                logger.error(f'Ошибка загрузки изображения: {str(e)}')
                return Response(
                    {'detail': 'Ошибка обработки изображения'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # DELETE обработка
        if not request.user.avatar:
            return Response(
                {'detail': 'Аватар отсутствует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        """Управление подписками на пользователей"""
        target_user = self.get_object()

        if request.method == 'POST':
            if Subscription.objects.filter(
                    subscriber=request.user, author=target_user).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if request.user == target_user:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Subscription.objects.create(
                subscriber=request.user,
                author=target_user
            )

            serializer = SubscriptionSerializer(
                subscription,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE обработка
        Subscription.objects.filter(
            subscriber=request.user,
            author=target_user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def following(self, request):
        """Получение списка подписок"""
        following_users = CustomUser.objects.filter(
            subscribers__subscriber=request.user
        ).annotate(
            recipes_count=Count('recipes')
        ).order_by('-subscription__created_at')

        page = self.paginate_queryset(following_users)
        serializer = UserSerializer(
            page if page is not None else following_users,
            many=True,
            context={'request': request}
        )

        # Добавляем информацию о рецептах
        response_data = []
        for user in (page if page is not None else following_users):
            user_data = serializer.data
            recipes = Recipe.objects.filter(author=user)[:3]
            user_data['recipes'] = [
                {
                    'id': recipe.id,
                    'name': recipe.name,
                    'image': request.build_absolute_uri(recipe.image.url),
                    'cooking_time': recipe.cooking_time
                } for recipe in recipes
            ]
            response_data.append(user_data)

        return self.get_paginated_response(
            response_data) if page else Response(response_data)
