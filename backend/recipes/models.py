from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

User = settings.AUTH_USER_MODEL

class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=128
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique_ingredient_unit')
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        'Название рецепта',
        max_length=256,
        db_index=True
    )
    
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/',
        help_text='Загрузите изображение рецепта'
       
    )
   
    text = models.TextField(
        'Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes_containing',
        verbose_name='Ингредиенты'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                getattr(settings, 'MIN_COOKING_TIME', 1),
                message=f'Время приготовления должно быть не меньше {getattr(settings, "MIN_COOKING_TIME", 1)} минуты'
            ),
            MaxValueValidator(32767, message='Слишком долгое время приготовления!')
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name='ingredient_in_recipes',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                getattr(settings, 'MIN_INGREDIENT_AMOUNT', 1),
                message=f'Количество должно быть не меньше {getattr(settings, "MIN_INGREDIENT_AMOUNT", 1)}'
            ),
            MaxValueValidator(32767, message='Слишком большое количество')
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return f'{self.ingredient.name} ({self.amount} {self.ingredient.measurement_unit}) in "{self.recipe.name}"'


class UserRecipeRelationBase(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    added_at = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )

    class Meta:
        abstract = True
        ordering = ['-added_at']


class Favorite(UserRecipeRelationBase):
    class Meta(UserRecipeRelationBase.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_user_favorite_recipe')
        ]

    def __str__(self):
        return f'{self.user} added "{self.recipe}" to favorites'


class ShoppingCart(UserRecipeRelationBase):
    class Meta(UserRecipeRelationBase.Meta):
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        default_related_name = 'shopping_cart_items'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_user_shopping_cart_recipe')
        ]

    def __str__(self):
        return f'{self.user} added "{self.recipe}" to shopping cart'