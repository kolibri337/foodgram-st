from django_filters import rest_framework as filters

class RecipeFilter(filters.FilterSet):
    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']