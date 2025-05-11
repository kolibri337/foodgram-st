from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Ingredient, FavoriteRecipe, ShoppingCartRecipe, RecipeIngredient
from PIL import Image
import tempfile
import base64
import uuid
from django.core.files import File

User = get_user_model()


def get_base64_image():
    image = Image.new('RGB', (100, 100))
    tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
    image.save(tmp_file, 'jpeg')
    tmp_file.seek(0)
    encoded_string = base64.b64encode(tmp_file.read()).decode('utf-8')
    return f"data:image/jpeg;base64,{encoded_string}"


class RecipeAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpassword"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        self.ingredient = Ingredient.objects.create(
            name="Соль", measurement_unit="г")

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file, 'jpeg')
        tmp_file.seek(0)

        self.recipe = Recipe.objects.create(
            author=self.user,
            name="Тестовый рецепт",
            text="Описание рецепта",
            cooking_time=15,
        )
        self.recipe.image.save('test.jpg', File(tmp_file))
        tmp_file.close()

        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient,
            amount=100)

    def test_add_to_favorite(self):
        url = f"/api/recipes/{self.recipe.id}/add-to-favorites/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_remove_from_favorite(self):
        FavoriteRecipe.objects.create(user=self.user, recipe=self.recipe)
        url = f"/api/recipes/{self.recipe.id}/remove-from-favorites/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_add_to_shopping_cart(self):
        url = f"/api/recipes/{self.recipe.id}/add-to-shopping-cart/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_remove_from_shopping_cart(self):
        ShoppingCartRecipe.objects.create(user=self.user, recipe=self.recipe)
        url = f"/api/recipes/{self.recipe.id}/remove-from-shopping-cart/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_recipe_list(self):
        response = self.client.get("/api/recipes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_ingredient_list(self):
        response = self.client.get("/api/ingredients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_search_ingredient(self):
        response = self.client.get("/api/ingredients/?name=Соль")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data[0]["name"], "Соль")
