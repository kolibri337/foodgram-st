from django.contrib import admin
from .models import Ingredient, Recipe, RecipeIngredient, FavoriteRecipe, ShoppingCartRecipe


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    ordering = ("name",)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1

@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "recipe", "ingredient", "amount")
    search_fields = ("recipe__name", "ingredient__name")


@admin.register(ShoppingCartRecipe)
class ShoppingCartRecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "author", "cooking_time", "favorites_count")
    list_filter = ("author", "name", "ingredients")
    search_fields = ("name", "author__username")
    inlines = [RecipeIngredientInline]

    fieldsets = (
        (None, {
            "fields": (
                "name", "author", "image",
                "description", "cooking_time"
            )
        }),
    )

    def favorites_count(self, obj):
        return FavoriteRecipe.objects.filter(recipe=obj).count()  
    favorites_count.short_description = "Добавлено в избранное"

@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin): 
    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
