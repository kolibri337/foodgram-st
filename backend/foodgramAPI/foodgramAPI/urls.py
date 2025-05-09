from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Основные URL-маршруты приложения
base_urlpatterns = [
    # API endpoints
    path("api/", include("api.urls", namespace="api")),
    # Основные URL рецептов
    path("", include("recipes.urls", namespace="recipes")),
     # Админ-панель Django
    path("admin/", admin.site.urls),
]

# Добавляем медиа-файлы в режиме DEBUG
debug_patterns = []
if settings.DEBUG:
    debug_patterns.extend([
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
        *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    ])

# Финальные URL-маршруты
urlpatterns = base_urlpatterns + debug_patterns