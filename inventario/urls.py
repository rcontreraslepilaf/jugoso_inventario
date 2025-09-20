from django.urls import path
from .views import reporte_stock_bajo

app_name = 'inventario'

urlpatterns = [
    path('reportes/stock-bajo/', reporte_stock_bajo, name='reporte_stock_bajo'),
]
