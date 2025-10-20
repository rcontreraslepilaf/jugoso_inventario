# inventario/views.py
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Q, F, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django import forms
from django.apps import apps
from django.utils import timezone

from .models import Categoria, Proveedor, Producto, Cliente, MovimientoStock

# Modelos que podrías no tener en algunos proyectos
Compra = DetalleCompra = Venta = DetalleVenta = None
try:
    Compra = apps.get_model("inventario", "Compra")
    DetalleCompra = apps.get_model("inventario", "DetalleCompra")
    Venta = apps.get_model("inventario", "Venta")
    DetalleVenta = apps.get_model("inventario", "DetalleVenta")
except LookupError:
    pass


# --------------------- utilidades ---------------------

def paginar_queryset(request, queryset, per_page=10):
    page_number = request.GET.get("page") or 1
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)

def _nombre_campo_precio(modelo, candidatos):
    field_names = {f.name for f in modelo._meta.fields}
    for name in candidatos:
        if name in field_names:
            return name
    return None

def _tiene_campo(modelo, nombre):
    return nombre in {f.name for f in modelo._meta.fields}

def _crear_detalle_compra(compra, producto, cantidad, precio_unit):
    price_field = _nombre_campo_precio(
        DetalleCompra,
        ["costo", "precio", "precio_unitario", "costo_unitario", "valor", "valor_unitario"],
    )
    kwargs = {"compra": compra, "producto": producto, "cantidad": cantidad}
    if price_field:
        kwargs[price_field] = precio_unit
    return DetalleCompra.objects.create(**kwargs)

def _crear_detalle_venta(venta, producto, cantidad, precio_unit):
    price_field = _nombre_campo_precio(
        DetalleVenta,
        ["precio", "precio_unitario", "valor", "valor_unitario"],
    )
    kwargs = {"venta": venta, "producto": producto, "cantidad": cantidad}
    if price_field:
        kwargs[price_field] = precio_unit
    return DetalleVenta.objects.create(**kwargs)

def _get_accessor_detalleventa():
    """Nombre del related_name real (p.ej. 'detalles')."""
    if not DetalleVenta:
        return None
    try:
        return DetalleVenta._meta.get_field("venta").remote_field.get_accessor_name()
    except Exception:
        return None

def _get_fecha_display(venta):
    """Devuelve fecha en el primer campo existente."""
    for f in ("created_at", "fecha", "fecha_creacion", "timestamp"):
        if _tiene_campo(Venta, f):
            return getattr(venta, f, None)
    return None

def _get_precio_from_detalle(det):
    """Devuelve el precio unitario del detalle, probando campos comunes."""
    for f in ("precio", "precio_unitario", "valor", "valor_unitario"):
        if hasattr(det, f):
            return getattr(det, f)
    return Decimal("0")

def _siguiente_codigo():
    """Próximo código correlativo de 3 dígitos (001, 002...)."""
    max_n = 0
    for c in Producto.objects.values_list("codigo", flat=True):
        try:
            n = int(str(c).strip())
            if n > max_n:
                max_n = n
        except (TypeError, ValueError):
            continue
    return f"{max_n + 1:03d}"


# --------------------- vistas base ---------------------

def home(request):
    return render(request, "inventario/home.html")


# --------------------- Categorías ---------------------

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion"]

def categoria_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Categoria.objects.all().order_by("nombre")
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    page_obj = paginar_queryset(request, qs, 10)
    return render(request, "inventario/categoria_list.html",
                  {"categorias": page_obj.object_list, "page_obj": page_obj, "q": q})

def categoria_crear(request):
    form = CategoriaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoría creada.")
        return redirect("inventario:categoria_list")
    return render(request, "inventario/categoria_form.html", {"form": form, "titulo": "Nueva categoría"})

def categoria_editar(request, pk):
    obj = get_object_or_404(Categoria, pk=pk)
    form = CategoriaForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoría actualizada.")
        return redirect("inventario:categoria_list")
    return render(request, "inventario/categoria_form.html", {"form": form, "titulo": f"Editar categoría: {obj.nombre}"})

def categoria_eliminar(request, pk):
    obj = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Categoría eliminada.")
        return redirect("inventario:categoria_list")
    return render(request, "inventario/categoria_confirm_delete.html", {"obj": obj})


# --------------------- Proveedores ---------------------

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "rut", "telefono", "email"]

def proveedor_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Proveedor.objects.all().order_by("nombre")
    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) |
            Q(rut__icontains=q) |
            Q(telefono__icontains=q) |
            Q(email__icontains=q)
        )
    page_obj = paginar_queryset(request, qs, 10)
    return render(request, "inventario/proveedor_list.html",
                  {"proveedores": page_obj.object_list, "page_obj": page_obj, "q": q})

