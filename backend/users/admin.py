
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Subscription


class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'recipe_count', 'follower_count'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('username',)
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('avatar',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('first_name', 'last_name', 'email', 'avatar')}),
    )

    @admin.display(description='Кол-во рецептов')
    def recipe_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Кол-во подписчиков')
    def follower_count(self, obj):
         return obj.following.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'created_at')
    search_fields = ('user__username', 'user__email', 'author__username', 'author__email')
    list_filter = ('created_at',)
    autocomplete_fields = ('user', 'author')


admin.site.register(User, CustomUserAdmin)