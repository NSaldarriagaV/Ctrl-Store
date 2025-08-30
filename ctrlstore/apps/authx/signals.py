from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Role

User = get_user_model()


@receiver(post_save, sender=User)
def assign_default_role(sender: type[User], instance: User, created: bool, **kwargs) -> None:
    """
    Asigna automáticamente el rol de Cliente a usuarios nuevos que no tengan rol asignado.
    """
    if created and not instance.role:
        try:
            cliente_role = Role.objects.get(name="Cliente")
            instance.role = cliente_role
            instance.save(update_fields=['role'])
        except Role.DoesNotExist:
            # Crear rol de Cliente si no existe
            cliente_role = Role.objects.create(
                name="Cliente",
                description="Acceso básico de compras",
                is_active=True
            )
            instance.role = cliente_role
            instance.save(update_fields=['role'])