def proveedor_crear(request):
    form = ProveedorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proveedor creado.")
        return redirect("inventario:proveedor_list")
    return render(request, "inventario/proveedor_form.html", {"form": form, "titulo": "Nuevo proveedor"})

def proveedor_editar(request, pk):
    obj = get_object_or_404(Proveedor, pk=pk)
    form = ProveedorForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proveedor actualizado.")
        return redirect("inventario:proveedor_list")
    return render(request, "inventario/proveedor_form.html", {"form": form, "titulo": f"Editar proveedor: {obj.nombre}"})

def proveedor_eliminar(request, pk):
    obj = get_object_or_404(Proveedor, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Proveedor eliminado.")
        return redirect("inventario:proveedor_list")
    return render(request, "inventario/proveedor_confirm_delete.html", {"obj": obj})


# --------------------- Productos ---------------------

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["codigo", "nombre", "categoria", "precio", "stock", "stock_minimo", "activo"]
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "inp", "placeholder": "Se asignará automáticamente"}),
            "nombre": forms.TextInput(attrs={"class": "inp"}),
            "categoria": forms.Select(attrs={"class": "inp"}),
            "precio": forms.NumberInput(attrs={"class": "inp", "step": "1", "min": "0"}),
            "stock": forms.NumberInput(attrs={"class": "inp", "step": "1", "min": "0"}),
            "stock_minimo": forms.NumberInput(attrs={"class": "inp", "step": "1", "min": "0"}),
            "activo": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        creando = not getattr(self.instance, "pk", None)
        if creando:
            if not self.initial.get("codigo"):
                self.initial["codigo"] = _siguiente_codigo()
            self.fields["codigo"].widget.attrs["readonly"] = "readonly"
            self.fields["codigo"].widget.attrs["style"] = "opacity:.85;cursor:not-allowed;"

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not getattr(obj, "pk", None):
            if not getattr(obj, "codigo", None) or not str(obj.codigo).strip():
                obj.codigo = _siguiente_codigo()
        if commit:
            obj.save()
        return obj

def productos_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Producto.objects.select_related("categoria").all().order_by("nombre")
    if q:
        qs = qs.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q))
    page_obj = paginar_queryset(request, qs, 10)
    return render(request, "inventario/productos_list.html",
                  {"productos": page_obj.object_list, "page_obj": page_obj, "q": q})

def producto_crear(request):
    form = ProductoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto creado.")
        return redirect("inventario:productos_list")
    return render(request, "inventario/producto_form.html", {"form": form, "titulo": "Nuevo producto"})

def producto_editar(request, pk):
    obj = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto actualizado.")
        return redirect("inventario:productos_list")
    return render(request, "inventario/producto_form.html", {"form": form, "titulo": f"Editar producto: {obj.nombre}"})

def producto_eliminar(request, pk):
    obj = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Producto eliminado.")
        return redirect("inventario:productos_list")
    return render(request, "inventario/producto_confirm_delete.html", {"obj": obj})


# --------------------- Compras ---------------------

def compra_nueva(request):
    productos = Producto.objects.filter(activo=True).order_by("nombre")

    if request.method == "POST":
        if not (Compra and DetalleCompra):
            messages.error(request, "Los modelos de Compra/DetalleCompra no están definidos.")
            return redirect("inventario:compra_nueva")

        ids = request.POST.getlist("product_id[]")
        cants = request.POST.getlist("cantidad[]")
        costos = request.POST.getlist("costo[]")
        lineas = []
        for i in range(len(ids)):
            try:
                pid = int(ids[i]) if ids[i] else 0
                cant = Decimal(cants[i] or "0")
                costo = Decimal(costos[i] or "0")
            except (ValueError, InvalidOperation):
                continue
            if pid > 0 and cant > 0 and costo >= 0:
                lineas.append((pid, cant, costo))

        if not lineas:
            messages.error(request, "Agrega al menos un ítem válido.")
            return redirect("inventario:compra_nueva")

        proveedor_nombre = (request.POST.get("proveedor_nombre") or "").strip()
        observacion = (request.POST.get("observacion") or "").strip()

        prov_field = None
        try:
            prov_field = Compra._meta.get_field("proveedor")
        except Exception:
            prov_field = None

        prov_instance = None
        if prov_field:
            if not proveedor_nombre:
                messages.error(request, "Debes indicar un proveedor.")
                return redirect("inventario:compra_nueva")
            prov_instance = Proveedor.objects.filter(nombre=proveedor_nombre).first()
            if not prov_instance:
                prov_instance = Proveedor.objects.create(nombre=proveedor_nombre)

        with transaction.atomic():
            compra = Compra.objects.create(proveedor=prov_instance) if prov_field else Compra.objects.create()

            if _tiene_campo(Compra, "observacion") and observacion:
                compra.observacion = observacion
                compra.save(update_fields=["observacion"])

            total = Decimal("0")
            for pid, cant, costo in lineas:
                prod = Producto.objects.select_for_update().get(pk=pid)
                _crear_detalle_compra(compra=compra, producto=prod, cantidad=cant, precio_unit=costo)
                # Si quieres aumentar stock aquí:
                # prod.stock = (prod.stock or 0) + cant
                # prod.save(update_fields=["stock"])
                total += cant * costo

            if _tiene_campo(Compra, "total"):
                compra.total = total
                compra.save(update_fields=["total"])

        messages.success(request, "Compra registrada.")
        return redirect("inventario:home")

    return render(request, "inventario/compra_nueva.html", {"productos": productos})


