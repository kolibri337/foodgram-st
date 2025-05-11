from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserAccountViewSet
from recipes.views import RecipesViewSet, IngredientsViewSet
from djoser.views import TokenCreateView, TokenDestroyView

app_name = 'api'

router = DefaultRouter()
router.register('users', UserAccountViewSet, basename='users')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('ingredients', IngredientsViewSet, basename='ingredients')

urlpatterns = [
    path('users/me/avatar/', UserAccountViewSet.as_view({'put': 'profile_image', 'delete': 'profile_image'}), name='user-profile-image'),
    path('users/<int:pk>/subscribe/', UserAccountViewSet.as_view({'post': 'follow', 'delete': 'follow'}), name='user-follow'),
    path('auth/token/login/', TokenCreateView.as_view(), name='token-auth'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='token-logout'),
    path('users/me/password/', UserAccountViewSet.as_view({'post': 'change_password'}), name='user-change-password'),
    path('users/', UserAccountViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-list'),
    path('', include(router.urls)),
]
