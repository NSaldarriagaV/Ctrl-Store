from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView


class AdminRequiredMixin:
    """Mixin para requerir acceso de administrador."""
    
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder al panel de administración.")
            return redirect(reverse_lazy("authx:login"))
        
        # Permitir acceso si el usuario es superusuario o cumple la regla de rol admin
        if not (getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_admin', False)):
            messages.error(request, "No tienes permisos para acceder al panel de administración.")
            return redirect(reverse_lazy("catalog:product_list"))
        
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin:
    """Mixin para requerir acceso de personal del sistema."""
    
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
            return redirect(reverse_lazy("authx:login"))
        
        if not hasattr(request.user, 'is_staff_member') or not request.user.is_staff_member:
            messages.error(request, "No tienes permisos para acceder a esta sección.")
            return redirect(reverse_lazy("catalog:product_list"))
        
        return super().dispatch(request, *args, **kwargs)
