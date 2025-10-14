from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from inventario.models import Producto, Categoria, Proveedor, Bodega
# Movimiento puede llamarse MovimientoStock o Movimiento
try:
    from inventario.models import MovimientoStock as MovimientoModel
except Exception:
    from inventario.models import Movimiento as MovimientoModel

class Command(BaseCommand):
    help = "Crea grupos (Administrador, Vendedor, Consultor) y usuarios de ejemplo"

    def handle(self, *args, **kwargs):
        admin_group, _ = Group.objects.get_or_create(name="Administrador")
        vendedor_group, _ = Group.objects.get_or_create(name="Vendedor")
        consultor_group, _ = Group.objects.get_or_create(name="Consultor")

        models = [Producto, Categoria, Proveedor, Bodega, MovimientoModel]
        ctypes = [ContentType.objects.get_for_model(m) for m in models]
        all_perms = Permission.objects.filter(content_type__in=ctypes)

        # Admin: todos
        admin_group.permissions.set(all_perms)

        # Vendedor: view_* + add_movimiento*
        vendedor_perms = [p for p in all_perms if (
            p.codename.startswith("view_") or p.codename.startswith("add_movimiento")
        )]
        vendedor_group.permissions.set(vendedor_perms)

        # Consultor: solo view_*
        consultor_perms = [p for p in all_perms if p.codename.startswith("view_")]
        consultor_group.permissions.set(consultor_perms)

        # Usuarios demo
        if not User.objects.filter(username="admin_demo").exists():
            u = User.objects.create_user("admin_demo", password="Admin@2025")
            u.is_staff = True; u.is_superuser = True; u.save()
        if not User.objects.filter(username="vendedor_demo").exists():
            u = User.objects.create_user("vendedor_demo", password="Vendedor@2025")
            u.groups.add(vendedor_group)
        if not User.objects.filter(username="consultor_demo").exists():
            u = User.objects.create_user("consultor_demo", password="Consultor@2025")
            u.groups.add(consultor_group)

        self.stdout.write(self.style.SUCCESS("Grupos y usuarios de demo creados."))
