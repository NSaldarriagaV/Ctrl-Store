from __future__ import annotations

from typing import Any

from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

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
            "gaming_products": Product.objects.filter(category__category_type='gaming').count(),
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


# Vistas para gestión de productos
class AdminProductsView(AdminRequiredMixin, TemplateView):
    """Vista principal para gestión de productos."""
    template_name = "authx/admin/products.html"
    
    def get_context_data(self, **kwargs):
        from ctrlstore.apps.catalog.models import Product, Category
        from django.core.paginator import Paginator
        
        context = super().get_context_data(**kwargs)
        
        # Filtros
        search = self.request.GET.get('search', '')
        category_filter = self.request.GET.get('category', '')
        status_filter = self.request.GET.get('status', '')
        
        # Consulta base
        products = Product.objects.select_related('category').prefetch_related('specifications')
        
        # Aplicar filtros
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(specifications__brand__icontains=search) |
                Q(specifications__model__icontains=search)
            )
        
        if category_filter:
            products = products.filter(category_id=category_filter)
            
        if status_filter == 'active':
            products = products.filter(is_active=True)
        elif status_filter == 'inactive':
            products = products.filter(is_active=False)
        elif status_filter == 'featured':
            products = products.filter(is_featured=True)
        elif status_filter == 'out_of_stock':
            products = products.filter(stock_quantity=0)
        
        # Paginación
        paginator = Paginator(products, 20)
        page = self.request.GET.get('page')
        products_page = paginator.get_page(page)
        
        context.update({
            'products': products_page,
            'categories': Category.objects.filter(parent__isnull=False),  # Solo subcategorías
            'search': search,
            'category_filter': category_filter,
            'status_filter': status_filter,
            'total_products': Product.objects.count(),
            'active_products': Product.objects.filter(is_active=True).count(),
            'featured_products': Product.objects.filter(is_featured=True).count(),
            'out_of_stock': Product.objects.filter(stock_quantity=0).count(),
        })
        
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
        
        context.update({
            'categories': categories_to_show,
            'action': 'create',
            'title': 'Agregar Producto'
        })
        return context
    
    def post(self, request):
        from ctrlstore.apps.catalog.models import Product, ProductSpecification, Category
        from django.utils.text import slugify
        from django.contrib import messages
        
        try:
            # Validar datos obligatorios
            name = request.POST.get('name', '').strip()
            category_id = request.POST.get('category')
            price_str = request.POST.get('price', '').strip()
            
            if not name or not category_id or not price_str:
                messages.error(request, 'Nombre, categoría y precio son obligatorios.')
                return redirect('authx:admin_product_create')
            
            try:
                price = float(price_str.replace(',', '.'))  # Permitir comas como separador decimal
                if price <= 0:
                    raise ValueError("El precio debe ser mayor a 0")
            except (ValueError, TypeError):
                messages.error(request, f'El precio "{price_str}" no es válido. Use un número mayor a 0 (ej: 100.00).')
                return redirect('authx:admin_product_create')
            
            try:
                stock_quantity = int(request.POST.get('stock_quantity', 0))
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
                description=request.POST.get('description', ''),
                short_description=request.POST.get('short_description', ''),
                stock_quantity=stock_quantity,
                is_featured=request.POST.get('is_featured') == 'on'
            )
            
            # Crear especificaciones
            specs_data = {}
            
            # Campos de texto
            text_fields = [
                'brand', 'model', 'operating_system', 'screen_resolution',
                'ram_memory', 'internal_storage', 'main_camera', 'front_camera',
                'battery_capacity', 'connectivity', 'processor', 'graphics_card',
                'storage_type', 'storage_capacity', 'socket_type',
                'power_consumption', 'frequency', 'memory_type', 'display_technology',
                'refresh_rate', 'audio_power', 'channels', 'platform_compatibility',
                'genre', 'age_rating'
            ]
            
            for field in text_fields:
                value = request.POST.get(field, '').strip()
                if value:
                    specs_data[field] = value
            
            # Campos decimales especiales
            screen_size_str = request.POST.get('screen_size', '').strip()
            if screen_size_str:
                try:
                    specs_data['screen_size'] = float(screen_size_str.replace(',', '.'))
                except (ValueError, TypeError):
                    pass  # Ignorar si no es válido
                    
            weight_str = request.POST.get('weight', '').strip()
            if weight_str:
                try:
                    specs_data['weight'] = float(weight_str.replace(',', '.'))
                except (ValueError, TypeError):
                    pass  # Ignorar si no es válido
            
            # Campo booleano
            specs_data['multiplayer'] = request.POST.get('multiplayer') == 'on'
            
            ProductSpecification.objects.create(product=product, **specs_data)
            
            messages.success(request, f'Producto "{name}" creado exitosamente.')
            return redirect('authx:admin_products')
            
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {str(e)}')
            return redirect('authx:admin_product_create')


