
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Recipe, Ingredient, Favorite, ShoppingCart,
    IngredientInRecipe 
)
from .serializers import (
    RecipeListSerializer, 
    RecipeCreateUpdateSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeGetShortLinkSerializer
)
from api.pagination import CustomPageNumberPagination
from api.permissions import IsOwnerOrReadOnly
from api.filters import RecipeFilter


def generate_shopping_list_text(user):
   
    ingredients = IngredientInRecipe.objects.filter(
        recipe__shopping_cart_items__user=user
    ).values(
        name=F('ingredient__name'),
        unit=F('ingredient__measurement_unit')
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('name')

    if not ingredients:
        return "Ваш список покупок пуст."

    shopping_list = ["Список покупок:\n"]
    for item in ingredients:
        shopping_list.append(
            f"- {item['name']} ({item['unit']}) — {item['total_amount']}"
        )
    return "\n".join(shopping_list)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny,]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name_query = self.request.query_params.get('name')
        if name_query:
            queryset = queryset.filter(name__istartswith=name_query)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
       
        'recipe_ingredients__ingredient', 
        'favorites',
        'shopping_cart_items'
    ).all().order_by('-pub_date')

    pagination_class = CustomPageNumberPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        elif self.action in ('favorite', 'shopping_cart'):
            return RecipeMinifiedSerializer 
        elif self.action == 'get_link':
            return RecipeGetShortLinkSerializer
        return RecipeListSerializer 

    def perform_create(self, serializer):
        
        serializer.save(author=self.request.user)

    def _manage_user_recipe_relation(self, request, pk, related_model, error_messages):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        relation_exists = related_model.objects.filter(user=user, recipe=recipe).exists()

        if request.method == 'POST':
            if relation_exists:
                return Response({'errors': error_messages['already_exists']},
                                status=status.HTTP_400_BAD_REQUEST)
            related_model.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={'request': request}) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not relation_exists:
                return Response({'errors': error_messages['not_exists']},
                                status=status.HTTP_400_BAD_REQUEST)
            relation = get_object_or_404(related_model, user=user, recipe=recipe)
            relation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated], url_path='favorite', url_name='favorite')
    def favorite(self, request, pk=None):
        error_messages = {
            'already_exists': 'Рецепт уже в избранном.',
            'not_exists': 'Рецепта не было в избранном.'
        }
        return self._manage_user_recipe_relation(request, pk, Favorite, error_messages)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated], url_path='shopping_cart', url_name='shopping_cart')
    def shopping_cart(self, request, pk=None):
        error_messages = {
            'already_exists': 'Рецепт уже в списке покупок.',
            'not_exists': 'Рецепта не было в списке покупок.'
        }
        return self._manage_user_recipe_relation(request, pk, ShoppingCart, error_messages)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='download_shopping_cart', url_name='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        shopping_list_content = generate_shopping_list_text(user)
        response = HttpResponse(shopping_list_content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny], url_path='get-link', url_name='get_link')
    def get_link(self, request, pk=None):
        print(f">>> Request received for get_link with pk={pk}") 
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            print(f">>> Recipe found: {recipe.name}")
        except Exception as e:
            print(f"!!! Error getting recipe: {e}") 
            raise 

        short_code_placeholder = f"s{recipe.id}"
        base_short_url = "https://foodgram.example.org/s/"
        short_link_url = f"{base_short_url}{short_code_placeholder}"

        
        response_data = {"short-link": short_link_url}
        print(f">>> Returning hardcoded response data: {response_data}") 
        return Response(response_data, status=status.HTTP_200_OK)
       