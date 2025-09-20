from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Enlaza las rutas de la app inventario (donde está reporte_stock_bajo)
    path('', include('inventario.urls')),
]
