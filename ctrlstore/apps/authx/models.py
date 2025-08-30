from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class Role(models.Model):
    """Modelo para roles de usuario en el sistema."""
    
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Nombre"))
    description = models.TextField(blank=True, verbose_name=_("Descripción"))
    is_active = models.BooleanField(default=True, verbose_name=_("Activo"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de creación"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de actualización"))

    class Meta:
        ordering = ["name"]
        verbose_name = _("Rol")
        verbose_name_plural = _("Roles")

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """Modelo de usuario extendido con roles y permisos."""
    
    # Campos adicionales
    phone = models.CharField(max_length=15, blank=True, verbose_name=_("Teléfono"))
    address = models.TextField(blank=True, verbose_name=_("Dirección"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verificado"))
    
    # Relación con roles
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name=_("Rol")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de registro"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de actualización"))

    class Meta:
        verbose_name = _("Usuario")
        verbose_name_plural = _("Usuarios")
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return f"{self.username} ({self.get_full_name()})"

    @property
    def is_admin(self) -> bool:
        """Verifica si el usuario es administrador."""
        return self.role and self.role.name.lower() in ["admin", "administrador"]

    @property
    def is_staff_member(self) -> bool:
        """Verifica si el usuario es personal del sistema."""
        return self.role and self.role.name.lower() in ["admin", "administrador", "staff", "empleado"]

    def get_role_display_name(self) -> str:
        """Obtiene el nombre del rol del usuario."""
        return self.role.name if self.role else _("Sin rol")
