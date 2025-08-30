from __future__ import annotations

from typing import Any

from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .decorators import admin_required, staff_required
from .forms import SignupForm


class SignupView(FormView):
    template_name = "authx/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("catalog:product_list")

    def form_valid(self, form: SignupForm) -> HttpResponse:
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

    # Opcional: hints explícitos para mypy/ruff (no requerido)
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # noqa: D401
        """Renderiza el formulario de registro."""
        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # noqa: D401
        """Procesa el envío del formulario de registro."""
        return super().post(request, *args, **kwargs)


class CustomLoginView(LoginView):
    """Vista de login personalizada."""
    template_name = "authx/login.html"
    success_url = reverse_lazy("catalog:product_list")


class CustomLogoutView(LogoutView):
    """Vista de logout personalizada."""
    next_page = reverse_lazy("catalog:product_list")


# Vistas del Panel de Administración
class AdminDashboardView(TemplateView):
    """Dashboard principal del panel de administración."""
    template_name = "authx/admin/dashboard.html"
    
    @admin_required
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        # Estadísticas básicas para el dashboard
        from ctrlstore.apps.catalog.models import Category, Product
        from ctrlstore.apps.authx.models import User
        
        context.update({
            "total_users": User.objects.count(),
            "total_products": Product.objects.count(),
            "total_categories": Category.objects.count(),
            "recent_users": User.objects.order_by("-date_joined")[:5],
            "recent_products": Product.objects.order_by("-created_at")[:5],
        })
        
        return context


class AdminUsersView(TemplateView):
    """Vista para gestión de usuarios."""
    template_name = "authx/admin/users.html"
    
    @admin_required
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        from ctrlstore.apps.authx.models import User, Role
        
        context.update({
            "users": User.objects.select_related("role").order_by("-date_joined"),
            "roles": Role.objects.all(),
        })
        
        return context


class AdminRolesView(TemplateView):
    """Vista para gestión de roles."""
    template_name = "authx/admin/roles.html"
    
    @admin_required
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        from ctrlstore.apps.authx.models import Role
        
        context.update({
            "roles": Role.objects.prefetch_related("users").all(),
        })
        
        return context
