from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField

from django.conf import settings 

from .models import (
    Ingredient, Recipe, IngredientInRecipe, 
    Favorite, ShoppingCart
)
from users.serializers import CustomUserSerializer

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer): 
    id = serializers.PrimaryKeyRelatedField( 
        source='ingredient',
        queryset=Ingredient.objects.all(),
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(
        min_value=settings.MIN_INGREDIENT_AMOUNT, 
        max_value=32767
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer): 
    image = Base64ImageField(required=False, allow_null=True, read_only=True) 

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeListSerializer(serializers.ModelSerializer): 
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer( 
        many=True, source='recipe_ingredients', read_only=True) 
    image = Base64ImageField(read_only=True) 
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author',
            'ingredients', 'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(many=True) 
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(
        min_value=settings.MIN_COOKING_TIME 
    )

    class Meta:
        model = Recipe
        fields = ('ingredients',
                  'image', 'name', 'text', 'cooking_time')
       
    def validate_ingredients(self, data): 
        if not data:
            raise serializers.ValidationError(
                {'ingredients': 'Нужно добавить хотя бы один ингредиент.'})

        ingredient_ids = set()
        for item_data in data:
            ingredient = item_data.get('ingredient') 
            if not ingredient:
                 raise serializers.ValidationError({'ingredients': 'Не указан ID ингредиента.'})

            if ingredient.id in ingredient_ids:
                raise serializers.ValidationError(
                    {'ingredients': f'Ингредиент "{ingredient.name}" добавлен дважды.'}
                )
            ingredient_ids.add(ingredient.id)
        return data

    def _manage_ingredients(self, recipe, ingredients_data):
        IngredientInRecipe.objects.filter(recipe=recipe).delete()
        recipe_ingredients_to_create = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient=item_data['ingredient'],
                amount=item_data['amount']
            ) for item_data in ingredients_data
        ]
        IngredientInRecipe.objects.bulk_create(recipe_ingredients_to_create)

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        author = self.context.get('request').user
        
        recipe = Recipe.objects.create(
            author=author,
            name=validated_data.get('name'),
            text=validated_data.get('text'),
            cooking_time=validated_data.get('cooking_time'),
            image=validated_data.get('image')
        )
        self._manage_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        if ingredients_data is not None:
            self._manage_ingredients(instance, ingredients_data)
        instance.save()
        return instance

    def to_representation(self, instance):
        instance.refresh_from_db()
        return RecipeListSerializer(instance, context=self.context).data 


class RecipeGetShortLinkSerializer(serializers.Serializer):
   
    actual_link = serializers.URLField(source='short-link')

   
from .models import (
    Ingredient, Recipe, IngredientInRecipe as RecipeIngredient,
    Favorite, ShoppingCart
)

from users.serializers import CustomUserSerializer

User = get_user_model()

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

class RecipeIngredientSerializer(serializers.ModelSerializer):
    
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', 
        queryset=Ingredient.objects.all(),
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(
        min_value=1, 
        max_value=32767 
       
    )

    class Meta:
        model = RecipeIngredient 
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
   
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients', read_only=True)
   
    image = serializers.ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 
            'ingredients', 'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_image(self, obj):
        request = self.context.get('request')
       
        if obj.image and hasattr(obj.image, 'url') and obj.image.url:
            if request:
                
                return request.build_absolute_uri(obj.image.url)
            else:
                
                return obj.image.url
      
        return ""
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
   
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(
        min_value=1 
    )

    class Meta:
        model = Recipe
        fields = ('ingredients', 
                  'image', 'name', 'text', 'cooking_time')
       
        read_only_fields = ('author',) 


    def validate_image(self, value):
        
        if value is None or not getattr(value, 'name', None):
             raise serializers.ValidationError("Поле image не может быть пустым.")
        return value 
    
    def validate(self, data):
        ingredients = data.get('ingredients')
       
        image_data = data.get('image') 
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужно добавить хотя бы один ингредиент.'})

        ingredient_ids = set()
        for item_data in ingredients:
           
            ingredient = item_data.get('ingredient')
            if not ingredient: 
                 raise serializers.ValidationError({'ingredients': 'Не указан ID ингредиента.'})

            if ingredient.id in ingredient_ids:
                raise serializers.ValidationError(
                    {'ingredients': f'Ингредиент "{ingredient.name}" добавлен дважды.'}
                )
            ingredient_ids.add(ingredient.id)
            

        return data

    def _manage_ingredients(self, recipe, ingredients_data):
        
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        
        recipe_ingredients_to_create = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item_data['ingredient'],
                amount=item_data['amount']
            ) for item_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients_to_create)

    
    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        author = self.context.get('request').user

        print(">>> serializer.create: author =", author)
        print(">>> serializer.create: validated_data BEFORE create =", validated_data)

        try:
            
            recipe = Recipe.objects.create(
                author=author,
                name=validated_data.get('name'),
                text=validated_data.get('text'),
                cooking_time=validated_data.get('cooking_time'),
                image=validated_data.get('image') 
            )
        except TypeError as e:
            print("!!! TypeError during Recipe.objects.create:", e)
           
            import inspect
            print("!!! Arguments passed to create:", inspect.getcallargs(Recipe.objects.create, author=author, **validated_data))
            raise e
        except Exception as e: 
            print("!!! Other error during Recipe.objects.create:", e)
            raise e
        
        self._manage_ingredients(recipe, ingredients_data) 
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
       
        ingredients_data = validated_data.pop('ingredients', None)

        instance = super().update(instance, validated_data)

        if ingredients_data is not None:
            self._manage_ingredients(instance, ingredients_data)

        instance.save()
        return instance

    def to_representation(self, instance):
        
        instance.refresh_from_db()
        
        return RecipeSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    
    image = Base64ImageField(required=False, allow_null=True, read_only=True)
   
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
  
    image = Base64ImageField(source='recipe.image', read_only=True, required=False, allow_null=True)
   
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
   
    image = Base64ImageField(source='recipe.image', read_only=True, required=False, allow_null=True)
    
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')

class RecipeGetShortLinkSerializer(serializers.Serializer):
    short_link = serializers.URLField(source='short-link', read_only=True)
   