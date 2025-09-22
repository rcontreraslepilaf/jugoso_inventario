from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
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
    path("ventas/<int:pk>/", views.ventas_detalle, name="ventas_detalle"),  # <--- NUEVO

    # Reportes
    path("reportes/stock-bajo/", views.reporte_stock_bajo, name="reporte_stock_bajo"),
]
