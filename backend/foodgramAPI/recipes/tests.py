from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Ingredient, FavoriteRecipe, ShoppingCartRecipe, RecipeIngredient

User = get_user_model()


class RecipeAPITestCase(APITestCase):
    def setUp(self):
        # Создаем пользователя
        self.user = User.objects.create_user(
            username="testuser", password="password"
        )

        # Создаем ингредиенты (используем первый из предоставленных)
        self.ingredient1 = Ingredient.objects.create(
            name="абрикосовое варенье",
            measurement_unit="г"
        )
        self.ingredient2 = Ingredient.objects.create(
            name="абрикосовый сок",
            measurement_unit="мл"
        )

        # Создаем рецепт
        self.recipe = Recipe.objects.create(
            author=self.user,
            name="Тестовый рецепт",
            description="Описание рецепта",
            cooking_time=15,
        )

        # Добавляем ингредиент в рецепт через RecipeIngredient
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient1,
            amount=100
        )

        # Логинимся
        self.client.login(username="testuser", password="password")

    def test_recipe_list(self):
        """Проверяем получение списка рецептов"""
        response = self.client.get("/api/recipes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_add_to_favorite(self):
        """Проверяем добавление рецепта в избранное"""
        response = self.client.post(
            f"/api/recipes/{self.recipe.id}/add-to-favorites/"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            FavoriteRecipe.objects.filter(user=self.user, recipe=self.recipe)
            .exists()
        )

    def test_remove_from_favorite(self):
        """Проверяем удаление рецепта из избранного"""
        FavoriteRecipe.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.delete(
            f"/api/recipes/{self.recipe.id}/remove-from-favorites/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            FavoriteRecipe.objects.filter(user=self.user, recipe=self.recipe)
            .exists()
        )

    def test_add_to_shopping_cart(self):
        """Проверяем добавление рецепта в список покупок"""
        response = self.client.post(
            f"/api/recipes/{self.recipe.id}/add-to-shopping-cart/"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ShoppingCartRecipe.objects.filter(user=self.user, recipe=self.recipe)
            .exists()
        )

    def test_remove_from_shopping_cart(self):
        """Проверяем удаление рецепта из списка покупок"""
        ShoppingCartRecipe.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.delete(
            f"/api/recipes/{self.recipe.id}/remove-from-shopping-cart/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT) 
        self.assertFalse(
            ShoppingCartRecipe.objects.filter(user=self.user, recipe=self.recipe)
            .exists()
        )

    def test_ingredient_list(self):
        """Проверяем получение списка ингредиентов"""
        response = self.client.get("/api/ingredients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_search_ingredient(self):
        """Проверяем поиск ингредиента по имени"""
        response = self.client.get("/api/ingredients/?name=абрико")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data[0]["name"], "абрикосовое варенье")