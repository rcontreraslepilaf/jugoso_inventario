# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importa un router ya construido desde la API (registra solo lo disponible)
from inventario.api import get_api_router

# (Opcional) JWT
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = get_api_router()

urlpatterns = [
    path('admin/', admin.site.urls),

    # API REST (root): http://127.0.0.1:8000/api/v1/
    path('api/v1/', include(router.urls)),

    # Rutas web clásicas
    path('', include('inventario.urls')),
]

# JWT endpoints (opcional para Postman)
urlpatterns += [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
