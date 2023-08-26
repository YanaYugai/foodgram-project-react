from django.contrib import admin
from django.urls import path, include, re_path
from api.views import RecipeViewSet, TagReadView, IngredientReadView, FollowApiView
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagReadView)
router.register(r'ingredients', IngredientReadView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/<int:user_id>/subscribe/', FollowApiView.as_view({'post': 'create', 'delete': 'destroy'})),
    path('api/users/subscriptions/', FollowApiView.as_view({'get': 'list'})),
    path('api/', include(router.urls)),
    path('api/', include('djoser.urls')),
    re_path(r'^api/auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