# --------------------- POS / Ventas (+ Deuda) ---------------------

def pos_venta(request):
    productos = Producto.objects.filter(activo=True).order_by("nombre")

    if request.method == "POST":
        if not (Venta and DetalleVenta):
            messages.error(request, "Los modelos de Venta/DetalleVenta no están definidos.")
            return redirect("inventario:pos_venta")

        accion = (request.POST.get("accion") or "guardar").strip()  # 'guardar' | 'deuda'
        es_deuda = (accion == "deuda")

        # líneas
        ids = request.POST.getlist("product_id[]")
        cants = request.POST.getlist("cantidad[]")
        precios = request.POST.getlist("precio[]")
        lineas = []
        for i in range(len(ids)):
            try:
                pid = int(ids[i]) if ids[i] else 0
                cant = Decimal(cants[i] or "0")
                precio = Decimal(precios[i] or "0")
            except (ValueError, InvalidOperation):
                continue
            if pid > 0 and cant > 0 and precio >= 0:
                lineas.append((pid, cant, precio))

        if not lineas:
            messages.error(request, "Agrega al menos un ítem válido.")
            return redirect("inventario:pos_venta")

        # cliente para deuda
        cli_instance = None
        if es_deuda:
            nombre = (request.POST.get("cliente_nombre") or "").strip()
            if not nombre:
                messages.error(request, "Para registrar deuda, indica el nombre del deudor.")
                return redirect("inventario:pos_venta")
            cli_instance, _ = Cliente.objects.get_or_create(nombre=nombre, defaults={"activo": True})

        with transaction.atomic():
            # crea venta con flags de deuda
            venta_kwargs = {}
            if _tiene_campo(Venta, "cliente"):
                venta_kwargs["cliente"] = cli_instance
            if _tiene_campo(Venta, "fecha"):
                venta_kwargs["fecha"] = timezone.now()
            if _tiene_campo(Venta, "observacion"):
                venta_kwargs["observacion"] = (request.POST.get("observacion") or "").strip()
            if _tiene_campo(Venta, "es_deuda"):
                venta_kwargs["es_deuda"] = es_deuda
            if _tiene_campo(Venta, "saldada"):
                venta_kwargs["saldada"] = False if es_deuda else True

            venta = Venta.objects.create(**venta_kwargs)

            total = Decimal("0")
            for pid, cant, precio in lineas:
                prod = Producto.objects.select_for_update().get(pk=pid)

                # Control stock y descuenta
                if prod.stock is not None and prod.stock < cant:
                    messages.error(request, f"Stock insuficiente para {prod.nombre}.")
                    transaction.set_rollback(True)
                    return redirect("inventario:pos_venta")

                _crear_detalle_venta(venta=venta, producto=prod, cantidad=cant, precio_unit=precio)

                # Descuento de stock
                try:
                    prod.stock = (prod.stock or 0) - cant
                    prod.save(update_fields=["stock"])
                except Exception:
                    pass

                # Movimiento de stock (opcional)
                try:
                    MovimientoStock.objects.create(
                        producto=prod,
                        tipo=MovimientoStock.SALIDA,
                        cantidad=cant,
                        motivo="Venta a Deuda" if es_deuda else "Venta",
                        fecha=getattr(venta, "fecha", timezone.now()),
                        referencia=f"Venta#{venta.id}",
                    )
                except Exception:
                    pass

                total += cant * precio

            if _tiene_campo(Venta, "total"):
                venta.total = total
                venta.save(update_fields=["total"])

        if es_deuda:
            messages.success(request, f"Deuda registrada para {cli_instance.nombre}.")
            return redirect("inventario:deudores_list")
        else:
            messages.success(request, "Venta registrada correctamente.")
            return redirect("inventario:ventas_list")

    return render(request, "inventario/pos_venta.html", {"productos": productos})


