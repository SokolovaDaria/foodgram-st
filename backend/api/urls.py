
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet 
from recipes.views import RecipeViewSet, IngredientViewSet

app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register(r'users', CustomUserViewSet, basename='users')

router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
   
    path('', include(router_v1.urls)),
    
    path('auth/', include('djoser.urls.authtoken')),
]