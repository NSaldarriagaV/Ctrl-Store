from __future__ import annotations

import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView

from ctrlstore.apps.common.exceptions import (AuthenticationError, RoleError,
                                              UserError)
from ctrlstore.apps.common.logging_config import authx_logger

from .forms import SignupForm, UserEditForm
from .mixins import AdminRequiredMixin, StaffAdminMixin, StaffRequiredMixin
from .services import AuthenticationService, RoleService, UserService

from datetime import datetime, timedelta
from decimal import Decimal

from django.apps import apps
from django.db.models import Sum, Count, F
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.views.generic import TemplateView, View

# i18n (solo se usa en signup/login/logout)
from django.utils.translation import gettext as _


class SignupView(FormView):
    """Vista para registro de nuevos usuarios."""

    template_name = "authx/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("catalog:product_list")

    def form_valid(self, form: SignupForm) -> HttpResponse:
        """Procesa el formulario de registro usando el servicio."""
        try:
            user = AuthenticationService.register_user(form, self.request)
            authx_logger.log_user_action(
                "user_registered", user_id=user.id, username=user.username, email=user.email
            )
            return super().form_valid(form)
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            authx_logger.log_error(e, {"action": "user_registration"})
            messages.error(self.request, _("Error al registrar usuario. Intente nuevamente."))
            return self.form_invalid(form)


class CustomLoginView(LoginView):
    """Vista de login personalizada."""

    template_name = "authx/login.html"
    success_url = reverse_lazy("catalog:product_list")

    def get_success_url(self):
        """Redirige según el rol del usuario después del login."""
        user = self.request.user

        try:
            dashboard_url = AuthenticationService.get_user_dashboard_url(user)
            authx_logger.log_user_action(
                "user_login", user_id=user.id, username=user.username, dashboard_url=dashboard_url
            )
            return reverse_lazy(dashboard_url)
        except Exception as e:
            authx_logger.log_error(e, {"action": "login_redirect", "user_id": user.id})
            return reverse_lazy("catalog:product_list")


class CustomLogoutView(LogoutView):
    """Vista de logout personalizada."""

    next_page = reverse_lazy("catalog:product_list")


class SmartAdminRedirectView(TemplateView):
    """Vista que redirige automáticamente según el rol del usuario."""

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect("authx:login")

        # Verificar si el usuario es admin
        is_admin = getattr(request.user, "is_superuser", False) or getattr(
            request.user, "is_admin", False
        )

        # Verificar si el usuario es staff
        is_staff = (
            hasattr(request.user, "role")
            and request.user.role
            and request.user.role.name.lower() == "staff"
        )

        if is_admin:
            return redirect("authx:admin_dashboard")
        elif is_staff:
            return redirect("authx:staff_dashboard")
        else:
            messages.error(request, "No tienes permisos para acceder al panel de administración.")
            return redirect("catalog:product_list")


