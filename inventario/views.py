from django.shortcuts import render
from django.db.models import F
from .models import Producto

def reporte_stock_bajo(request):
    productos = Producto.objects.filter(activo=True).filter(
        stock__lte=F('stock_minimo')
    ).order_by('categoria__nombre', 'nombre')
    return render(request, 'inventario/reporte_stock_bajo.html', {'productos': productos})
