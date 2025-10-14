# inventario/serializers.py
from rest_framework import serializers
from django.db import transaction

from .models import Categoria, Producto

# Proveedor puede existir o no según tu proyecto
try:
    from .models import Proveedor
except Exception:
    Proveedor = None

# Movimiento puede llamarse MovimientoStock o Movimiento
try:
    from .models import MovimientoStock as MovimientoModel
except Exception:
    from .models import Movimiento as MovimientoModel

# Bodega opcional
try:
    from .models import Bodega as BodegaModel
except Exception:
    BodegaModel = None


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor if Proveedor is not None else Categoria  # dummy para no romper import si no existe
        fields = "__all__"


def get_bodega_serializer_or_none(BodegaModelRef):
    class _BodegaSerializer(serializers.ModelSerializer):
        class Meta:
            model = BodegaModelRef
            fields = "__all__"
    return _BodegaSerializer


class ProductoSerializer(serializers.ModelSerializer):
    """
    Usa __all__ para adaptarse a tu modelo real. Valida SKU 'codigo' si existe.
    """
    class Meta:
        model = Producto
        fields = "__all__"

    def _has_field(self, name: str) -> bool:
        return name in {f.name for f in self.Meta.model._meta.get_fields()}

    def validate(self, attrs):
        # SKU único si el campo 'codigo' existe en tu modelo
        if self._has_field("codigo"):
            codigo = attrs.get("codigo") or getattr(self.instance, "codigo", None)
            if codigo:
                qs = self.Meta.model.objects.filter(codigo=codigo)
                if self.instance:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise serializers.ValidationError({"codigo": "El SKU (codigo) ya existe."})
        return attrs


class MovimientoSerializer(serializers.ModelSerializer):
    """
    Controla stock no negativo si tu Producto tiene campo 'stock'.
    """
    class Meta:
        model = MovimientoModel
        fields = "__all__"

    def validate(self, attrs):
        prod = attrs["producto"]
        tipo = str(attrs.get("tipo", "")).upper()  # 'E' entrada, 'S' salida
        cantidad = attrs.get("cantidad", 0)

        if hasattr(prod, "stock"):
            delta = cantidad if tipo == "E" else -cantidad
            nuevo = (getattr(prod, "stock", 0) or 0) + delta
            if nuevo < 0:
                raise serializers.ValidationError({"cantidad": "El stock no puede quedar negativo."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        mov = super().create(validated_data)
        prod = mov.producto
        if hasattr(prod, "stock"):
            if str(mov.tipo).upper() == "E":
                prod.stock = (getattr(prod, "stock", 0) or 0) + mov.cantidad
            else:
                prod.stock = (getattr(prod, "stock", 0) or 0) - mov.cantidad
            prod.save(update_fields=["stock"])
        return mov
