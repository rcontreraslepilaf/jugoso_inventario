from django import forms
from .models import Categoria, Proveedor, Producto

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "inp"}),
            "descripcion": forms.Textarea(attrs={"class": "inp", "rows": 3}),
        }

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "rut", "telefono", "email"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "inp"}),
            "rut": forms.TextInput(attrs={"class": "inp"}),
            "telefono": forms.TextInput(attrs={"class": "inp"}),
            "email": forms.EmailInput(attrs={"class": "inp"}),
        }

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["codigo", "nombre", "categoria", "precio", "stock", "stock_minimo", "activo"]
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "inp"}),
            "nombre": forms.TextInput(attrs={"class": "inp"}),
            "categoria": forms.Select(attrs={"class": "inp"}),
            "precio": forms.NumberInput(attrs={"class": "inp", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "inp", "step": "0.001"}),
            "stock_minimo": forms.NumberInput(attrs={"class": "inp", "step": "0.001"}),
            "activo": forms.CheckboxInput(attrs={"class": "chk"}),
        }
