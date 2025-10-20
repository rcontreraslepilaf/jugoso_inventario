# inventario/admin.py
from decimal import Decimal
from django.contrib import admin, messages
from django.utils.html import format_html

from .models import (
    Categoria, Proveedor, Cliente, Producto,
    Compra, DetalleCompra, Venta, DetalleVenta, MovimientoStock
)

# ---------------------------
# Helpers internos
# ---------------------------
def _campo_precio_detalle_venta():
    for f in ("precio_unitario", "precio", "valor", "valor_unitario"):
        if f in {fld.name for fld in DetalleVenta._meta.fields}:
            return f
    return None

def _campo_costo_detalle_compra():
    for f in ("costo_unitario", "costo", "precio", "precio_unitario", "valor", "valor_unitario"):
        if f in {fld.name for fld in DetalleCompra._meta.fields}:
            return f
    return None

def _fmt_money(n):
    try:
        val = Decimal(n or 0)
    except Exception:
        val = Decimal("0")
    # render simple: $1.234
    return f"${val.quantize(Decimal('1')):,.0f}".replace(",", ".")


# ---------------------------
# Catálogos
# ---------------------------
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut", "telefono", "email", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "rut", "email")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut", "telefono", "email", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "rut", "email")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "categoria", "unidad", "precio", "stock", "stock_minimo", "activo")
    list_filter = ("categoria", "activo")
    search_fields = ("codigo", "nombre")
    ordering = ("codigo",)


# ---------------------------
# Compras
# ---------------------------
class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 0

    # Detecta dinámicamente el nombre del campo costo/precio unitario:
    def get_fields(self, request, obj=None):
        base = ["producto", "cantidad"]
        costo = _campo_costo_detalle_compra()
        if costo:
            base.append(costo)
        return base

    def get_readonly_fields(self, request, obj=None):
        # nada readonly por defecto; ajusta si deseas
        return []

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ("id", "proveedor", "fecha", "total_mostrable")
    date_hierarchy = "fecha"
    inlines = [DetalleCompraInline]
    search_fields = ("proveedor__nombre",)
    ordering = ("-fecha",)

    @admin.display(description="Total")
    def total_mostrable(self, obj):
        try:
            return _fmt_money(obj.total())
        except Exception:
            return _fmt_money(0)


# ---------------------------
# Ventas (con soporte a Deuda)
# ---------------------------
class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0

    # Detecta dinámicamente el nombre del campo precio unitario
    def get_fields(self, request, obj=None):
        base = ["producto", "cantidad"]
        precio = _campo_precio_detalle_venta()
        if precio:
            base.append(precio)
        return base

    def get_readonly_fields(self, request, obj=None):
        # nada readonly por defecto; ajusta si deseas
        return []


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    inlines = [DetalleVentaInline]

    list_display = ("id", "cliente", "fecha", "es_deuda", "saldada", "total_mostrable")
    list_filter = ("es_deuda", "saldada", "fecha")
    search_fields = ("cliente__nombre",)
    date_hierarchy = "fecha"
    ordering = ("-fecha",)

    actions = ("marcar_pagada", "marcar_pendiente")

    @admin.display(description="Total")
    def total_mostrable(self, obj):
        try:
            return _fmt_money(obj.total())
        except Exception:
            return _fmt_money(0)

    @admin.action(description="Marcar como pagada (solo ventas a deuda)")
    def marcar_pagada(self, request, queryset):
        qs = queryset.filter(es_deuda=True, saldada=False)
        updated = qs.update(saldada=True)
        if updated:
            self.message_user(request, f"{updated} venta(s) marcadas como pagadas.", level=messages.SUCCESS)
        else:
            self.message_user(request, "No había ventas a deuda pendientes en la selección.", level=messages.WARNING)

    @admin.action(description="Marcar como pendiente (solo ventas a deuda)")
    def marcar_pendiente(self, request, queryset):
        qs = queryset.filter(es_deuda=True, saldada=True)
        updated = qs.update(saldada=False)
        if updated:
            self.message_user(request, f"{updated} venta(s) marcadas como pendientes.", level=messages.SUCCESS)
        else:
            self.message_user(request, "No había ventas a deuda pagadas en la selección.", level=messages.WARNING)


# ---------------------------
# Movimientos de Stock
# ---------------------------
@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ("producto", "tipo", "cantidad", "motivo", "fecha", "referencia")
    list_filter = ("tipo", "fecha")
    search_fields = ("producto__nombre", "referencia", "motivo")
    date_hierarchy = "fecha"
    ordering = ("-fecha",)
