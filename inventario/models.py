from django.db import models
from django.utils import timezone

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    nombre = models.CharField(max_length=120)
    rut = models.CharField(max_length=15, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    nombre = models.CharField(max_length=120)
    rut = models.CharField(max_length=15, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=120)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    unidad = models.CharField(max_length=20, default='unidad')  # unidad, kg, lt, pack
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # precio de venta
    stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Compra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras')
    fecha = models.DateTimeField(default=timezone.now)
    observacion = models.TextField(blank=True)

    def total(self):
        return sum(d.subtotal() for d in self.detalles.all())

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor} - {self.fecha:%Y-%m-%d}"


class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.costo_unitario


class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ventas', null=True, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    observacion = models.TextField(blank=True)

    def total(self):
        return sum(d.subtotal() for d in self.detalles.all())

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha:%Y-%m-%d}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario


class MovimientoStock(models.Model):
    ENTRADA = 'E'
    SALIDA = 'S'
    TIPO_CHOICES = [(ENTRADA, 'Entrada'), (SALIDA, 'Salida')]

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    motivo = models.CharField(max_length=120, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(max_length=80, blank=True)  # ej: Compra#ID, Venta#ID

    def __str__(self):
        return f"{self.get_tipo_display()} {self.cantidad} de {self.producto} en {self.fecha:%Y-%m-%d}"
