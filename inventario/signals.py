from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps

# Intentamos cargar modelos de forma segura (por nombre)
Producto = apps.get_model('inventario', 'Producto')
DetalleCompra = apps.get_model('inventario', 'DetalleCompra')
DetalleVenta = apps.get_model('inventario', 'DetalleVenta')

# MovimientoStock es opcional: si existe, lo usamos; si no, seguimos sin registrar movimiento
MovimientoStock = None
try:
    MovimientoStock = apps.get_model('inventario', 'MovimientoStock')
except LookupError:
    MovimientoStock = None


def _registrar_movimiento(producto, tipo, cantidad, referencia=None, nota=''):
    """
    Crea un MovimientoStock si el modelo existe. 'tipo' puede ser 'COMPRA', 'VENTA', 'AJUSTE'.
    'referencia' puede ser el objeto Compra/Venta/Detalle involucrado.
    """
    if not MovimientoStock:
        return
    try:
        MovimientoStock.objects.create(
            producto=producto,
            tipo=tipo,
            cantidad=cantidad,
            referencia=str(referencia) if referencia else '',
            nota=nota or ''
        )
    except Exception:
        # No interrumpas el flujo si falla el log
        pass


# =========================
# COMPRAS: suman stock
# =========================
@receiver(post_save, sender=DetalleCompra)
def detalle_compra_guardado(sender, instance, created, **kwargs):
    """
    Al crear un DetalleCompra, aumenta el stock del producto en 'cantidad'.
    Si se actualiza, no hacemos nada (para simplicidad). 
    """
    if not created:
        return
    prod = instance.producto
    cantidad = Decimal(instance.cantidad or 0)
    if cantidad > 0:
        prod.stock = (prod.stock or Decimal('0')) + cantidad
        prod.save(update_fields=['stock'])
        _registrar_movimiento(prod, 'COMPRA', cantidad, referencia=instance, nota='Ingreso por compra')


@receiver(post_delete, sender=DetalleCompra)
def detalle_compra_eliminado(sender, instance, **kwargs):
    """
    Si se elimina un DetalleCompra, revertimos el stock.
    """
    prod = instance.producto
    cantidad = Decimal(instance.cantidad or 0)
    if cantidad > 0:
        prod.stock = (prod.stock or Decimal('0')) - cantidad
        if prod.stock < 0:
            prod.stock = Decimal('0')
        prod.save(update_fields=['stock'])
        _registrar_movimiento(prod, 'AJUSTE', -cantidad, referencia=instance, nota='Reverso por eliminación de detalle de compra')


# =========================
# VENTAS: restan stock
# =========================
@receiver(post_save, sender=DetalleVenta)
def detalle_venta_guardado(sender, instance, created, **kwargs):
    """
    Al crear un DetalleVenta, disminuye el stock del producto en 'cantidad'.
    """
    if not created:
        return
    prod = instance.producto
    cantidad = Decimal(instance.cantidad or 0)
    if cantidad > 0:
        nuevo = (prod.stock or Decimal('0')) - cantidad
        prod.stock = nuevo if nuevo >= 0 else Decimal('0')
        prod.save(update_fields=['stock'])
        _registrar_movimiento(prod, 'VENTA', -cantidad, referencia=instance, nota='Salida por venta')


@receiver(post_delete, sender=DetalleVenta)
def detalle_venta_eliminado(sender, instance, **kwargs):
    """
    Si se elimina un DetalleVenta, devolvemos el stock.
    """
    prod = instance.producto
    cantidad = Decimal(instance.cantidad or 0)
    if cantidad > 0:
        prod.stock = (prod.stock or Decimal('0')) + cantidad
        prod.save(update_fields=['stock'])
        _registrar_movimiento(prod, 'AJUSTE', cantidad, referencia=instance, nota='Reverso por eliminación de detalle de venta')
