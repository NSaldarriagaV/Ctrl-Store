from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Product, Category

class ProductListView(ListView):
    model = Product
    paginate_by = 12
    template_name = "catalog/product-list.html"

    def get_queryset(self):
        qs = Product.objects.select_related("category").filter(is_active=True)
        cat = self.request.GET.get("cat")
        gaming = self.request.GET.get("gaming")
        if cat:
            qs = qs.filter(category__slug=cat)
        if gaming in {"true", "1"}:
            qs = qs.filter(category__category_type='gaming')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Obtener categorías organizadas jerárquicamente
        main_categories = Category.objects.filter(
            parent__isnull=True, 
            is_active=True
        ).prefetch_related('subcategories')
        
        ctx["main_categories"] = main_categories
        ctx["categories"] = Category.objects.filter(is_active=True)  # Para compatibilidad
        ctx["selected_cat"] = self.request.GET.get("cat", "")
        return ctx

class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product-detail.html"


# Vistas del Comparador
class CompareCategorySelectView(TemplateView):
    """Vista para seleccionar categoría antes de comparar productos"""
    template_name = "catalog/compare/category-select.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener categorías principales con sus subcategorías
        main_categories = Category.objects.filter(
            parent__isnull=True,
            is_active=True
        ).prefetch_related('subcategories').order_by('name')
        
        # Filtrar solo las categorías que tienen productos (principales o subcategorías)
        categories_with_products = []
        for main_cat in main_categories:
            # Verificar si la categoría principal tiene productos
            if main_cat.products.filter(is_active=True).exists():
                categories_with_products.append(main_cat)
            else:
                # Si no tiene productos directos, verificar subcategorías
                subcategories_with_products = main_cat.subcategories.filter(
                    is_active=True,
                    products__is_active=True
                ).distinct()
                if subcategories_with_products.exists():
                    # Crear una versión modificada de la categoría principal
                    main_cat.subcategories_with_products = subcategories_with_products
                    categories_with_products.append(main_cat)
        
        context['main_categories'] = categories_with_products
        return context


class CompareProductSelectView(TemplateView):
    """Vista para seleccionar productos de una categoría específica"""
    template_name = "catalog/compare/product-select.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = kwargs.get('category_id')
        
        category = get_object_or_404(Category, id=category_id, is_active=True)
        products = Product.objects.filter(
            category=category,
            is_active=True
        ).select_related('category', 'specifications').order_by('name')
        
        context['category'] = category
        context['products'] = products
        return context


