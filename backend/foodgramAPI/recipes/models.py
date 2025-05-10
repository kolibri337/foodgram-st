from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента"""
    name = models.CharField(
        max_length=128,
        verbose_name='Наименование',
        help_text='Введите название ингредиента (например, капуста)',
        db_index=True,
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения',
        help_text='Укажите единицу измерения (например, мл)',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_with_unit'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_recipes',
        verbose_name='Автор рецепта',
        help_text='Выберите автора рецепта',
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название блюда',
        help_text='Введите название рецепта (например, борщ)',
        db_index=True,
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Фото рецепта',
        help_text='Загрузите изображение готового блюда',
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Опишите процесс приготовления',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='used_in_recipes',
        verbose_name='Ингредиенты',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (мин)',
        validators=[MinValueValidator(1)],
        help_text='Укажите время приготовления в минутах',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Связь между рецептом и ингредиентом"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_usage',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)],
        help_text='Укажите количество ингредиента',
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        ordering = ['recipe', 'ingredient']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient_entry'
            )
        ]

    def __str__(self):
        return f'{self.recipe.name} — {self.ingredient.name} ({self.amount} {self.ingredient.measurement_unit})'


class BaseRecipeRelation(models.Model):
    """Абстрактная модель связи пользователя с рецептом"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        ordering = ['user']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_entry'
            )
        ]

    def __str__(self):
        return f'{self.user.username} → {self.recipe.name}'


class FavoriteRecipe(BaseRecipeRelation):
    """Модель избранных рецептов"""

    class Meta(BaseRecipeRelation.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_in_favorites'
            )
        ]


class ShoppingCartRecipe(BaseRecipeRelation):
    """Модель списка покупок"""

    class Meta(BaseRecipeRelation.Meta):
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_in_shopping_cart'
            )
        ]
