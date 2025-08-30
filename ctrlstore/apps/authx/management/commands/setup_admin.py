from __future__ import annotations

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from ctrlstore.apps.authx.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = "Configura el usuario administrador y roles básicos del sistema"

    def handle(self, *args, **options):
        self.stdout.write("Configurando roles básicos...")
        
        # Crear roles básicos
        admin_role, created = Role.objects.get_or_create(
            name="Administrador",
            defaults={
                "description": "Acceso completo al sistema",
                "is_active": True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Rol 'Administrador' creado")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠ Rol 'Administrador' ya existe")
            )
        
        staff_role, created = Role.objects.get_or_create(
            name="Staff",
            defaults={
                "description": "Gestión de productos y pedidos",
                "is_active": True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Rol 'Staff' creado")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠ Rol 'Staff' ya existe")
            )
        
        cliente_role, created = Role.objects.get_or_create(
            name="Cliente",
            defaults={
                "description": "Acceso básico de compras",
                "is_active": True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Rol 'Cliente' creado")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠ Rol 'Cliente' ya existe")
            )
        
        # Crear superusuario si no existe
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Creando superusuario...")
            
            admin_user = User.objects.create_superuser(
                username="admin",
                email="admin@ctrlstore.com",
                password="admin123",
                first_name="Administrador",
                last_name="Sistema",
                role=admin_role,
                is_verified=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Superusuario creado: {admin_user.username}"
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "⚠ Credenciales: admin / admin123"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠ Superusuario ya existe")
            )
        
        self.stdout.write(
            self.style.SUCCESS("✓ Configuración completada")
        )
