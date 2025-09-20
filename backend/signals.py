from decimal import Decimal
from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Producto, Compra, DetalleCompra,
    Venta, DetalleVenta, MovimientoStock
)

def _ajustar_stock(producto: Producto, delta: Decimal, referencia: str, motivo: str = ''):
    """
    Ajusta el stock del producto y registra el movimiento (kardex).
    delta > 0 => Entrada, delta < 0 => Salida
    """
    # Evitar stock negativo
    if delta < 0 and (producto.stock or 0) + delta < 0:
        raise ValidationError(
            f"Stock insuficiente para {producto}. Intento de salida {abs(delta)}, stock actual {producto.stock}."
        )

    # Ajuste
    producto.stock = (producto.stock or 0) + delta
    producto.save(update_fields=['stock'])

    # Movimiento
    MovimientoStock.objects.create(
        producto=producto,
        tipo=MovimientoStock.ENTRADA if delta > 0 else MovimientoStock.SALIDA,
        cantidad=abs(delta),
        motivo=motivo,
        fecha=timezone.now(),
        referencia=referencia,
    )

def _get_old_cantidad(instance, default=Decimal('0')):
    if not instance.pk:
        return default
    try:
        old = type(instance).objects.get(pk=instance.pk)
        return old.cantidad
    except type(instance).DoesNotExist:
        return default

# Validación: no vender sin stock (solo sobre el delta adicional)
@receiver(pre_save, sender=DetalleVenta)
def validar_stock_en_venta(sender, instance: DetalleVenta, **kwargs):
    new_qty = instance.cantidad or Decimal('0')
    old_qty = _get_old_cantidad(instance)
    delta_salida = new_qty - old_qty  # extra que saldrá ahora
    if delta_salida <= 0:
        return
    prod = instance.producto
    if (prod.stock or 0) < delta_salida:
        raise ValidationError(
            f"Stock insuficiente para {prod}. Stock actual: {prod.stock}, requerido: {delta_salida}."
        )

# Compra: aplicar entradas
@receiver(post_save, sender=DetalleCompra)
def aplicar_entrada_compra(sender, instance: DetalleCompra, created, **kwargs):
    with transaction.atomic():
        new_qty = instance.cantidad or Decimal('0')
        old_qty = _get_old_cantidad(instance) if not created else Decimal('0')
        delta = new_qty - old_qty
        if delta != 0:
            ref = f"Compra#{instance.compra_id}"
            _ajustar_stock(instance.producto, delta, referencia=ref, motivo='Ingreso por compra')

# Compra: revertir entradas al borrar detalle
@receiver(post_delete, sender=DetalleCompra)
def revertir_entrada_compra(sender, instance: DetalleCompra, **kwargs):
    with transaction.atomic():
        qty = instance.cantidad or Decimal('0')
        if qty > 0:
            ref = f"Compra#{instance.compra_id}"
            _ajustar_stock(instance.producto, -qty, referencia=ref, motivo='Reverso compra')

# Venta: aplicar salidas
@receiver(post_save, sender=DetalleVenta)
def aplicar_salida_venta(sender, instance: DetalleVenta, created, **kwargs):
    with transaction.atomic():
        new_qty = instance.cantidad or Decimal('0')
        old_qty = _get_old_cantidad(instance) if not created else Decimal('0')
        delta = new_qty - old_qty
        if delta != 0:
            ref = f"Venta#{instance.venta_id}"
            _ajustar_stock(instance.producto, -delta, referencia=ref, motivo='Egreso por venta')

# Venta: revertir salidas al borrar detalle
@receiver(post_delete, sender=DetalleVenta)
def revertir_salida_venta(sender, instance: DetalleVenta, **kwargs):
    with transaction.atomic():
        qty = instance.cantidad or Decimal('0')
        if qty > 0:
            ref = f"Venta#{instance.venta_id}"
            _ajustar_stock(instance.producto, qty, referencia=ref, motivo='Reverso venta')