# Vistas del Panel de Administración
class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Dashboard principal del panel de administración."""

    template_name = "authx/admin/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Estadísticas básicas para el dashboard
        from ctrlstore.apps.authx.models import User
        from ctrlstore.apps.catalog.models import Category, Product

        # authx/views.py dentro de AdminDashboardView.get_context_data
        Order = apps.get_model("order", "Order")
        last_30 = timezone.now() - timedelta(days=30)

        context.update(
            {
                "total_users": User.objects.count(),
                "total_products": Product.objects.count(),
                "total_categories": Category.objects.count(),
                "gaming_products": Product.objects.filter(category__category_type="gaming").count(),
                "recent_users": User.objects.select_related("role").order_by("-date_joined")[:5],
                "recent_products": Product.objects.select_related("category").order_by("-created_at")[:5],
                "orders_paid_30": Order.objects.filter(status="paid", created_at__gte=last_30).count(),
                "revenue_30": Order.objects.filter(status="paid", created_at__gte=last_30).aggregate(s=Sum("total_amount"))["s"]
                or Decimal("0.00"),
            }
        )

        return context
    


class AdminUsersView(AdminRequiredMixin, TemplateView):
    """Vista para gestión de usuarios."""

    template_name = "authx/admin/users.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        from ctrlstore.apps.authx.models import Role, User

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
            users = (
                users.filter(username__icontains=search)
                | users.filter(email__icontains=search)
                | users.filter(first_name__icontains=search)
                | users.filter(last_name__icontains=search)
            )

        context.update(
            {
                "users": users,
                "roles": Role.objects.all(),
            }
        )

        return context


class AdminRolesView(AdminRequiredMixin, TemplateView):
    """Vista para gestión de roles."""

    template_name = "authx/admin/roles.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        from ctrlstore.apps.authx.models import Role

        roles = Role.objects.prefetch_related("users").all()

        context.update(
            {
                "roles": roles,
                "active_roles": roles.filter(is_active=True).count(),
            }
        )

        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Maneja la creación de roles."""
        from django.contrib import messages

        from ctrlstore.apps.authx.models import Role

        action = request.POST.get("action")

        if action == "create_role":
            name = request.POST.get("name", "").strip()
            custom_name = request.POST.get("custom_name", "").strip()
            description = request.POST.get("description", "").strip()
            is_active = request.POST.get("is_active") == "on"

            if not name:
                messages.error(request, "Debe seleccionar un tipo de rol.")
                return redirect("authx:admin_roles")

            # Determinar el nombre final del rol
            if name == "custom":
                if not custom_name:
                    messages.error(request, "El nombre personalizado del rol es obligatorio.")
                    return redirect("authx:admin_roles")
                final_name = custom_name
            else:
                final_name = name

            # Verificar si el rol ya existe
            if Role.objects.filter(name__iexact=final_name).exists():
                messages.error(request, f'Ya existe un rol con el nombre "{final_name}".')
                return redirect("authx:admin_roles")

            try:
                Role.objects.create(name=final_name, description=description, is_active=is_active)
                messages.success(request, f'Rol "{final_name}" creado exitosamente.')
            except Exception as e:
                messages.error(request, f"Error al crear el rol: {str(e)}")

        elif action == "create_suggested_role":
            role_name = request.POST.get("role_name", "").strip()

            # Definir roles sugeridos con sus descripciones
            suggested_roles = {
                "Administrador": "Acceso completo al sistema",
                "Staff": "Gestión de productos y pedidos",
                "Cliente": "Acceso básico de compras",
            }

            if role_name not in suggested_roles:
                messages.error(request, "Rol sugerido no válido.")
                return redirect("authx:admin_roles")

            # Verificar si el rol ya existe
            if Role.objects.filter(name__iexact=role_name).exists():
                messages.error(request, f'Ya existe un rol con el nombre "{role_name}".')
                return redirect("authx:admin_roles")

            try:
                Role.objects.create(
                    name=role_name, description=suggested_roles[role_name], is_active=True
                )
                messages.success(request, f'Rol sugerido "{role_name}" creado exitosamente.')
            except Exception as e:
                messages.error(request, f"Error al crear el rol sugerido: {str(e)}")

        elif action == "edit_role":
            role_id = request.POST.get("role_id")
            name = request.POST.get("name", "").strip()
            custom_name = request.POST.get("custom_name", "").strip()
            description = request.POST.get("description", "").strip()
            is_active = request.POST.get("is_active") == "on"

            if not role_id:
                messages.error(request, "El ID del rol es obligatorio.")
                return redirect("authx:admin_roles")

            # Determinar el nombre final del rol
            if name == "custom":
                if not custom_name:
                    messages.error(request, "El nombre personalizado del rol es obligatorio.")
                    return redirect("authx:admin_roles")
                final_name = custom_name
            else:
                final_name = name

            try:
                role = Role.objects.get(id=role_id)

                # Verificar si el nombre ya existe en otro rol
                if Role.objects.filter(name__iexact=final_name).exclude(id=role_id).exists():
                    messages.error(request, f'Ya existe otro rol con el nombre "{final_name}".')
                    return redirect("authx:admin_roles")

                role.name = final_name
                role.description = description
                role.is_active = is_active
                role.save()

                messages.success(request, f'Rol "{final_name}" actualizado exitosamente.')
            except Role.DoesNotExist:
                messages.error(request, "El rol especificado no existe.")
            except Exception as e:
                messages.error(request, f"Error al actualizar el rol: {str(e)}")

        elif action == "delete_role":
            role_id = request.POST.get("role_id")

            if not role_id:
                messages.error(request, "ID del rol es obligatorio.")
                return redirect("authx:admin_roles")

            try:
                role = Role.objects.get(id=role_id)

                # Verificar si el rol tiene usuarios asignados
                if role.users.exists():
                    messages.error(
                        request,
                        f'No se puede eliminar el rol "{role.name}" porque tiene usuarios asignados.',
                    )
                    return redirect("authx:admin_roles")

                role_name = role.name
                role.delete()
                messages.success(request, f'Rol "{role_name}" eliminado exitosamente.')
            except Role.DoesNotExist:
                messages.error(request, "El rol especificado no existe.")
            except Exception as e:
                messages.error(request, f"Error al eliminar el rol: {str(e)}")

        return redirect("authx:admin_roles")


