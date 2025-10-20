# inventario/views_deuda.py
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.contrib import messages

from .models import Cliente, Producto, Venta, DetalleVenta


# ---------------- Utilidades internas ----------------

def _nombre_precio(detalle_model):
    """
    Devuelve el nombre del campo de precio unitario en DetalleVenta
    (precio_unitario, precio, valor, valor_unitario).
    """
    nombres = {f.name for f in detalle_model._meta.fields}
    for f in ("precio_unitario", "precio", "valor", "valor_unitario"):
        if f in nombres:
            return f
    return None


def _crear_detalle(venta, producto, cantidad, precio):
    """
    Crea el detalle de venta usando el nombre real del campo de precio.
    """
    price_field = _nombre_precio(DetalleVenta)
    kwargs = {"venta": venta, "producto": producto, "cantidad": cantidad}
    if price_field:
        kwargs[price_field] = precio
    return DetalleVenta.objects.create(**kwargs)


def _precio_detalle(det):
    """
    Obtiene el precio unitario de una línea sin importar el nombre del campo.
    """
    for f in ("precio_unitario", "precio", "valor", "valor_unitario"):
        if hasattr(det, f):
            return getattr(det, f)
    return Decimal("0")


# ---------------- Vistas públicas ----------------

@transaction.atomic
def deuda_guardar(request):
    """
    Recibe las líneas del POS y registra una venta marcada como deuda.
    - Crea/usa un Cliente por nombre.
    - Marca Venta.es_deuda=True y saldada=False.
    - Guarda la descripción en Venta.observacion (si viene).
    - Crea DetalleVenta por cada línea.
    - Descuenta stock (con select_for_update para evitar condiciones de carrera).
    """
    if request.method != "POST":
        return redirect("inventario:pos_venta")

    deudor_nombre = (request.POST.get("deudor_nombre") or "").strip()
    descripcion = (request.POST.get("descripcion") or "").strip()

    if not deudor_nombre:
        messages.error(request, "Debes indicar el nombre del deudor.")
        return redirect("inventario:pos_venta")

    ids = request.POST.getlist("product_id[]")
    cants = request.POST.getlist("cantidad[]")
    precios = request.POST.getlist("precio[]")

    lineas = []
    for i in range(len(ids)):
        try:
            pid = int(ids[i]) if ids[i] else 0
            cant = Decimal(cants[i] or "0")
            precio = Decimal(precios[i] or "0")
        except (InvalidOperation, ValueError):
            continue
        if pid > 0 and cant > 0 and precio >= 0:
            lineas.append((pid, cant, precio))

    if not lineas:
        messages.error(request, "Agrega al menos un ítem válido para registrar la deuda.")
        return redirect("inventario:pos_venta")

    # Cliente por nombre (lo crea si no existe)
    cliente = Cliente.objects.filter(nombre__iexact=deudor_nombre).first()
    if not cliente:
        cliente = Cliente.objects.create(nombre=deudor_nombre)

    with transaction.atomic():
        venta = Venta.objects.create(
            cliente=cliente,
            es_deuda=True,
            saldada=False,
            observacion=descripcion
        )

        total = Decimal("0")
        for pid, cant, precio in lineas:
            # Bloqueo del producto para stock consistente
            prod = Producto.objects.select_for_update().get(pk=pid)

            if prod.stock is not None and prod.stock < cant:
                messages.error(request, f"Stock insuficiente para {prod.nombre}.")
                raise transaction.TransactionManagementError("Stock insuficiente")

            _crear_detalle(venta=venta, producto=prod, cantidad=cant, precio=precio)
            total += cant * precio

            # Descuento de stock
            prod.stock = (prod.stock or Decimal("0")) - cant
            prod.save(update_fields=["stock"])

        # Guarda total si el modelo lo tiene
        if "total" in {f.name for f in Venta._meta.fields}:
            venta.total = total
            venta.save(update_fields=["total"])

    messages.success(request, f"Deuda registrada para {cliente.nombre}.")
    return redirect("inventario:deudores_list")