class CompareProductsView(TemplateView):
    """Vista para comparar dos productos lado a lado"""
    template_name = "catalog/compare/compare-products.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product1_id = kwargs.get('product1_id')
        product2_id = kwargs.get('product2_id')
        
        product1 = get_object_or_404(Product, id=product1_id, is_active=True)
        product2 = get_object_or_404(Product, id=product2_id, is_active=True)
        
        # Verificar que ambos productos sean de la misma categoría
        if product1.category != product2.category:
            raise ValueError("Los productos deben ser de la misma categoría")
        
        # Obtener especificaciones completas
        specs1 = getattr(product1, 'specifications', None)
        specs2 = getattr(product2, 'specifications', None)
        
        # Generar comparación de especificaciones
        comparison_data = self._generate_comparison_data(product1, product2, specs1, specs2)
        
        context.update({
            'product1': product1,
            'product2': product2,
            'specs1': specs1,
            'specs2': specs2,
            'comparison_data': comparison_data,
            'category': product1.category,
        })
        return context
    
    def _generate_comparison_data(self, product1, product2, specs1, specs2):
        """Genera datos estructurados para la comparación"""
        comparison = []
        
        # Información básica
        comparison.append({
            'section': 'Información General',
            'fields': [
                {'name': 'Nombre', 'value1': product1.name, 'value2': product2.name},
                {'name': 'Precio', 'value1': f"${product1.price:,.0f}", 'value2': f"${product2.price:,.0f}"},
                {'name': 'Marca', 'value1': specs1.brand if specs1 else 'N/A', 'value2': specs2.brand if specs2 else 'N/A'},
                {'name': 'Modelo', 'value1': specs1.model if specs1 else 'N/A', 'value2': specs2.model if specs2 else 'N/A'},
            ]
        })
        
        if not specs1 or not specs2:
            return comparison
        
        # Especificaciones según el tipo de categoría
        category_type = product1.category.category_type
        
        if category_type == 'celulares_tablets':
            comparison.append({
                'section': 'Pantalla',
                'fields': [
                    {'name': 'Tamaño', 'value1': f"{specs1.screen_size}\"" if specs1.screen_size else 'N/A', 
                     'value2': f"{specs2.screen_size}\"" if specs2.screen_size else 'N/A'},
                    {'name': 'Resolución', 'value1': specs1.screen_resolution or 'N/A', 'value2': specs2.screen_resolution or 'N/A'},
                ]
            })
            comparison.append({
                'section': 'Rendimiento',
                'fields': [
                    {'name': 'Sistema Operativo', 'value1': specs1.operating_system or 'N/A', 'value2': specs2.operating_system or 'N/A'},
                    {'name': 'RAM', 'value1': specs1.ram_memory or 'N/A', 'value2': specs2.ram_memory or 'N/A'},
                    {'name': 'Almacenamiento', 'value1': specs1.internal_storage or 'N/A', 'value2': specs2.internal_storage or 'N/A'},
                ]
            })
            comparison.append({
                'section': 'Cámaras',
                'fields': [
                    {'name': 'Cámara Principal', 'value1': specs1.main_camera or 'N/A', 'value2': specs2.main_camera or 'N/A'},
                    {'name': 'Cámara Frontal', 'value1': specs1.front_camera or 'N/A', 'value2': specs2.front_camera or 'N/A'},
                ]
            })
            comparison.append({
                'section': 'Batería y Conectividad',
                'fields': [
                    {'name': 'Batería', 'value1': specs1.battery_capacity or 'N/A', 'value2': specs2.battery_capacity or 'N/A'},
                    {'name': 'Conectividad', 'value1': specs1.connectivity or 'N/A', 'value2': specs2.connectivity or 'N/A'},
                ]
            })
            
        elif category_type == 'computadores':
            comparison.append({
                'section': 'Procesador',
                'fields': [
                    {'name': 'CPU', 'value1': specs1.processor or 'N/A', 'value2': specs2.processor or 'N/A'},
                ]
            })
            comparison.append({
                'section': 'Memoria y Almacenamiento',
                'fields': [
                    {'name': 'RAM', 'value1': specs1.ram_memory or 'N/A', 'value2': specs2.ram_memory or 'N/A'},
                    {'name': 'Almacenamiento', 'value1': f"{specs1.storage_type} {specs1.storage_capacity}" if specs1.storage_type and specs1.storage_capacity else 'N/A', 
                     'value2': f"{specs2.storage_type} {specs2.storage_capacity}" if specs2.storage_type and specs2.storage_capacity else 'N/A'},
                ]
            })
            comparison.append({
                'section': 'Gráficos',
                'fields': [
                    {'name': 'Tarjeta Gráfica', 'value1': specs1.graphics_card or 'N/A', 'value2': specs2.graphics_card or 'N/A'},
                ]
            })
            comparison.append({
                'section': 'Físico',
                'fields': [
                    {'name': 'Peso', 'value1': f"{specs1.weight} kg" if specs1.weight else 'N/A', 'value2': f"{specs2.weight} kg" if specs2.weight else 'N/A'},
                ]
            })
            
        elif category_type == 'componentes':
            comparison.append({
                'section': 'Especificaciones Técnicas',
                'fields': [
                    {'name': 'Socket/Tipo', 'value1': specs1.socket_type or 'N/A', 'value2': specs2.socket_type or 'N/A'},
                    {'name': 'Frecuencia', 'value1': specs1.frequency or 'N/A', 'value2': specs2.frequency or 'N/A'},
                    {'name': 'Consumo Energético', 'value1': specs1.power_consumption or 'N/A', 'value2': specs2.power_consumption or 'N/A'},
                    {'name': 'Tipo de Memoria', 'value1': specs1.memory_type or 'N/A', 'value2': specs2.memory_type or 'N/A'},
                ]
            })
            
        elif category_type == 'audio_video':
            comparison.append({
                'section': 'Pantalla',
                'fields': [
                    {'name': 'Tamaño', 'value1': f"{specs1.screen_size}\"" if specs1.screen_size else 'N/A', 'value2': f"{specs2.screen_size}\"" if specs2.screen_size else 'N/A'},
                    {'name': 'Resolución', 'value1': specs1.screen_resolution or 'N/A', 'value2': specs2.screen_resolution or 'N/A'},
                    {'name': 'Tecnología', 'value1': specs1.display_technology or 'N/A', 'value2': specs2.display_technology or 'N/A'},
                    {'name': 'Frecuencia de Refresco', 'value1': specs1.refresh_rate or 'N/A', 'value2': specs2.refresh_rate or 'N/A'},
                ]
            })
            comparison.append({
                'section': 'Audio',
                'fields': [
                    {'name': 'Potencia', 'value1': specs1.audio_power or 'N/A', 'value2': specs2.audio_power or 'N/A'},
                    {'name': 'Canales', 'value1': specs1.channels or 'N/A', 'value2': specs2.channels or 'N/A'},
                ]
            })
            
        elif category_type == 'gaming':
            comparison.append({
                'section': 'Información del Juego',
                'fields': [
                    {'name': 'Plataforma', 'value1': specs1.platform_compatibility or 'N/A', 'value2': specs2.platform_compatibility or 'N/A'},
                    {'name': 'Género', 'value1': specs1.genre or 'N/A', 'value2': specs2.genre or 'N/A'},
                    {'name': 'Clasificación', 'value1': specs1.age_rating or 'N/A', 'value2': specs2.age_rating or 'N/A'},
                    {'name': 'Multijugador', 'value1': 'Sí' if specs1.multiplayer else 'No', 'value2': 'Sí' if specs2.multiplayer else 'No'},
                ]
            })
        
        return comparison
