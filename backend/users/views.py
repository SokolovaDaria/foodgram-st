from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated 
from rest_framework.response import Response

from djoser.views import UserViewSet as DjoserUserViewSet

from .models import Subscription
from .serializers import (
    CustomUserSerializer,
    UserWithRecipesSerializer, 
    SetAvatarSerializer,
    SetAvatarResponseSerializer,
)

from api.pagination import CustomPageNumberPagination

User = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    """
    ViewSet для пользователей, наследуется от Djoser UserViewSet.
    Обрабатывает регистрацию, профиль, подписки, аватар.
    """
    queryset = User.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    pagination_class = CustomPageNumberPagination
    
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия."""
        if self.action == 'subscriptions':
            
            return UserWithRecipesSerializer
        elif self.action == 'set_avatar':
             
            return SetAvatarSerializer
        
        return super().get_serializer_class()

    
    @action(["get", "put", "patch", "delete"], detail=False)
    def me(self, request, *args, **kwargs):
        """
        Обрабатывает запросы к /api/users/me/.
        Явно проверяет аутентификацию перед вызовом стандартной логики.
        """
        
        if request.user.is_anonymous:
           
            raise NotAuthenticated()

        self.instance = self.request.user
        if request.method == "GET":
            return self.retrieve(request, *args, **kwargs)
        elif request.method == "PUT":
            return self.update(request, *args, **kwargs)
        elif request.method == "PATCH":
            return self.partial_update(request, *args, **kwargs)
        elif request.method == "DELETE":
           
            return self.destroy(request, *args, **kwargs) 
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

   
    def get_object(self):
        """
        Возвращает объект для detail-действий.
        Для 'me' возвращает текущего пользователя.
        """
        if self.action == 'me':
            
            if self.request.user.is_anonymous:
                 
                raise NotAuthenticated()
            return self.request.user
        
        return super().get_object()

   
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated], 
        url_path='subscriptions',
        url_name='subscriptions'
    )
    def subscriptions(self, request):
        """
        Возвращает список авторов, на которых подписан текущий пользователь.
        """
        user = request.user
        
        queryset = User.objects.filter(
            following__user=user 
        ).prefetch_related('recipes').order_by('id') 

        page = self.paginate_queryset(queryset)
        if page is not None:
            
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    
    @action(
        detail=True, 
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated], 
        url_path='subscribe',
        url_name='subscribe'
    )
    def subscribe(self, request, id=None):
        """Подписывает (POST) или отписывает (DELETE) от пользователя с id."""
        user = request.user
        author = get_object_or_404(User, id=id)

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription_exists = Subscription.objects.filter(user=user, author=author).exists()

        if request.method == 'POST':
            if subscription_exists:
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)
            
            serializer = UserWithRecipesSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not subscription_exists:
                return Response(
                    {'errors': 'Вы не были подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription = get_object_or_404(Subscription, user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    
    @action(
        detail=False, 
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar',
        url_name='set_avatar'
    )
    def set_avatar(self, request):
        """Устанавливает (PUT) или удаляет (DELETE) аватар текущего пользователя."""
        user = request.user

        if request.method == 'PUT':
           
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user.avatar = serializer.validated_data['avatar']
            user.save()
           
            response_serializer = SetAvatarResponseSerializer(user, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)