# Vistas para acciones de usuarios
@method_decorator(csrf_exempt, name="dispatch")
class UserToggleStatusView(AdminRequiredMixin, TemplateView):
    """Vista para activar/desactivar usuarios."""

    def post(self, request: HttpRequest, user_id: int) -> JsonResponse:
        from ctrlstore.apps.authx.models import User

        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()

        return JsonResponse(
            {
                "success": True,
                "is_active": user.is_active,
                "message": f'Usuario {"activado" if user.is_active else "desactivado"} correctamente',
            }
        )


class UserDetailView(AdminRequiredMixin, TemplateView):
    """Vista para ver detalles de usuario."""

    template_name = "authx/admin/user_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        from ctrlstore.apps.authx.models import User

        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)

        context.update(
            {
                "user_detail": user,
            }
        )

        return context


class UserEditView(AdminRequiredMixin, FormView):
    """Vista para editar usuario."""

    template_name = "authx/admin/user_edit.html"
    form_class = UserEditForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_id = self.kwargs.get("user_id")
        from ctrlstore.apps.authx.models import User

        self.user = get_object_or_404(User, id=user_id)
        kwargs["instance"] = self.user
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["user_detail"] = self.user
        return context

    def form_valid(self, form):
        form.save()
        return redirect("authx:admin_users")


# Vistas para gestión de productos
class AdminProductsView(AdminRequiredMixin, TemplateView):
    """Vista principal para gestión de productos."""

    template_name = "authx/admin/products.html"

    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator

        from ctrlstore.apps.catalog.models import Category, Product

        context = super().get_context_data(**kwargs)

        # Filtros
        search = self.request.GET.get("search", "")
        category_filter = self.request.GET.get("category", "")
        status_filter = self.request.GET.get("status", "")

        # Consulta base
        products = Product.objects.select_related("category").prefetch_related("specifications")

        # Aplicar filtros
        if search:
            products = products.filter(
                Q(name__icontains=search)
                | Q(specifications__brand__icontains=search)
                | Q(specifications__model__icontains=search)
            )

        if category_filter:
            products = products.filter(category_id=category_filter)

        if status_filter == "active":
            products = products.filter(is_active=True)
        elif status_filter == "inactive":
            products = products.filter(is_active=False)
        elif status_filter == "featured":
            products = products.filter(is_featured=True)
        elif status_filter == "out_of_stock":
            products = products.filter(stock_quantity=0)

        # Paginación
        paginator = Paginator(products, 20)
        page = self.request.GET.get("page")
        products_page = paginator.get_page(page)

        context.update(
            {
                "products": products_page,
                "categories": Category.objects.filter(parent__isnull=False),  # Solo subcategorías
                "search": search,
                "category_filter": category_filter,
                "status_filter": status_filter,
                "total_products": Product.objects.count(),
                "active_products": Product.objects.filter(is_active=True).count(),
                "featured_products": Product.objects.filter(is_featured=True).count(),
                "out_of_stock": Product.objects.filter(stock_quantity=0).count(),
            }
        )

        return context


class AdminProductCreateView(AdminRequiredMixin, TemplateView):
    """Vista para crear productos."""

    template_name = "authx/admin/product_form.html"

    def get_context_data(self, **kwargs):
        from ctrlstore.apps.catalog.models import Category

        context = super().get_context_data(**kwargs)

        # Obtener todas las categorías disponibles
        all_categories = Category.objects.all()
        subcategories = Category.objects.filter(parent__isnull=False)

        # Si no hay subcategorías, mostrar todas las categorías
        categories_to_show = subcategories if subcategories.exists() else all_categories

        context.update(
            {"categories": categories_to_show, "action": "create", "title": "Agregar Producto"}
        )
        return context

    def post(self, request):
        from django.contrib import messages
        from django.utils.text import slugify

        from ctrlstore.apps.catalog.models import (Category, Product,
                                                   ProductSpecification)

        try:
            # Validar datos obligatorios
            name = request.POST.get("name", "").strip()
            category_id = request.POST.get("category")
            price_str = request.POST.get("price", "").strip()

            if not name or not category_id or not price_str:
                messages.error(request, "Nombre, categoría y precio son obligatorios.")
                return redirect("authx:admin_product_create")

            try:
                price = float(price_str.replace(",", "."))  # Permitir comas como separador decimal
                if price <= 0:
                    raise ValueError("El precio debe ser mayor a 0")
            except (ValueError, TypeError):
                messages.error(
                    request,
                    f'El precio "{price_str}" no es válido. Use un número mayor a 0 (ej: 100.00).',
                )
                return redirect("authx:admin_product_create")

            try:
                stock_quantity = int(request.POST.get("stock_quantity", 0))
                if stock_quantity < 0:
                    stock_quantity = 0
            except (ValueError, TypeError):
                stock_quantity = 0

            category = Category.objects.get(id=category_id)

            # Crear producto
            product = Product.objects.create(
                name=name,
                slug=slugify(name),
                category=category,
                price=price,
                description=request.POST.get("description", ""),
                short_description=request.POST.get("short_description", ""),
                stock_quantity=stock_quantity,
                is_featured=request.POST.get("is_featured") == "on",
            )

            # Crear especificaciones
            specs_data = {}

            # Campos de texto
            text_fields = [
                "brand",
                "model",
                "operating_system",
                "screen_resolution",
                "ram_memory",
                "internal_storage",
                "main_camera",
                "front_camera",
                "battery_capacity",
                "connectivity",
                "processor",
                "graphics_card",
                "storage_type",
                "storage_capacity",
                "socket_type",
                "power_consumption",
                "frequency",
                "memory_type",
                "display_technology",
                "refresh_rate",
                "audio_power",
                "channels",
                "platform_compatibility",
                "genre",
                "age_rating",
            ]

            for field in text_fields:
                value = request.POST.get(field, "").strip()
                if value:
                    specs_data[field] = value

            # Campos decimales especiales
            screen_size_str = request.POST.get("screen_size", "").strip()
            if screen_size_str:
                try:
                    specs_data["screen_size"] = float(screen_size_str.replace(",", "."))
                except (ValueError, TypeError):
                    pass  # Ignorar si no es válido

            weight_str = request.POST.get("weight", "").strip()
            if weight_str:
                try:
                    specs_data["weight"] = float(weight_str.replace(",", "."))
                except (ValueError, TypeError):
                    pass  # Ignorar si no es válido

            # Campo booleano
            specs_data["multiplayer"] = request.POST.get("multiplayer") == "on"

            ProductSpecification.objects.create(product=product, **specs_data)

            messages.success(request, f'Producto "{name}" creado exitosamente.')
            return redirect("authx:admin_products")

        except Exception as e:
            messages.error(request, f"Error al crear el producto: {str(e)}")
            return redirect("authx:admin_product_create")


