from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from recipes.views import RecipesViewSet, IngredientsViewSet 
from djoser.views import TokenObtainPairView, TokenDestroyView

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('ingredients', IngredientsViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
]