class AdminProductEditView(AdminRequiredMixin, TemplateView):
    template_name = "authx/admin/product_form.html"

    def get_context_data(self, **kwargs):
        from ctrlstore.apps.catalog.models import Product, Category
        from django.shortcuts import get_object_or_404

        context = super().get_context_data(**kwargs)
        product_id = kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        all_categories = Category.objects.all()
        subcategories = Category.objects.filter(parent__isnull=False)
        categories_to_show = subcategories if subcategories.exists() else all_categories

        context.update({
            'product': product,
            'categories': categories_to_show,
            'action': 'edit',
            'title': f'Editar Producto: {product.name}'
        })
        return context

    def post(self, request, product_id):
        from ctrlstore.apps.catalog.models import Product, ProductSpecification
        from django.shortcuts import get_object_or_404, redirect
        from django.utils.text import slugify
        from django.contrib import messages
        from django.core.files.uploadedfile import UploadedFile

        product = get_object_or_404(Product, id=product_id)

        try:
            name = (request.POST.get('name') or '').strip()
            category_id = request.POST.get('category')
            price_str = (request.POST.get('price') or '').strip()

            if not name or not category_id or not price_str:
                messages.error(request, 'Nombre, categoría y precio son obligatorios.')
                return redirect('authx:admin_product_edit', product_id=product_id)

            try:
                price = float(price_str.replace(',', '.'))
                if price <= 0:
                    raise ValueError
            except Exception:
                messages.error(request, f'El precio "{price_str}" no es válido. Use un número mayor a 0 (ej: 100.00).')
                return redirect('authx:admin_product_edit', product_id=product_id)

            try:
                stock_quantity = int(request.POST.get('stock_quantity') or 0)
                if stock_quantity < 0:
                    stock_quantity = 0
            except Exception:
                stock_quantity = 0

            # --- Actualizar datos básicos ---
            product.name = name
            product.category_id = category_id
            product.price = price
            product.description = request.POST.get('description') or ''
            product.short_description = request.POST.get('short_description') or ''
            product.stock_quantity = stock_quantity
            product.is_featured = request.POST.get('is_featured') == 'on'
            product.is_active = request.POST.get('is_active') == 'on'
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
                'brand', 'model', 'operating_system', 'screen_resolution',
                'ram_memory', 'internal_storage', 'main_camera', 'front_camera',
                'battery_capacity', 'connectivity', 'processor', 'graphics_card',
                'storage_type', 'storage_capacity', 'socket_type',
                'power_consumption', 'frequency', 'memory_type', 'display_technology',
                'refresh_rate', 'audio_power', 'channels', 'platform_compatibility',
                'genre', 'age_rating'
            ]
            for field in text_fields:
                if field in request.POST:
                    setattr(specs, field, (request.POST.get(field) or '').strip())

            if request.POST.get('screen_size'):
                try:
                    specs.screen_size = float(request.POST['screen_size'].replace(',', '.'))
                except Exception:
                    pass
            if request.POST.get('weight'):
                try:
                    specs.weight = float(request.POST['weight'].replace(',', '.'))
                except Exception:
                    pass

            specs.multiplayer = request.POST.get('multiplayer') == 'on'
            specs.save()

            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            return redirect('authx:admin_products')

        except Exception as e:
            messages.error(request, f'Error al actualizar el producto: {e}')
            return redirect('authx:admin_product_edit', product_id=product_id)



class AdminProductDeleteView(AdminRequiredMixin, TemplateView):
    """Vista para eliminar productos."""
    
    def post(self, request, product_id):
        from ctrlstore.apps.catalog.models import Product
        from django.contrib import messages
        
        product = get_object_or_404(Product, id=product_id)
        product_name = product.name
        
        try:
            product.delete()
            messages.success(request, f'Producto "{product_name}" eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el producto: {str(e)}')
        
        return redirect('authx:admin_products')


class AdminCategoriesView(AdminRequiredMixin, TemplateView):
    """Vista para gestión de categorías."""
    template_name = "authx/admin/categories.html"
    
    def get_context_data(self, **kwargs):
        from ctrlstore.apps.catalog.models import Category
        
        context = super().get_context_data(**kwargs)
        
        # Obtener todas las categorías sin intentar crear nuevas
        all_categories = Category.objects.all().prefetch_related('products')
        main_categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories__products')
        
        # Estadísticas
        total_categories = all_categories.count()
        active_categories = all_categories.filter(is_active=True).count()
        
        context.update({
            'categories': all_categories,
            'main_categories': main_categories,
            'total_categories': total_categories,
            'active_categories': active_categories,
        })
        
        return context
    