class AdminProductEditView(AdminRequiredMixin, TemplateView):
    template_name = "authx/admin/product_form.html"

    def get_context_data(self, **kwargs):
        from django.shortcuts import get_object_or_404

        from ctrlstore.apps.catalog.models import Category, Product

        context = super().get_context_data(**kwargs)
        product_id = kwargs.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        all_categories = Category.objects.all()
        subcategories = Category.objects.filter(parent__isnull=False)
        categories_to_show = subcategories if subcategories.exists() else all_categories

        context.update(
            {
                "product": product,
                "categories": categories_to_show,
                "action": "edit",
                "title": f"Editar Producto: {product.name}",
            }
        )
        return context

    def post(self, request, product_id):
        from django.contrib import messages
        from django.core.files.uploadedfile import UploadedFile
        from django.shortcuts import get_object_or_404, redirect
        from django.utils.text import slugify

        from ctrlstore.apps.catalog.models import Product, ProductSpecification

        product = get_object_or_404(Product, id=product_id)

        try:
            name = (request.POST.get("name") or "").strip()
            category_id = request.POST.get("category")
            price_str = (request.POST.get("price") or "").strip()

            if not name or not category_id or not price_str:
                messages.error(request, "Nombre, categoría y precio son obligatorios.")
                return redirect("authx:admin_product_edit", product_id=product_id)

            try:
                price = float(price_str.replace(",", "."))
                if price <= 0:
                    raise ValueError
            except Exception:
                messages.error(
                    request,
                    f'El precio "{price_str}" no es válido. Use un número mayor a 0 (ej: 100.00).',
                )
                return redirect("authx:admin_product_edit", product_id=product_id)

            try:
                stock_quantity = int(request.POST.get("stock_quantity") or 0)
                if stock_quantity < 0:
                    stock_quantity = 0
            except Exception:
                stock_quantity = 0

            # --- Actualizar datos básicos ---
            product.name = name
            product.category_id = category_id
            product.price = price
            product.description = request.POST.get("description") or ""
            product.short_description = request.POST.get("short_description") or ""
            product.stock_quantity = stock_quantity
            product.is_featured = request.POST.get("is_featured") == "on"
            product.is_active = request.POST.get("is_active") == "on"
            product.slug = slugify(product.name)

            # --- Imagen principal (NUEVO) ---
            file = request.FILES.get("main_image")
            if request.POST.get("remove_main_image") == "on":
                if product.main_image:
                    product.main_image.delete(save=False)
                product.main_image = None
            elif isinstance(file, UploadedFile):
                product.main_image.save(file.name, file, save=False)

            product.save()

            # --- Especificaciones ---
            specs, _ = ProductSpecification.objects.get_or_create(product=product)
            text_fields = [
                "brand",
                "model",
                "operating_system",
                "screen_resolution",
                "ram_memory",
                "internal_storage",
                "main_camera",
                "front_camera",
                "battery_capacity",
                "connectivity",
                "processor",
                "graphics_card",
                "storage_type",
                "storage_capacity",
                "socket_type",
                "power_consumption",
                "frequency",
                "memory_type",
                "display_technology",
                "refresh_rate",
                "audio_power",
                "channels",
                "platform_compatibility",
                "genre",
                "age_rating",
            ]
            for field in text_fields:
                if field in request.POST:
                    setattr(specs, field, (request.POST.get(field) or "").strip())

            if request.POST.get("screen_size"):
                try:
                    specs.screen_size = float(request.POST["screen_size"].replace(",", "."))
                except Exception:
                    pass
            if request.POST.get("weight"):
                try:
                    specs.weight = float(request.POST["weight"].replace(",", "."))
                except Exception:
                    pass

            specs.multiplayer = request.POST.get("multiplayer") == "on"
            specs.save()

            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            return redirect("authx:admin_products")

        except Exception as e:
            messages.error(request, f"Error al actualizar el producto: {e}")
            return redirect("authx:admin_product_edit", product_id=product_id)


