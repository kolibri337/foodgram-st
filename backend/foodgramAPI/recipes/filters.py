from django_filters import rest_framework as filters
from django.db.models import Exists, OuterRef
from .models import Recipe, FavoriteRecipe, ShoppingCartRecipe


class RecipeFilter(filters.FilterSet):
    """
    Кастомный фильтр для рецептов:
    - По автору
    - По наличию в избранном
    - По наличию в списке покупок
    """
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрация рецептов по наличию в избранном у текущего пользователя
        """
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрация рецептов по наличию в списке покупок у текущего пользователя
        """
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(shopping_cart_recipes__user=user)
        return queryset
