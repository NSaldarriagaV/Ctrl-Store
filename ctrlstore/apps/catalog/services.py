"""
Servicios del catálogo de productos.
Implementa la lógica de negocio siguiendo el principio "Thin Views, Fat Services".
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Dict, List, Optional

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import QuerySet

from .models import Category, Product, ProductSpecification

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


class CategoryService:
    """Servicio para gestión de categorías."""
    
    @staticmethod
    def get_active_categories() -> QuerySet[Category]:
        """
        Obtiene todas las categorías activas.
        
        Returns:
            QuerySet de categorías activas
        """
        return Category.objects.filter(is_active=True).order_by('name')
    
    @staticmethod
    def get_main_categories() -> QuerySet[Category]:
        """
        Obtiene las categorías principales (sin padre).
        
        Returns:
            QuerySet de categorías principales
        """
        return Category.objects.filter(
            parent__isnull=True,
            is_active=True
        ).order_by('name')
    
    @staticmethod
    def get_category_by_slug(slug: str) -> Optional[Category]:
        """
        Obtiene una categoría por su slug.
        
        Args:
            slug: Slug de la categoría
            
        Returns:
            Categoría encontrada o None
        """
        try:
            return Category.objects.get(slug=slug, is_active=True)
        except Category.DoesNotExist:
            return None
    
    @staticmethod
    def create_category(
        name: str,
        slug: str,
        category_type: str,
        parent: Optional[Category] = None,
        is_active: bool = True
    ) -> Category:
        """
        Crea una nueva categoría.
        
        Args:
            name: Nombre de la categoría
            slug: Slug único
            category_type: Tipo de categoría
            parent: Categoría padre (opcional)
            is_active: Si está activa
            
        Returns:
            Categoría creada
            
        Raises:
            ValueError: Si el slug ya existe
        """
        if Category.objects.filter(slug=slug).exists():
            raise ValueError(f"La categoría con slug '{slug}' ya existe")
        
        category = Category.objects.create(
            name=name,
            slug=slug,
            category_type=category_type,
            parent=parent,
            is_active=is_active
        )
        
        logger.info(
            "Categoría creada exitosamente",
            extra={
                "category_id": category.id,
                "category_name": category.name,
                "category_type": category_type,
            }
        )
        
        return category


class ProductService:
    """Servicio para gestión de productos."""
    
    @staticmethod
    def get_active_products() -> QuerySet[Product]:
        """
        Obtiene todos los productos activos.
        
        Returns:
            QuerySet de productos activos
        """
        return Product.objects.filter(is_active=True).select_related('category')
    
    @staticmethod
    def get_featured_products() -> QuerySet[Product]:
        """
        Obtiene productos destacados.
        
        Returns:
            QuerySet de productos destacados
        """
        return Product.objects.filter(
            is_featured=True,
            is_active=True
        ).select_related('category')
    
    @staticmethod
    def get_products_by_category(category: Category) -> QuerySet[Product]:
        """
        Obtiene productos de una categoría específica.
        
        Args:
            category: Categoría a filtrar
            
        Returns:
            QuerySet de productos de la categoría
        """
        return Product.objects.filter(
            category=category,
            is_active=True
        ).select_related('category')
    
    @staticmethod
    def get_gaming_products() -> QuerySet[Product]:
        """
        Obtiene productos de gaming.
        
        Returns:
            QuerySet de productos de gaming
        """
        return Product.objects.filter(
            category__category_type='gaming',
            is_active=True
        ).select_related('category')
    
    @staticmethod
    def search_products(query: str) -> QuerySet[Product]:
        """
        Busca productos por nombre o descripción.
        
        Args:
            query: Término de búsqueda
            
        Returns:
            QuerySet de productos encontrados
        """
        return Product.objects.filter(
            is_active=True
        ).filter(
            name__icontains=query
        ).select_related('category')
    
    @staticmethod
    def get_product_by_slug(slug: str) -> Optional[Product]:
        """
        Obtiene un producto por su slug.
        
        Args:
            slug: Slug del producto
            
        Returns:
            Producto encontrado o None
        """
        try:
            return Product.objects.select_related('category').get(
                slug=slug,
                is_active=True
            )
        except Product.DoesNotExist:
            return None
    
    @staticmethod
    def create_product(
        name: str,
        slug: str,
        description: str,
        short_description: str,
        price: Decimal,
        category: Category,
        stock_quantity: int = 0,
        is_featured: bool = False,
        main_image: Optional[str] = None
    ) -> Product:
        """
        Crea un nuevo producto.
        
        Args:
            name: Nombre del producto
            slug: Slug único
            description: Descripción completa
            short_description: Descripción corta
            price: Precio del producto
            category: Categoría del producto
            stock_quantity: Cantidad en stock
            is_featured: Si es destacado
            main_image: Ruta de la imagen principal
            
        Returns:
            Producto creado
            
        Raises:
            ValueError: Si el slug ya existe
        """
        if Product.objects.filter(slug=slug).exists():
            raise ValueError(f"El producto con slug '{slug}' ya existe")
        
        product = Product.objects.create(
            name=name,
            slug=slug,
            description=description,
            short_description=short_description,
            price=price,
            category=category,
            stock_quantity=stock_quantity,
            is_featured=is_featured,
            main_image=main_image
        )
        
        logger.info(
            "Producto creado exitosamente",
            extra={
                "product_id": product.id,
                "product_name": product.name,
                "category": category.name,
            }
        )
        
        return product
    
    @staticmethod
    def update_stock(product: Product, quantity: int) -> Product:
        """
        Actualiza el stock de un producto.
        
        Args:
            product: Producto a actualizar
            quantity: Nueva cantidad en stock
            
        Returns:
            Producto actualizado
            
        Raises:
            ValueError: Si la cantidad es negativa
        """
        if quantity < 0:
            raise ValueError("La cantidad en stock no puede ser negativa")
        
        product.stock_quantity = quantity
        product.save()
        
        logger.info(
            "Stock de producto actualizado",
            extra={
                "product_id": product.id,
                "product_name": product.name,
                "new_stock": quantity,
            }
        )
        
        return product


class ProductSpecificationService:
    """Servicio para gestión de especificaciones de productos."""
    
    @staticmethod
    def create_specification(
        product: Product,
        brand: str = "",
        model: str = "",
        **spec_data
    ) -> ProductSpecification:
        """
        Crea especificaciones para un producto.
        
        Args:
            product: Producto al que pertenecen las especificaciones
            brand: Marca del producto
            model: Modelo del producto
            **spec_data: Datos adicionales de especificación
            
        Returns:
            Especificación creada
            
        Raises:
            ValueError: Si el producto ya tiene especificaciones
        """
        if hasattr(product, 'specifications'):
            raise ValueError(f"El producto '{product.name}' ya tiene especificaciones")
        
        spec = ProductSpecification.objects.create(
            product=product,
            brand=brand,
            model=model,
            **spec_data
        )
        
        logger.info(
            "Especificaciones de producto creadas",
            extra={
                "product_id": product.id,
                "product_name": product.name,
                "brand": brand,
                "model": model,
            }
        )
        
        return spec
    
    @staticmethod
    def update_specification(
        product: Product,
        brand: str = "",
        model: str = "",
        **spec_data
    ) -> ProductSpecification:
        """
        Actualiza las especificaciones de un producto.
        
        Args:
            product: Producto cuyas especificaciones se actualizarán
            brand: Nueva marca
            model: Nuevo modelo
            **spec_data: Nuevos datos de especificación
            
        Returns:
            Especificación actualizada
        """
        if not hasattr(product, 'specifications'):
            return ProductSpecificationService.create_specification(
                product, brand, model, **spec_data
            )
        
        spec = product.specifications
        spec.brand = brand
        spec.model = model
        
        # Actualizar campos adicionales
        for field, value in spec_data.items():
            if hasattr(spec, field):
                setattr(spec, field, value)
        
        spec.save()
        
        logger.info(
            "Especificaciones de producto actualizadas",
            extra={
                "product_id": product.id,
                "product_name": product.name,
            }
        )
        
        return spec


class ProductFilterService:
    """Servicio para filtrado y paginación de productos."""
    
    @staticmethod
    def filter_products(
        request: HttpRequest,
        products: QuerySet[Product],
        page_size: int = 12
    ) -> Dict:
        """
        Filtra y pagina productos según los parámetros de la request.
        
        Args:
            request: Request HTTP con parámetros de filtro
            products: QuerySet base de productos
            page_size: Tamaño de página para paginación
            
        Returns:
            Diccionario con productos filtrados y datos de paginación
        """
        # Filtro por categoría
        category_slug = request.GET.get('cat')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug, is_active=True)
                products = products.filter(category=category)
            except Category.DoesNotExist:
                pass
        
        # Filtro por gaming
        if request.GET.get('gaming'):
            products = products.filter(category__category_type='gaming')
        
        # Búsqueda por texto
        search_query = request.GET.get('search')
        if search_query:
            products = products.filter(name__icontains=search_query)
        
        # Paginación
        paginator = Paginator(products, page_size)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        return {
            'products': page_obj,
            'is_paginated': paginator.num_pages > 1,
            'page_obj': page_obj,
            'paginator': paginator,
        }
