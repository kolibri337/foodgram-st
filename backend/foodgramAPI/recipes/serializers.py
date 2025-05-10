from rest_framework import serializers
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from ..models import Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart
from users.serializers import UserSerializer
from ..fields import ImageDataField

class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient"""
    
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'unit')

class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецептов в избранное"""
    
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
    
    def to_representation(self, instance):
        request = self.context.get('request')
        recipe = instance.recipe
        return {
            'id': recipe.id,
            'name': recipe.name,
            'image': self._build_image_url(recipe, request),
            'cooking_time': recipe.time_minutes
        }
    
    def _build_image_url(self, recipe, request):
        if not request:
            return recipe.image.url
        return request.build_absolute_uri(recipe.image.url)

class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для управления списком покупок"""
    
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
    
    def to_representation(self, instance):
        recipe = instance.recipe
        request = self.context.get('request')
        return {
            'id': recipe.id,
            'name': recipe.name,
            'image': request.build_absolute_uri(recipe.image.url) if request else recipe.image.url,
            'time': recipe.cooking_time
        }

class RecipeIngredientSerializer(serializers.Serializer):
    """Вспомогательный сериализатор для работы с ингредиентами в рецепте"""
    
    ingredient_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class RecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор рецептов"""
    
    image = ImageDataField()
    ingredients = RecipeIngredientSerializer(many=True)
    
    class Meta:
        model = Recipe
        fields = ('id', 'title', 'image', 'description', 'time_minutes', 'ingredients')

    def validate(self, data):
        self._validate_cooking_time(data)
        self._validate_image(data)
        self._validate_ingredients(data)
        return data
    
    def _validate_cooking_time(self, data):
        time = data.get('time_minutes')
        if time is not None and time < 5:  # Минимум 5 минут
            raise serializers.ValidationError({
                'time_minutes': 'Время готовки должно быть не менее 5 минут'
            })
    
    def _validate_image(self, data):
        image = data.get('image')
        if not image:
            raise serializers.ValidationError({
                'image': 'Изображение обязательно'
            })
    
    def _validate_ingredients(self, data):
        ingredients = data.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент'
            })
        
        seen_ids = set()
        for item in ingredients:
            ing_id = item.get('ingredient_id')
            
            if not Ingredient.objects.filter(id=ing_id).exists():
                raise serializers.ValidationError({
                    'ingredients': f'Ингредиент {ing_id} не существует'
                })
                
            if ing_id in seen_ids:
                raise serializers.ValidationError({
                    'ingredients': f'Дублирование ингредиента {ing_id}'
                })
                
            seen_ids.add(ing_id)
    
    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self._save_ingredients(recipe, ingredients)
        return recipe
    
    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        recipe = super().update(instance, validated_data)
        
        if ingredients:
            recipe.recipe_ingredients.all().delete()
            self._save_ingredients(recipe, ingredients)
            
        return recipe
    
    def _save_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=item['ingredient_id']),
                quantity=item['quantity']
            ) for item in ingredients_data
        ])

class RecipeDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального отображения рецептов"""
    
    author = UserSerializer(read_only=True)
    image = ImageDataField()
    is_favorite = serializers.SerializerMethodField()
    is_in_cart = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'title', 'image', 'description', 
            'time_minutes', 'is_favorite', 'is_in_cart', 'ingredients'
        )
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated and 
            obj.favorite_recipes.filter(user=request.user).exists()
        )
    
    def get_is_in_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated and 
            obj.shopping_recipes.filter(user=request.user).exists()
        )
    
    def get_ingredients(self, obj):
        return [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'unit': ri.ingredient.unit,
                'quantity': ri.quantity
            } for ri in obj.recipe_ingredients.select_related('ingredient')
        ]
