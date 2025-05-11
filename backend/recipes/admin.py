from django.contrib import admin
from .models import Recipe, Ingredient, IngredientInRecipe, Favorite, ShoppingCart

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_usage_count')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)

    @admin.display(description='Используется в рецептах')
    def recipe_usage_count(self, obj):
        return obj.recipes.count()


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1
    autocomplete_fields = ('ingredient',)
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'pub_date', 'favorite_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('author__username', 'pub_date')
    readonly_fields = ('pub_date', 'favorite_count_display')
    inlines = [IngredientInRecipeInline]

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        return obj.favorites.count()

    @admin.display(description='Добавлений в избранное')
    def favorite_count_display(self, obj):
        return self.favorite_count(obj)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added_at')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('added_at',)
    autocomplete_fields = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added_at')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('added_at',)
    autocomplete_fields = ('user', 'recipe')