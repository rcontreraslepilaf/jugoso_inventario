from rest_framework.permissions import BasePermission, SAFE_METHODS

def user_in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()

class RolePermission(BasePermission):
    """
    - Admin: todo permitido.
    - Vendedor: lectura global + puede crear movimientos (POST /movimientos).
    - Consultor: solo lectura.
    """
    def has_permission(self, request, view):
        user = request.user

        # Anónimo: solo lectura (puedes cambiarlo a False si quieres forzar login para todo)
        if not user.is_authenticated:
            return request.method in SAFE_METHODS

        if user.is_superuser or user_in_group(user, "Administrador"):
            return True

        if user_in_group(user, "Consultor"):
            return request.method in SAFE_METHODS

        if user_in_group(user, "Vendedor"):
            if request.method in SAFE_METHODS:
                return True
            # Vendedor solo puede escribir en vistas que lo habiliten (movimientos)
            return getattr(view, "allow_vendor_write", False)

        # Otros: solo lectura
        return request.method in SAFE_METHODS
