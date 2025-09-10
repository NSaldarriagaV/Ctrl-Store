"""
Servicios de autenticación y gestión de usuarios.
Implementa la lógica de negocio siguiendo el principio "Thin Views, Fat Services".
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpRequest

from .models import Role

if TYPE_CHECKING:
    from .forms import SignupForm, UserEditForm

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Servicio para operaciones de autenticación."""
    
    @staticmethod
    def register_user(form: SignupForm, request: HttpRequest) -> User:
        """
        Registra un nuevo usuario y lo autentica.
        
        Args:
            form: Formulario de registro validado
            request: Request HTTP
            
        Returns:
            Usuario creado y autenticado
            
        Raises:
            ValueError: Si hay errores en el registro
        """
        try:
            with transaction.atomic():
                user = form.save()
                login(request, user)
                
                logger.info(
                    "Usuario registrado exitosamente",
                    extra={
                        "user_id": user.id,
                        "username": user.username,
                        "email": user.email,
                    }
                )
                
                return user
                
        except Exception as e:
            logger.error(
                "Error al registrar usuario",
                extra={
                    "error": str(e),
                    "form_data": form.cleaned_data if hasattr(form, 'cleaned_data') else None,
                }
            )
            raise ValueError(f"Error al registrar usuario: {str(e)}")
    
    @staticmethod
    def get_user_dashboard_url(user: User) -> str:
        """
        Determina la URL del dashboard según el rol del usuario.
        
        Args:
            user: Usuario autenticado
            
        Returns:
            URL del dashboard apropiado
        """
        is_admin = (getattr(user, 'is_superuser', False) or 
                   getattr(user, 'is_admin', False))
        
        is_staff = (hasattr(user, 'role') and 
                   user.role and 
                   user.role.name.lower() == 'staff')
        
        if is_admin:
            return "authx:admin_dashboard"
        elif is_staff:
            return "authx:staff_dashboard"
        else:
            return "catalog:product_list"


class RoleService:
    """Servicio para gestión de roles."""
    
    @staticmethod
    def create_role(name: str, description: str = "", is_active: bool = True) -> Role:
        """
        Crea un nuevo rol en el sistema.
        
        Args:
            name: Nombre del rol
            description: Descripción del rol
            is_active: Si el rol está activo
            
        Returns:
            Rol creado
            
        Raises:
            ValueError: Si el rol ya existe
        """
        if Role.objects.filter(name=name).exists():
            raise ValueError(f"El rol '{name}' ya existe")
        
        role = Role.objects.create(
            name=name,
            description=description,
            is_active=is_active
        )
        
        logger.info(
            "Rol creado exitosamente",
            extra={
                "role_id": role.id,
                "role_name": role.name,
            }
        )
        
        return role
    
    @staticmethod
    def update_role(role_id: int, name: str, description: str = "", is_active: bool = True) -> Role:
        """
        Actualiza un rol existente.
        
        Args:
            role_id: ID del rol a actualizar
            name: Nuevo nombre del rol
            description: Nueva descripción
            is_active: Nuevo estado activo
            
        Returns:
            Rol actualizado
            
        Raises:
            ValueError: Si el rol no existe o el nombre ya está en uso
        """
        try:
            role = Role.objects.get(id=role_id)
            
            # Verificar si el nuevo nombre ya existe en otro rol
            if name != role.name and Role.objects.filter(name=name).exists():
                raise ValueError(f"El rol '{name}' ya existe")
            
            role.name = name
            role.description = description
            role.is_active = is_active
            role.save()
            
            logger.info(
                "Rol actualizado exitosamente",
                extra={
                    "role_id": role.id,
                    "role_name": role.name,
                }
            )
            
            return role
            
        except Role.DoesNotExist:
            raise ValueError(f"El rol con ID {role_id} no existe")
    
    @staticmethod
    def delete_role(role_id: int) -> bool:
        """
        Elimina un rol si no tiene usuarios asignados.
        
        Args:
            role_id: ID del rol a eliminar
            
        Returns:
            True si se eliminó exitosamente
            
        Raises:
            ValueError: Si el rol no existe o tiene usuarios asignados
        """
        try:
            role = Role.objects.get(id=role_id)
            
            # Verificar si tiene usuarios asignados
            if role.users.exists():
                raise ValueError(f"El rol '{role.name}' tiene usuarios asignados y no puede ser eliminado")
            
            role_name = role.name
            role.delete()
            
            logger.info(
                "Rol eliminado exitosamente",
                extra={
                    "role_id": role_id,
                    "role_name": role_name,
                }
            )
            
            return True
            
        except Role.DoesNotExist:
            raise ValueError(f"El rol con ID {role_id} no existe")


class UserService:
    """Servicio para gestión de usuarios."""
    
    @staticmethod
    def update_user_profile(user: User, form: UserEditForm) -> User:
        """
        Actualiza el perfil de un usuario.
        
        Args:
            user: Usuario a actualizar
            form: Formulario con los datos actualizados
            
        Returns:
            Usuario actualizado
            
        Raises:
            ValueError: Si hay errores en la actualización
        """
        try:
            with transaction.atomic():
                user.first_name = form.cleaned_data.get('first_name', user.first_name)
                user.last_name = form.cleaned_data.get('last_name', user.last_name)
                user.email = form.cleaned_data.get('email', user.email)
                user.phone = form.cleaned_data.get('phone', user.phone)
                user.address = form.cleaned_data.get('address', user.address)
                user.role = form.cleaned_data.get('role', user.role)
                user.save()
                
                logger.info(
                    "Perfil de usuario actualizado exitosamente",
                    extra={
                        "user_id": user.id,
                        "username": user.username,
                    }
                )
                
                return user
                
        except Exception as e:
            logger.error(
                "Error al actualizar perfil de usuario",
                extra={
                    "user_id": user.id,
                    "error": str(e),
                }
            )
            raise ValueError(f"Error al actualizar perfil: {str(e)}")
