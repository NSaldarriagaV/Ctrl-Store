from __future__ import annotations

from typing import Any

from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .mixins import AdminRequiredMixin, StaffRequiredMixin
from .forms import SignupForm, UserEditForm


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
class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Dashboard principal del panel de administración."""
    template_name = "authx/admin/dashboard.html"
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        # Estadísticas básicas para el dashboard
        from ctrlstore.apps.catalog.models import Category, Product
        from ctrlstore.apps.authx.models import User
        
        context.update({
            "total_users": User.objects.count(),
            "total_products": Product.objects.count(),
            "total_categories": Category.objects.count(),
            "gaming_products": Product.objects.filter(is_gaming=True).count(),
            "recent_users": User.objects.select_related("role").order_by("-date_joined")[:5],
            "recent_products": Product.objects.select_related("category").order_by("-created_at")[:5],
        })
        
        return context


class AdminUsersView(AdminRequiredMixin, TemplateView):
    """Vista para gestión de usuarios."""
    template_name = "authx/admin/users.html"
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        from ctrlstore.apps.authx.models import User, Role
        
        # Aplicar filtros
        users = User.objects.select_related("role").order_by("-date_joined")
        
        # Filtro por rol
        role_filter = self.request.GET.get("role")
        if role_filter:
            users = users.filter(role_id=role_filter)
        
        # Filtro por estado
        status_filter = self.request.GET.get("status")
        if status_filter == "active":
            users = users.filter(is_active=True)
        elif status_filter == "inactive":
            users = users.filter(is_active=False)
        
        # Filtro por búsqueda
        search = self.request.GET.get("search")
        if search:
            users = users.filter(
                username__icontains=search
            ) | users.filter(
                email__icontains=search
            ) | users.filter(
                first_name__icontains=search
            ) | users.filter(
                last_name__icontains=search
            )
        
        context.update({
            "users": users,
            "roles": Role.objects.all(),
        })
        
        return context


class AdminRolesView(AdminRequiredMixin, TemplateView):
    """Vista para gestión de roles."""
    template_name = "authx/admin/roles.html"
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        from ctrlstore.apps.authx.models import Role
        
        roles = Role.objects.prefetch_related("users").all()
        
        context.update({
            "roles": roles,
            "active_roles": roles.filter(is_active=True).count(),
        })
        
        return context


# Vistas para acciones de usuarios
@method_decorator(csrf_exempt, name='dispatch')
class UserToggleStatusView(AdminRequiredMixin, TemplateView):
    """Vista para activar/desactivar usuarios."""
    
    def post(self, request: HttpRequest, user_id: int) -> JsonResponse:
        from ctrlstore.apps.authx.models import User
        
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        return JsonResponse({
            'success': True,
            'is_active': user.is_active,
            'message': f'Usuario {"activado" if user.is_active else "desactivado"} correctamente'
        })


class UserDetailView(AdminRequiredMixin, TemplateView):
    """Vista para ver detalles de usuario."""
    template_name = "authx/admin/user_detail.html"
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        from ctrlstore.apps.authx.models import User
        
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        
        context.update({
            "user_detail": user,
        })
        
        return context


class UserEditView(AdminRequiredMixin, FormView):
    """Vista para editar usuario."""
    template_name = "authx/admin/user_edit.html"
    form_class = UserEditForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_id = self.kwargs.get('user_id')
        from ctrlstore.apps.authx.models import User
        self.user = get_object_or_404(User, id=user_id)
        kwargs['instance'] = self.user
        return kwargs
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['user_detail'] = self.user
        return context
    
    def form_valid(self, form):
        form.save()
        return redirect('authx:admin_users')