# --------------------- Deudores ---------------------

def deudores_list(request):
    if not Venta:
        messages.error(request, "El modelo Venta no está definido.")
        return redirect("inventario:home")

    if not (_tiene_campo(Venta, "es_deuda") and _tiene_campo(Venta, "saldada")):
        # Sin campos, no hay deudores que mostrar
        return render(request, "inventario/deudores_list.html", {"rows": []})

    clientes = (
        Cliente.objects.filter(ventas__es_deuda=True, ventas__saldada=False)
        .distinct()
        .order_by("nombre")
    )

    rows = []
    for cli in clientes:
        ventas_cli = cli.ventas.filter(es_deuda=True, saldada=False).prefetch_related("detalles", "detalles__producto")
        total = Decimal("0")
        ultima = None
        for v in ventas_cli:
            if ultima is None or (getattr(v, "fecha", None) and v.fecha > ultima):
                ultima = getattr(v, "fecha", ultima)
            accessor = _get_accessor_detalleventa()
            dets = getattr(v, accessor).all() if accessor else []
            for d in dets:
                total += (getattr(d, "cantidad", 0) or 0) * (_get_precio_from_detalle(d) or 0)
        rows.append({"cliente": cli, "total": total, "ultima": ultima})

    return render(request, "inventario/deudores_list.html", {"rows": rows})

def deudor_detalle(request, pk):
    if not Venta:
        messages.error(request, "El modelo Venta no está definido.")
        return redirect("inventario:home")

    cli = get_object_or_404(Cliente, pk=pk)
    ventas = cli.ventas.filter(es_deuda=True).order_by("-fecha").prefetch_related("detalles", "detalles__producto")

    filas = []
    for v in ventas:
        accessor = _get_accessor_detalleventa()
        dets = getattr(v, accessor).all() if accessor else []
        total = Decimal("0")
        for d in dets:
            total += (getattr(d, "cantidad", 0) or 0) * (_get_precio_from_detalle(d) or 0)
        filas.append({"venta": v, "total": total})

    return render(request, "inventario/deudor_detalle.html", {"cliente": cli, "filas": filas})


# --------------------- Ventas (listado/detalle) ---------------------

def ventas_list(request):
    if not Venta:
        messages.error(request, "El modelo Venta no está definido.")
        return redirect("inventario:home")

    qs = Venta.objects.all().order_by("-id")

    accessor = _get_accessor_detalleventa()
    if accessor:
        qs = qs.annotate(items=Count(accessor))

    page_obj = paginar_queryset(request, qs, 10)

    ventas_fmt = []
    for v in page_obj.object_list:
        ventas_fmt.append({
            "obj": v,
            "id": v.id,
            "fecha": _get_fecha_display(v),
            "total": getattr(v, "total", None),
            "items": getattr(v, "items", None),
        })

    return render(request, "inventario/ventas_list.html",
                  {"ventas": ventas_fmt, "page_obj": page_obj})

def ventas_detalle(request, pk):
    if not (Venta and DetalleVenta):
        messages.error(request, "Los modelos de Venta/DetalleVenta no están definidos.")
        return redirect("inventario:ventas_list")

    venta = get_object_or_404(Venta, pk=pk)

    accessor = _get_accessor_detalleventa()
    detalles = getattr(venta, accessor).select_related("producto").all() if accessor else []

    lineas = []
    total = Decimal("0")
    for d in detalles:
        producto = getattr(d, "producto", None)
        nombre = getattr(producto, "nombre", "—")
        cantidad = getattr(d, "cantidad", 0)
        precio = _get_precio_from_detalle(d)
        subtotal = (cantidad or 0) * (precio or 0)
        total += subtotal
        lineas.append({
            "producto": nombre,
            "cantidad": cantidad,
            "precio": precio,
            "subtotal": subtotal,
        })

    if hasattr(venta, "total") and venta.total:
        total = venta.total

    contexto = {
        "venta": venta,
        "fecha": _get_fecha_display(venta),
        "lineas": lineas,
        "total": total,
    }
    return render(request, "inventario/ventas_detalle.html", contexto)


# --------------------- Reportes ---------------------

def reporte_stock_bajo(request):
    productos = (Producto.objects
                 .select_related("categoria")
                 .filter(stock__lte=F("stock_minimo"))
                 .order_by("categoria__nombre", "nombre"))
    return render(request, "inventario/reporte_stock_bajo.html", {"productos": productos})
