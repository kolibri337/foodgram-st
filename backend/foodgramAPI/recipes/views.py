from http import HTTPStatus
from collections import defaultdict

# Сторонние библиотеки
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Локальные импорты
from .filters import RecipeFilter, IngredientFilter
from .models import Recipe, Ingredient, FavoriteRecipe, ShoppingCartRecipe
from .paginations import RecipePaginator
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    FavoriteRecipeSerializer,
    ShoppingCartRecipeSerializer
)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для работы с ингредиентами
    """
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для работы с рецептами: CRUD + действия "избранное", "список покупок"
    """
    queryset = Recipe.objects.all()
    pagination_class = RecipePaginator
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_permissions(self):
        if self.action in [
            'create', 'update', 'partial_update',
            'destroy', 'add_to_shopping_cart',
            'remove_from_shopping_cart',
            'download_shopping_list'
        ]:
            return [IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {"error": "Вы не можете редактировать чужие рецепты"},
                status=HTTPStatus.FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {"error": "Удаление чужих рецептов запрещено"},
                status=HTTPStatus.FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """
        Расширенный queryset с фильтрацией по избранному и списку покупок
        """
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1':
            queryset = queryset.filter(favorites__user=user)
        elif is_favorited == '0':
            queryset = queryset.exclude(favorites__user=user)

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart == '1':
            queryset = queryset.filter(shopping_cart__user=user)
        elif is_in_shopping_cart == '0':
            queryset = queryset.exclude(shopping_cart__user=user)

        return queryset

    @action(detail=True, methods=['get'], url_path='short-link')
    def generate_short_url(self, request, pk=None):
        """
        Генерация короткой ссылки на рецепт
        """
        recipe = self.get_object()
        short_code = ''.join(
            [c for c in recipe.name if c.isalnum()])[:6] or 'default'
        return Response(
            {'short-link': f'https://foodgram.ru/s/ {short_code}'}, status=HTTPStatus.OK)

    @action(detail=True, methods=['post'], url_path='add-to-favorites')
    def add_to_favorites(self, request, pk=None):
        """
        Добавить рецепт в избранное
        """
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = FavoriteRecipeSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(detail=True, methods=['delete'], url_path='remove-from-favorites')
    def remove_from_favorites(self, request, pk=None):
        """
        Удалить рецепт из избранного
        """
        recipe = get_object_or_404(Recipe, id=pk)
        deleted, _ = FavoriteRecipe.objects.filter(
            user=request.user, recipe=recipe).delete()
        if deleted == 0:
            return Response(
                {"detail": "Рецепт не найден в избранном"},
                status=HTTPStatus.BAD_REQUEST
            )
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='add-to-shopping-cart')
    def add_to_shopping_cart(self, request, pk=None):
        """
        Добавить рецепт в список покупок
        """
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = ShoppingCartRecipeSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(detail=True, methods=['delete'],
            url_path='remove-from-shopping-cart')
    def remove_from_shopping_cart(self, request, pk=None):
        """
        Удалить рецепт из списка покупок
        """
        recipe = get_object_or_404(Recipe, id=pk)
        deleted, _ = ShoppingCartRecipe.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if deleted == 0:
            return Response(
                {"detail": "Рецепт не найден в списке покупок"},
                status=HTTPStatus.BAD_REQUEST
            )
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='shopping-cart')
    def download_shopping_list(self, request):
        """
        Скачать список покупок в формате текстового файла
        """
        if not request.user.is_authenticated:
            return Response(
                {"error": "Пожалуйста, войдите в систему"},
                status=HTTPStatus.UNAUTHORIZED
            )

        cart_items = ShoppingCartRecipe.objects.filter(
            user=request.user).prefetch_related('recipe__recipe_ingredients')
        if not cart_items.exists():
            return Response(
                {"error": "Ваш список покупок пуст"},
                status=HTTPStatus.NOT_FOUND
            )

        ingredients_map = defaultdict(int)
        for item in cart_items:
            for ri in item.recipe.recipe_ingredients.all():
                key = (ri.ingredient.name, ri.ingredient.measurement_unit)
                ingredients_map[key] += ri.amount

        content = ["Список покупок:\n"]
        for (name, unit), amount in ingredients_map.items():
            content.append(f"{name} ({unit}) — {amount}")

        filename = "shopping_list.txt"
        response = FileResponse(
            "\n".join(content),
            as_attachment=True,
            filename=filename)
        return response
