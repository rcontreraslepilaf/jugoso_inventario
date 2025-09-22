from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Q, F, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django import forms
from django.apps import apps

from .models import Categoria, Proveedor, Producto

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
                total += cant * costo

            if _tiene_campo(Compra, "total"):
                compra.total = total
                compra.save(update_fields=["total"])

        messages.success(request, "Compra registrada y stock actualizado.")
        return redirect("inventario:home")

    return render(request, "inventario/compra_nueva.html", {"productos": productos})


# --------------------- POS / Ventas ---------------------

def pos_venta(request):
    productos = Producto.objects.filter(activo=True).order_by("nombre")

    if request.method == "POST":
        if not (Venta and DetalleVenta):
            messages.error(request, "Los modelos de Venta/DetalleVenta no están definidos.")
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
            except (ValueError, InvalidOperation):
                continue
            # <--- CORREGIDO: sin coma
            if pid > 0 and cant > 0 and precio >= 0:
                lineas.append((pid, cant, precio))

        if not lineas:
            messages.error(request, "Agrega al menos un ítem válido.")
            return redirect("inventario:pos_venta")

        with transaction.atomic():
            venta = Venta.objects.create()
            total = Decimal("0")
            for pid, cant, precio in lineas:
                prod = Producto.objects.select_for_update().get(pk=pid)
                if prod.stock is not None and prod.stock < cant:
                    messages.error(request, f"Stock insuficiente para {prod.nombre}.")
                    transaction.set_rollback(True)
                    return redirect("inventario:pos_venta")
                _crear_detalle_venta(venta=venta, producto=prod, cantidad=cant, precio_unit=precio)
                total += cant * precio

            if _tiene_campo(Venta, "total"):
                venta.total = total
                venta.save(update_fields=["total"])

        messages.success(request, "Venta registrada y stock actualizado.")
        return redirect("inventario:ventas_list")

    return render(request, "inventario/pos_venta.html", {"productos": productos})

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
