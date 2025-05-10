from rest_framework import serializers
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from ..models import Ingredient, Recipe, RecipeIngredient, FavoriteRecipe, ShoppingCartRecipe
from users.serializers import UserSerializer
from ..fields import ImageDataField


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для связи рецепта и ингредиента"""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'unit', 'amount')


class BaseRecipeActionSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для действий с рецептами"""

    def to_representation(self, instance):
        request = self.context.get('request')
        recipe = instance.recipe

        return {
            'id': recipe.id,
            'name': recipe.name,
            'image': self._get_image_url(recipe, request),
            'cooking_time': recipe.cooking_time
        }

    def _get_image_url(self, recipe, request):
        if not request:
            return recipe.image.url
        return request.build_absolute_uri(recipe.image.url)


class FavoriteRecipeSerializer(BaseRecipeActionSerializer):
    """Сериализатор для избранного"""

    class Meta:
        model = FavoriteRecipe
        fields = ('user', 'recipe')


class ShoppingCartRecipeSerializer(BaseRecipeActionSerializer):
    """Сериализатор для списка покупок"""

    class Meta:
        model = ShoppingCartRecipe
        fields = ('user', 'recipe')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецептов"""
    image = ImageDataField()
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        required=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'cooking_time',
            'recipe_ingredients')
        extra_kwargs = {
            'cooking_time': {'min_value': 5}
        }

    def validate(self, data):
        ingredients = data.get('recipe_ingredients', [])

        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Необходим хотя бы один ингредиент'
            })

        ingredient_ids = [item['ingredient']['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться'
            })

        return data

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        recipe = super().update(instance, validated_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._create_ingredients(recipe, ingredients_data)

        return recipe

    def _create_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['ingredient']['id'],
                amount=item['amount']
            ) for item in ingredients_data
        ])


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов"""
    author = UserSerializer(read_only=True)
    image = ImageDataField()
    is_favorite = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text',
            'cooking_time', 'is_favorite', 'is_in_shopping_cart', 'recipe_ingredients'
        )

    def get_is_favorite(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and obj.favorites.filter(
            user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and obj.shopping_cart.filter(
            user=user).exists()
