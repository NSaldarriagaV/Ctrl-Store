from __future__ import annotations

from functools import wraps
from typing import Callable

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy


def admin_required(view_func: Callable) -> Callable:
    """
    Decorador para requerir acceso de administrador.
    
    Verifica que el usuario esté autenticado y tenga rol de administrador.
    """
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder al panel de administración.")
            return redirect(reverse_lazy("authx:login"))
        
        if not hasattr(request.user, 'is_admin') or not request.user.is_admin:
            messages.error(request, "No tienes permisos para acceder al panel de administración.")
            return redirect(reverse_lazy("catalog:product_list"))
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def staff_required(view_func: Callable) -> Callable:
    """
    Decorador para requerir acceso de personal del sistema.
    
    Verifica que el usuario esté autenticado y tenga rol de staff o admin.
    """
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
            return redirect(reverse_lazy("authx:login"))
        
        if not hasattr(request.user, 'is_staff_member') or not request.user.is_staff_member:
            messages.error(request, "No tienes permisos para acceder a esta sección.")
            return redirect(reverse_lazy("catalog:product_list"))
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