class AdminProductDeleteView(AdminRequiredMixin, TemplateView):
    """Vista para eliminar productos."""

    def post(self, request, product_id):
        from django.contrib import messages

        from ctrlstore.apps.catalog.models import Product

        product = get_object_or_404(Product, id=product_id)
        product_name = product.name

        try:
            product.delete()
            messages.success(request, f'Producto "{product_name}" eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f"Error al eliminar el producto: {str(e)}")

        return redirect("authx:admin_products")


class AdminCategoriesView(AdminRequiredMixin, TemplateView):
    """Vista para gestión de categorías."""

    template_name = "authx/admin/categories.html"

    def get_context_data(self, **kwargs):
        from ctrlstore.apps.catalog.models import Category

        context = super().get_context_data(**kwargs)

        # Obtener todas las categorías sin intentar crear nuevas
        all_categories = Category.objects.all().prefetch_related("products")
        main_categories = Category.objects.filter(parent__isnull=True).prefetch_related(
            "subcategories__products"
        )

        # Estadísticas
        total_categories = all_categories.count()
        active_categories = all_categories.filter(is_active=True).count()

        context.update(
            {
                "categories": all_categories,
                "main_categories": main_categories,
                "total_categories": total_categories,
                "active_categories": active_categories,
            }
        )

        return context


# Vistas específicas para Staff (sin acceso a gestión de usuarios)
class StaffDashboardView(StaffAdminMixin, TemplateView):
    """Dashboard para usuarios Staff (sin gestión de usuarios)."""

    template_name = "authx/admin/staff_dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Estadísticas básicas para el dashboard de Staff
        from ctrlstore.apps.catalog.models import Category, Product

        context.update(
            {
                "total_products": Product.objects.count(),
                "total_categories": Category.objects.count(),
                "gaming_products": Product.objects.filter(category__category_type="gaming").count(),
                "recent_products": Product.objects.select_related("category").order_by(
                    "-created_at"
                )[:5],
            }
        )

        return context


class StaffProductsView(StaffAdminMixin, TemplateView):
    """Vista para gestión de productos para Staff."""

    template_name = "authx/admin/staff_products.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        from django.core.paginator import Paginator
        from django.db.models import Q

        from ctrlstore.apps.catalog.models import Category, Product

        context = super().get_context_data(**kwargs)

        # Filtros
        search = self.request.GET.get("search", "")
        category_filter = self.request.GET.get("category", "")
        status_filter = self.request.GET.get("status", "")

        # Consulta base
        products = Product.objects.select_related("category").prefetch_related("specifications")

        # Aplicar filtros
        if search:
            products = products.filter(
                Q(name__icontains=search)
                | Q(specifications__brand__icontains=search)
                | Q(specifications__model__icontains=search)
            )

        if category_filter:
            products = products.filter(category_id=category_filter)

        if status_filter == "active":
            products = products.filter(is_active=True)
        elif status_filter == "inactive":
            products = products.filter(is_active=False)
        elif status_filter == "featured":
            products = products.filter(is_featured=True)
        elif status_filter == "out_of_stock":
            products = products.filter(stock_quantity=0)

        # Paginación
        paginator = Paginator(products, 20)
        page = self.request.GET.get("page")
        products_page = paginator.get_page(page)

        context.update(
            {
                "products": products_page,
                "categories": Category.objects.filter(parent__isnull=False),  # Solo subcategorías
                "search": search,
                "category_filter": category_filter,
                "status_filter": status_filter,
                "total_products": Product.objects.count(),
                "active_products": Product.objects.filter(is_active=True).count(),
                "featured_products": Product.objects.filter(is_featured=True).count(),
                "out_of_stock": Product.objects.filter(stock_quantity=0).count(),
            }
        )

        return context

    
def _parse_dates(request):
    """
    Lee ?start=YYYY-MM-DD&end=YYYY-MM-DD. Si no vienen, últimos 30 días.
    Devuelve dos datetimes (timezone-aware) [start, end+1d).
    """
    tz = timezone.get_current_timezone()
    today = timezone.localdate()
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")

    if start_str and end_str:
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            start_date = today - timedelta(days=30)
            end_date = today
    else:
        start_date = today - timedelta(days=30)
        end_date = today

    start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()), tz)
    end_dt = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), datetime.min.time()), tz)
    return start_dt, end_dt, start_date, end_date


