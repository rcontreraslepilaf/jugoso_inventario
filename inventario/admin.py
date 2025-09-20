from django.contrib import admin
from .models import (Categoria, Proveedor, Cliente, Producto,
                     Compra, DetalleCompra, Venta, DetalleVenta, MovimientoStock)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'email', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'rut', 'email')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'email', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'rut', 'email')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'unidad', 'precio', 'stock', 'stock_minimo', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre')

class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 1

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'proveedor', 'fecha', 'total')
    date_hierarchy = 'fecha'
    inlines = [DetalleCompraInline]

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'total')
    date_hierarchy = 'fecha'
    inlines = [DetalleVentaInline]

@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'motivo', 'fecha', 'referencia')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre', 'referencia', 'motivo')