def deudores_list(request):
    """
    Lista de deudores (ventas a crédito pendientes).
    Muestra una fila por venta pendiente con: cliente, fecha, descripción, total y acciones.
    """
    qs = (Venta.objects
          .filter(es_deuda=True, saldada=False, cliente__isnull=False)
          .select_related("cliente"))

    campo_precio = _nombre_precio(DetalleVenta)

    if campo_precio:
        # IMPORTANTE: prefijar con detalles__ para que Django haga el join correcto
        subtotal_expr = ExpressionWrapper(
            F("detalles__cantidad") * F(f"detalles__{campo_precio}"),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
        deudas = (
            qs.values("id", "cliente__id", "cliente__nombre", "fecha", "observacion")
              .annotate(total_adeudado=Sum(subtotal_expr))
              .order_by("-fecha", "-id")
        )
    else:
        # Si Venta.total existe, úsalo como respaldo
        deudas = (
            qs.values("id", "cliente__id", "cliente__nombre", "fecha", "observacion")
              .annotate(total_adeudado=Sum("total"))
              .order_by("-fecha", "-id")
        )

    return render(request, "inventario/deudores_list.html", {"deudas": deudas})


@transaction.atomic
def deuda_pagar(request, pk):
    """
    Marca una deuda como pagada (saldada=True).
    Solo permite método POST.
    """
    if request.method != "POST":
        messages.error(request, "Acción no permitida. Usa el botón Pagar.")
        return redirect("inventario:deudores_list")

    venta = get_object_or_404(Venta, pk=pk, es_deuda=True, saldada=False)
    venta.saldada = True
    venta.save(update_fields=["saldada"])
    nombre = venta.cliente.nombre if venta.cliente else "—"
    messages.success(request, f"La deuda del cliente {nombre} fue marcada como pagada.")
    return redirect("inventario:deudores_list")


@transaction.atomic
def deuda_eliminar(request, pk):
    """
    Elimina una venta a deuda (si está pendiente) y repone stock.
    Solo permite método POST.
    """
    if request.method != "POST":
        messages.error(request, "Acción no permitida. Usa el botón Eliminar.")
        return redirect("inventario:deudores_list")

    venta = get_object_or_404(Venta, pk=pk, es_deuda=True, saldada=False)
    nombre = venta.cliente.nombre if venta.cliente else "—"

    # Reponer stock
    detalles = venta.detalles.select_related("producto").all()
    for d in detalles:
        if not d.producto_id:
            continue
        prod = Producto.objects.select_for_update().get(pk=d.producto_id)
        prod.stock = (prod.stock or Decimal("0")) + (d.cantidad or Decimal("0"))
        prod.save(update_fields=["stock"])

    venta.delete()
    messages.success(request, f"La deuda de {nombre} fue eliminada y el stock repuesto.")
    return redirect("inventario:deudores_list")


def deudor_detalle(request, pk):
    """
    Historial de deudas de un cliente (pendientes y saldadas) con sus líneas.
    """
    cliente = get_object_or_404(Cliente, pk=pk)

    ventas = (
        Venta.objects
        .filter(cliente=cliente, es_deuda=True)
        .order_by("-id")
    )

    historial = []
    for v in ventas:
        detalles = v.detalles.select_related("producto").all()
        lineas = []
        v_total = Decimal("0")
        for d in detalles:
            precio = _precio_detalle(d)
            subtotal = (d.cantidad or Decimal("0")) * (precio or Decimal("0"))
            v_total += subtotal
            lineas.append({
                "producto": getattr(d.producto, "nombre", "—"),
                "cantidad": d.cantidad,
                "precio": precio,
                "subtotal": subtotal,
            })

        if hasattr(v, "total") and v.total:
            v_total = v.total

        historial.append({
            "venta": v,
            "fecha": getattr(v, "fecha", getattr(v, "created_at", None)),
            "descripcion": getattr(v, "observacion", ""),
            "total": v_total,
            "saldada": v.saldada,
            "lineas": lineas,
        })

    return render(request, "inventario/deudor_detalle.html", {
        "cliente": cliente,
        "historial": historial,
    })