class AdminSalesHistoryView(AdminRequiredMixin, TemplateView):
    """
    Tabla de órdenes pagadas con filtros por rango de fechas + export CSV.
    """
    template_name = "authx/admin/sales-history.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        Order = apps.get_model("order", "Order")

        start_dt, end_dt, start_date, end_date = _parse_dates(self.request)

        qs = (
            Order.objects
            .filter(status="paid", created_at__gte=start_dt, created_at__lt=end_dt)
            .select_related("user")
            .prefetch_related("items__product", "payments")
            .order_by("-created_at")
        )

        # Paginación
        paginator = Paginator(qs, 25)
        page = self.request.GET.get("page")
        orders_page = paginator.get_page(page)

        # KPIs rápidos
        total_orders = qs.count()
        total_revenue = qs.aggregate(s=Sum("total_amount"))["s"] or Decimal("0.00")
        avg_ticket = (total_revenue / total_orders) if total_orders else Decimal("0.00")

        context.update({
            "orders": orders_page,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "avg_ticket": avg_ticket,
            "start_date": start_date,
            "end_date": end_date,
        })
        return context


class AdminSalesReportView(AdminRequiredMixin, TemplateView):
    """
    Reporte agregado: ingresos, #órdenes, ticket promedio, top productos/categorías y serie por día.
    """
    template_name = "authx/admin/sales-report.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        Order = apps.get_model("order", "Order")
        OrderItem = apps.get_model("order", "OrderItem")
        Category = apps.get_model("catalog", "Category")

        start_dt, end_dt, start_date, end_date = _parse_dates(self.request)

        paid_orders = (
            Order.objects.filter(status="paid", created_at__gte=start_dt, created_at__lt=end_dt)
        )

        revenue = paid_orders.aggregate(s=Sum("total_amount"))["s"] or Decimal("0.00")
        orders_count = paid_orders.count()
        avg_ticket = (revenue / orders_count) if orders_count else Decimal("0.00")

        # Top productos (por unidades)
        top_products = (
            OrderItem.objects
            .filter(order__in=paid_orders)
            .values("product", "product__name")
            .annotate(units=Sum("quantity"), income=Sum(F("unit_price") * F("quantity")))
            .order_by("-units")[:10]
        )

        # Top categorías (si tu OrderItem -> product -> category)
        top_categories = (
            OrderItem.objects
            .filter(order__in=paid_orders)
            .values("product__category__id", "product__category__name")
            .annotate(units=Sum("quantity"), income=Sum(F("unit_price") * F("quantity")))
            .order_by("-income")[:10]
        )

        # Serie diaria (ingresos por día)
        # Nota: para SQLite usamos date() sobre created_at; en Postgres podrías usar TruncDate.
        daily = (
            paid_orders.extra(select={"d": "date(created_at)"})
            .values("d")
            .annotate(income=Sum("total_amount"), orders=Count("id"))
            .order_by("d")
        )

        context.update({
            "start_date": start_date,
            "end_date": end_date,
            "revenue": revenue,
            "orders_count": orders_count,
            "avg_ticket": avg_ticket,
            "top_products": top_products,
            "top_categories": top_categories,
            "daily": daily,
        })
        return context


