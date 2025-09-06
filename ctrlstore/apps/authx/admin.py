from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin para el modelo Role."""
    
    list_display = ["name", "description", "is_active", "created_at", "users_count"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["name"]
    
    fieldsets = (
        (None, {"fields": ("name", "description")}),
        (_("Estado"), {"fields": ("is_active",)}),
    )
    
    def users_count(self, obj: Role) -> int:
        """Cuenta el número de usuarios con este rol."""
        return obj.users.count()
    users_count.short_description = _("Usuarios")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin para el modelo User personalizado."""
    
    list_display = [
        "username", 
        "email", 
        "first_name", 
        "last_name", 
        "role", 
        "is_staff", 
        "is_active"
    ]
    list_filter = [
        "role", 
        "is_staff", 
        "is_active", 
        "created_at"
    ]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering = ["-date_joined"]
    
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Información personal"), {
            "fields": ("first_name", "last_name", "email", "phone", "address")
        }),
        (_("Permisos"), {
            "fields": (
                "role",
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        (_("Fechas importantes"), {"fields": ("last_login", "date_joined")}),
    )
    
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username", 
                "email", 
                "password1", 
                "password2", 
                "role",
                "is_staff",
                "is_active"
            ),
        }),
    )
    
    readonly_fields = ["last_login", "date_joined", "created_at", "updated_at"]
