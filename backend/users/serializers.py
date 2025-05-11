
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField

from .models import Subscription

User = get_user_model()


class CustomUserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(read_only=True, required=False, allow_null=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous or not isinstance(obj, User):
            return False
        user = request.user
        return Subscription.objects.filter(user=user, author=obj).exists()


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'password',
                  'first_name', 'last_name')
        read_only_fields = ('id',)

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                "Имя пользователя 'me' запрещено.")
        return value


class UserWithRecipesSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = CustomUserSerializer.Meta.fields + ('recipes_count',)

    def get_recipes(self, obj):
        from recipes.serializers import RecipeMinifiedSerializer

        request = self.context.get('request')
        limit_param = request.query_params.get('recipes_limit') if request else None
        try:
            limit = int(limit_param) if limit_param else settings.DEFAULT_RECIPES_LIMIT
        except (ValueError, TypeError):
            limit = settings.DEFAULT_RECIPES_LIMIT

        recipes = obj.recipes.all()[:limit]
        serializer = RecipeMinifiedSerializer(recipes, many=True, read_only=True, context=self.context)
        return serializer.data


class SetAvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('avatar',)