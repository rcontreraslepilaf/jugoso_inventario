# inventario/forms.py
from django import forms
from django.db.models import Max, IntegerField
from django.db.models.functions import Cast

from .models import Producto


def _siguiente_codigo(pad: int = 3) -> str:
    """
    Busca el mayor 'codigo' numérico en Producto, le suma 1 y lo devuelve
    con relleno a la izquierda (por defecto 3 dígitos: 001, 002, ...).
    Si no hay productos aún, devolverá '001'.
    """
    max_val = (
        Producto.objects
        .exclude(codigo__isnull=True)
        .exclude(codigo__exact='')
        .annotate(cint=Cast('codigo', IntegerField()))
        .aggregate(m=Max('cint'))['m'] or 0
    )
    return str(max_val + 1).zfill(pad)


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'categoria', 'precio', 'stock', 'stock_minimo', 'activo']
        widgets = {
            # lo mostramos pero en solo lectura
            'codigo': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Si es creación (no hay PK), proponemos el siguiente código y lo
        dejamos en solo lectura. En edición, respetamos el existente.
        """
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            # Solo si el initial no trae código ya (por si la vista lo setea)
            if not self.initial.get('codigo'):
                self.initial['codigo'] = _siguiente_codigo()
