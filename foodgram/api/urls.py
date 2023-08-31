from django.urls import include, path
from rest_framework import routers

from api.views import (
    FollowApiView,
    FollowListApiView,
    IngredientReadView,
    RecipeViewSet,
    TagReadView,
)

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagReadView)
router.register(r'ingredients', IngredientReadView)

urlpatterns = [
    path(
        'users/<int:user_id>/subscribe/',
        FollowApiView.as_view(),
        name='subscribe',
    ),
    path(
        'users/subscriptions/',
        FollowListApiView.as_view(),
        name='subscriptions',
    ),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
