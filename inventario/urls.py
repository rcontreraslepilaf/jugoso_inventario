# inventario/urls.py
from django.urls import path
from . import views, api
from . import views_deuda  # vistas específicas para Deuda/Deudores

app_name = "inventario"

urlpatterns = [
    # Home
    path("", views.home, name="home"),

    # Categorías
    path("categorias/", views.categoria_list, name="categoria_list"),
    path("categorias/nueva/", views.categoria_crear, name="categoria_crear"),
    path("categorias/<int:pk>/editar/", views.categoria_editar, name="categoria_editar"),
    path("categorias/<int:pk>/eliminar/", views.categoria_eliminar, name="categoria_eliminar"),

    # Proveedores
    path("proveedores/", views.proveedor_list, name="proveedor_list"),
    path("proveedores/nuevo/", views.proveedor_crear, name="proveedor_crear"),
    path("proveedores/<int:pk>/editar/", views.proveedor_editar, name="proveedor_editar"),
    path("proveedores/<int:pk>/eliminar/", views.proveedor_eliminar, name="proveedor_eliminar"),

    # Productos
    path("productos/", views.productos_list, name="productos_list"),
    path("productos/nuevo/", views.producto_crear, name="producto_crear"),
    path("productos/<int:pk>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:pk>/eliminar/", views.producto_eliminar, name="producto_eliminar"),

    # Compras
    path("compras/nueva/", views.compra_nueva, name="compra_nueva"),

    # POS / Ventas
    path("ventas/pos/", views.pos_venta, name="pos_venta"),
    path("ventas/", views.ventas_list, name="ventas_list"),
    path("ventas/<int:pk>/", views.ventas_detalle, name="ventas_detalle"),

    # Reportes
    path("reportes/stock-bajo/", views.reporte_stock_bajo, name="reporte_stock_bajo"),

    # API (precios para previsualización en POS)
    path("api/producto-info/", api.producto_info, name="producto_info"),

    # Deudores / Deuda
    path("ventas/deudores/", views_deuda.deudores_list, name="deudores_list"),
    path("ventas/deudores/<int:pk>/", views_deuda.deudor_detalle, name="deudor_detalle"),
    path("ventas/deuda/guardar/", views_deuda.deuda_guardar, name="deuda_guardar"),

    # NUEVO: Acciones sobre deudas (POST recomendado desde el template)
    path("ventas/deuda/<int:pk>/pagar/", views_deuda.deuda_pagar, name="deuda_pagar"),
    path("ventas/deuda/<int:pk>/eliminar/", views_deuda.deuda_eliminar, name="deuda_eliminar"),
]
