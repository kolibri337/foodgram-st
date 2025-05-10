from django.urls import path
from . import views

app_name = 'recipes'

urlpatterns = [path('recipes/',
                    views.RecipesViewSet.as_view({'get': 'list'}),
                    name='recipes-list'),
               ]
