from django.contrib import admin
from django.db.models import Count
from django.contrib.admin import SimpleListFilter
from .models import Ingredient, Recipe, RecipeIngredient, FavoriteRecipe, ShoppingCartRecipe

# Кастомный фильтр для проверки наличия ингредиентов


class HasIngredientsFilter(SimpleListFilter):
    title = 'Ингредиенты'
    parameter_name = 'has_ingredients'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть ингредиенты'),
            ('no', 'Нет ингредиентов'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(ingredients__isnull=False)
        if self.value() == 'no':
            return queryset.filter(ingredients__isnull=True)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    ordering = ("name",)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    # Автозаполнение для поля ingredient
    autocomplete_fields = ['ingredient']


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "recipe", "ingredient", "amount")
    search_fields = ("recipe__name", "ingredient__name")
    autocomplete_fields = ['recipe', 'ingredient']


@admin.register(ShoppingCartRecipe)
class ShoppingCartRecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
    autocomplete_fields = ['user', 'recipe']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "author", "cooking_time", "favorites_count")
    list_filter = ("author", "name", HasIngredientsFilter)
    search_fields = ("name", "author__username")
    inlines = [RecipeIngredientInline]
    raw_id_fields = ['author']
    ordering = ('-id',)
    list_per_page = 6

    fieldsets = (
        (None, {
            "fields": (
                "name", "author", "image",
                "description", "cooking_time"
            )
        }),
    )

    # Оптимизация счетчика избранных рецептов
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count('favorited_by'))

    def favorites_count(self, obj):
        return obj.favorites_count
    favorites_count.admin_order_field = 'favorites_count'
    favorites_count.short_description = "Добавлено в избранное"


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
    autocomplete_fields = ['user', 'recipe']
