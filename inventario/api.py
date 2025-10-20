# inventario/api.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models as dj_models
from rest_framework.routers import DefaultRouter

# 👇 imports necesarios para la previsualización del POS
from django.shortcuts import render
from django.db.models import Q

from .models import Categoria, Producto, Proveedor  # si Proveedor no existe, no pasa nada porque no lo usamos aquí

# Movimiento puede llamarse MovimientoStock o Movimiento
try:
    from .models import MovimientoStock as MovimientoModel
except Exception:
    from .models import Movimiento as MovimientoModel

# Bodega es opcional
try:
    from .models import Bodega as BodegaModel
except Exception:
    BodegaModel = None

from .serializers import (
    CategoriaSerializer,
    ProveedorSerializer,
    ProductoSerializer,
    MovimientoSerializer,
    get_bodega_serializer_or_none,
)
from .permissions import RolePermission


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [RolePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]


class CategoriaViewSet(BaseViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class ProveedorViewSet(BaseViewSet):
    # Si tu proyecto no tiene proveedores en la BD, igual funciona (CRUD estándar)
    try:
        queryset = Proveedor.objects.all()
    except Exception:
        queryset = []
    serializer_class = ProveedorSerializer


class ProductoViewSet(BaseViewSet):
    # 💡 IMPORTANTE: quitamos select_related('proveedor') porque tu modelo no lo tiene.
    # Usamos la consulta simple y así evitamos FieldError.
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    # Vendedor NO puede escribir aquí
    allow_vendor_write = False

    @action(detail=False, methods=["get"])
    def bajo_stock(self, request):
        """
        GET /api/v1/productos/bajo_stock/
        Si el modelo tiene 'stock' y 'stock_minimo', filtra; si no, devuelve lista vacía.
        """
        fields = {f.name for f in Producto._meta.get_fields()}
        if {"stock", "stock_minimo"}.issubset(fields):
            qs = self.get_queryset().filter(stock__lte=dj_models.F("stock_minimo"))
            page = self.paginate_queryset(qs)
            if page is not None:
                ser = self.get_serializer(page, many=True)
                return self.get_paginated_response(ser.data)
            ser = self.get_serializer(qs, many=True)
            return Response(ser.data, status=status.HTTP_200_OK)
        # Si tu modelo no tiene esos campos, devolvemos 200 con lista vacía para no romper la demo.
        return Response([], status=status.HTTP_200_OK)


class MovimientoViewSet(BaseViewSet):
    queryset = MovimientoModel.objects.select_related("producto").all()
    serializer_class = MovimientoSerializer

    # Vendedor SÍ puede escribir aquí
    allow_vendor_write = True


# --- Bodega: solo definimos el ViewSet si el modelo existe ---
if BodegaModel is not None:
    BodegaSerializer = get_bodega_serializer_or_none(BodegaModel)

    class BodegaViewSet(BaseViewSet):
        queryset = BodegaModel.objects.all()
        serializer_class = BodegaSerializer


def get_api_router() -> DefaultRouter:
    """
    Construye y devuelve un router DRF registrando solo los endpoints disponibles.
    """
    router = DefaultRouter()
    router.register(r'categorias', CategoriaViewSet, basename='categoria')
    router.register(r'proveedores', ProveedorViewSet, basename='proveedor')
    router.register(r'productos', ProductoViewSet, basename='producto')
    router.register(r'movimientos', MovimientoViewSet, basename='movimiento')
    if BodegaModel is not None:
        router.register(r'bodegas', BodegaViewSet, basename='bodega')
    return router


# ============================================================
# ==========  ENDPOINT PARA PREVISUALIZAR EN EL POS  =========
# ============================================================
def producto_info(request):
    """
    Retorna un fragmento HTML (partial) con la previsualización
    de un producto para POS: cantidad, precio y subtotal ANTES de agregar.

    Busca por código EXACTO (codigo__iexact) o nombre (icontains).
    Si tu modelo usa otro campo de precio (p. ej. 'precio_venta'), lo detecta.
    """
    q = (request.GET.get("q") or "").strip()
    p = None
    precio_base = 0

    if q:
        p = (
            Producto.objects.filter(Q(codigo__iexact=q) | Q(nombre__icontains=q))
            .order_by("id")
            .first()
        )
        if p:
            # Detecta el campo de precio existente
            if hasattr(p, "precio") and p.precio is not None:
                precio_base = p.precio
            elif hasattr(p, "precio_venta") and p.precio_venta is not None:
                precio_base = p.precio_venta
            else:
                precio_base = 0

    # Render del partial con el producto (p) y el precio_base decidido
    return render(
        request,
        "inventario/partials/producto_preview.html",
        {"p": p, "precio_base": precio_base},
    )