class AdminSalesExportCSVView(AdminRequiredMixin, View):
    """
    Exportación CSV del historial filtrado.
    """
    def get(self, request, *args, **kwargs):
        Order = apps.get_model("order", "Order")
        start_dt, end_dt, *_ = _parse_dates(request)
        qs = (
            Order.objects
            .filter(status="paid", created_at__gte=start_dt, created_at__lt=end_dt)
            .select_related("user")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

        import csv
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="ventas.csv"'
        writer = csv.writer(resp)
        writer.writerow(["order_id", "fecha", "usuario", "email", "total", "items"])

        for o in qs:
            items_str = "; ".join(f"{it.product.name} x{it.quantity}" for it in o.items.all())
            writer.writerow([
                o.id,
                timezone.localtime(o.created_at).strftime("%Y-%m-%d %H:%M"),
                (o.user.get_full_name() or o.user.username) if o.user_id else "",
                o.user.email if o.user_id else "",
                str(o.total_amount),
                items_str,
            ])
        return resp



class StaffProductCreateView(StaffAdminMixin, TemplateView):
    """Vista para crear productos para Staff."""

    template_name = "authx/admin/staff_product_form.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        from ctrlstore.apps.catalog.models import Category

        context = super().get_context_data(**kwargs)

        # Obtener todas las categorías disponibles
        all_categories = Category.objects.all()
        subcategories = Category.objects.filter(parent__isnull=False)

        # Si no hay subcategorías, mostrar todas las categorías
        categories_to_show = subcategories if subcategories.exists() else all_categories

        context.update(
            {"categories": categories_to_show, "action": "create", "title": "Agregar Producto"}
        )
        return context

    def post(self, request: HttpRequest) -> HttpResponse:
        from django.contrib import messages
        from django.utils.text import slugify

        from ctrlstore.apps.catalog.models import (Category, Product,
                                                   ProductSpecification)

        try:
            # Validar datos obligatorios
            name = request.POST.get("name", "").strip()
            category_id = request.POST.get("category")
            price_str = request.POST.get("price", "").strip()

            if not name or not category_id or not price_str:
                messages.error(request, "Nombre, categoría y precio son obligatorios.")
                return redirect("authx:staff_product_create")

            try:
                price = float(price_str.replace(",", "."))  # Permitir comas como separador decimal
                if price <= 0:
                    raise ValueError("El precio debe ser mayor a 0")
            except (ValueError, TypeError):
                messages.error(
                    request,
                    f'El precio "{price_str}" no es válido. Use un número mayor a 0 (ej: 100.00).',
                )
                return redirect("authx:staff_product_create")

            try:
                stock_quantity = int(request.POST.get("stock_quantity", 0))
                if stock_quantity < 0:
                    stock_quantity = 0
            except (ValueError, TypeError):
                stock_quantity = 0

            category = Category.objects.get(id=category_id)

            # Crear producto
            product = Product.objects.create(
                name=name,
                slug=slugify(name),
                category=category,
                price=price,
                description=request.POST.get("description", ""),
                short_description=request.POST.get("short_description", ""),
                stock_quantity=stock_quantity,
                is_featured=request.POST.get("is_featured") == "on",
            )

            # Crear especificaciones
            specs_data = {}

            # Campos de texto
            text_fields = [
                "brand",
                "model",
                "operating_system",
                "screen_resolution",
                "ram_memory",
                "internal_storage",
                "main_camera",
                "front_camera",
                "battery_capacity",
                "connectivity",
                "processor",
                "graphics_card",
                "storage_type",
                "storage_capacity",
                "socket_type",
                "power_consumption",
                "frequency",
                "memory_type",
                "display_technology",
                "refresh_rate",
                "audio_power",
                "channels",
                "platform_compatibility",
                "genre",
                "age_rating",
            ]

            for field in text_fields:
                value = request.POST.get(field, "").strip()
                if value:
                    specs_data[field] = value

            # Campos decimales especiales
            screen_size_str = request.POST.get("screen_size", "").strip()
            if screen_size_str:
                try:
                    specs_data["screen_size"] = float(screen_size_str.replace(",", "."))
                except (ValueError, TypeError):
                    pass  # Ignorar si no es válido

            weight_str = request.POST.get("weight", "").strip()
            if weight_str:
                try:
                    specs_data["weight"] = float(weight_str.replace(",", "."))
                except (ValueError, TypeError):
                    pass  # Ignorar si no es válido

            # Campo booleano
            specs_data["multiplayer"] = request.POST.get("multiplayer") == "on"

            ProductSpecification.objects.create(product=product, **specs_data)

            messages.success(request, f'Producto "{name}" creado exitosamente.')
            return redirect("authx:staff_products")

        except Exception as e:
            messages.error(request, f"Error al crear el producto: {str(e)}")
            return redirect("authx:staff_product_create")


class StaffProductEditView(StaffAdminMixin, TemplateView):
    """Vista para editar productos para Staff."""

    template_name = "authx/admin/staff_product_form.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        from ctrlstore.apps.catalog.models import Category, Product

        context = super().get_context_data(**kwargs)
        product_id = kwargs.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        # Obtener categorías disponibles
        all_categories = Category.objects.all()
        subcategories = Category.objects.filter(parent__isnull=False)
        categories_to_show = subcategories if subcategories.exists() else all_categories

        context.update(
            {
                "product": product,
                "categories": categories_to_show,
                "action": "edit",
                "title": f"Editar Producto: {product.name}",
            }
        )
        return context

    def post(self, request: HttpRequest, product_id: int) -> HttpResponse:
        from django.contrib import messages
        from django.utils.text import slugify

        from ctrlstore.apps.catalog.models import (Category, Product,
                                                   ProductSpecification)

        product = get_object_or_404(Product, id=product_id)

        try:
            # Validar datos obligatorios
            name = request.POST.get("name", "").strip()
            category_id = request.POST.get("category")
            price_str = request.POST.get("price", "").strip()

            if not name or not category_id or not price_str:
                messages.error(request, "Nombre, categoría y precio son obligatorios.")
                return redirect("authx:staff_product_edit", product_id=product_id)

            try:
                price = float(price_str.replace(",", "."))  # Permitir comas como separador decimal
                if price <= 0:
                    raise ValueError("El precio debe ser mayor a 0")
            except (ValueError, TypeError):
                messages.error(
                    request,
                    f'El precio "{price_str}" no es válido. Use un número mayor a 0 (ej: 100.00).',
                )
                return redirect("authx:staff_product_edit", product_id=product_id)

            try:
                stock_quantity = int(request.POST.get("stock_quantity", 0))
                if stock_quantity < 0:
                    stock_quantity = 0
            except (ValueError, TypeError):
                stock_quantity = 0

            # Actualizar datos básicos
            product.name = name
            product.category_id = category_id
            product.price = price
            product.description = request.POST.get("description", "")
            product.short_description = request.POST.get("short_description", "")
            product.stock_quantity = stock_quantity
            product.is_featured = request.POST.get("is_featured") == "on"
            product.is_active = request.POST.get("is_active") == "on"
            product.slug = slugify(product.name)
            product.save()

            # Actualizar especificaciones
            specs, created = ProductSpecification.objects.get_or_create(product=product)

            # Campos de texto normales - solo actualizar si existen en el POST
            text_fields = [
                "brand",
                "model",
                "operating_system",
                "screen_resolution",
                "ram_memory",
                "internal_storage",
                "main_camera",
                "front_camera",
                "battery_capacity",
                "connectivity",
                "processor",
                "graphics_card",
                "storage_type",
                "storage_capacity",
                "socket_type",
                "power_consumption",
                "frequency",
                "memory_type",
                "display_technology",
                "refresh_rate",
                "audio_power",
                "channels",
                "platform_compatibility",
                "genre",
                "age_rating",
            ]

            for field in text_fields:
                if field in request.POST:  # Solo actualizar si el campo existe en el formulario
                    value = request.POST.get(field, "").strip()
                    setattr(specs, field, value)

            # Campos decimales especiales - solo actualizar si tienen valor
            if "screen_size" in request.POST and request.POST.get("screen_size", "").strip():
                try:
                    screen_size_value = float(request.POST.get("screen_size").replace(",", "."))
                    specs.screen_size = screen_size_value
                except (ValueError, TypeError):
                    pass  # Mantener valor anterior si hay error

            if "weight" in request.POST and request.POST.get("weight", "").strip():
                try:
                    weight_value = float(request.POST.get("weight").replace(",", "."))
                    specs.weight = weight_value
                except (ValueError, TypeError):
                    pass  # Mantener valor anterior si hay error

            # Campo booleano
            specs.multiplayer = request.POST.get("multiplayer") == "on"
            specs.save()

            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            return redirect("authx:staff_products")

        except Exception as e:
            messages.error(request, f"Error al actualizar el producto: {str(e)}")
            return redirect("authx:staff_product_edit", product_id=product_id)


class StaffProductDeleteView(StaffAdminMixin, TemplateView):
    """Vista para eliminar productos para Staff."""

    def post(self, request: HttpRequest, product_id: int) -> HttpResponse:
        from django.contrib import messages

        from ctrlstore.apps.catalog.models import Product

        product = get_object_or_404(Product, id=product_id)
        product_name = product.name

        try:
            product.delete()
            messages.success(request, f'Producto "{product_name}" eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f"Error al eliminar el producto: {str(e)}")

        return redirect("authx:staff_products")


class StaffCategoriesView(StaffAdminMixin, TemplateView):
    """Vista para gestión de categorías para Staff."""

    template_name = "authx/admin/staff_categories.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        from ctrlstore.apps.catalog.models import Category

        context = super().get_context_data(**kwargs)

        # Obtener todas las categorías sin intentar crear nuevas
        all_categories = Category.objects.all().prefetch_related("products")
        main_categories = Category.objects.filter(parent__isnull=True).prefetch_related(
            "subcategories__products"
        )

        # Estadísticas
        total_categories = all_categories.count()
        active_categories = all_categories.filter(is_active=True).count()

        context.update(
            {
                "categories": all_categories,
                "main_categories": main_categories,
                "total_categories": total_categories,
                "active_categories": active_categories,
            }
        )

        return context
