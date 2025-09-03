from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Role

User = get_user_model()


@receiver(post_save, sender=User)
def assign_default_role(sender: type[User], instance: User, created: bool, **kwargs) -> None:
    """
    Asigna automáticamente el rol adecuado a usuarios nuevos:
    - Si es superusuario y no tiene rol, asigna 'Administrador' (o crea si falta).
    - Si no tiene rol, asigna 'Cliente' por defecto (o crea si falta).
    """
    if not created or instance.role:
        return

    # Si es superusuario, asignar rol de Administrador
    if getattr(instance, "is_superuser", False):
        admin_role = None
        # Buscar por variantes de nombre aceptadas
        for name in ("Administrador", "admin", "ADMINISTRADOR", "ADMIN"):
            try:
                admin_role = Role.objects.get(name=name)
                break
            except Role.DoesNotExist:
                continue
        if admin_role is None:
            admin_role = Role.objects.create(
                name="Administrador",
                description="Acceso completo al sistema",
                is_active=True,
            )
        instance.role = admin_role
        instance.save(update_fields=["role"])
        return

    # En caso contrario, asignar Cliente por defecto
    try:
        cliente_role = Role.objects.get(name="Cliente")
    except Role.DoesNotExist:
        cliente_role = Role.objects.create(
            name="Cliente",
            description="Acceso básico de compras",
            is_active=True,
        )
    instance.role = cliente_role
    instance.save(update_fields=["role"])