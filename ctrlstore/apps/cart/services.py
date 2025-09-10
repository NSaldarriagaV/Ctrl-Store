"""
Servicios del carrito de compras.
Implementa la lógica de negocio siguiendo el principio "Thin Views, Fat Services".
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpRequest

from .models import Cart, CartItem
from .utils import get_or_create_cart

if TYPE_CHECKING:
    from ctrlstore.apps.catalog.models import Product

logger = logging.getLogger(__name__)


class CartService:
    """Servicio para gestión del carrito de compras."""
    
    @staticmethod
    def add_to_cart(
        request: HttpRequest,
        product: Product,
        quantity: int = 1
    ) -> CartItem:
        """
        Agrega un producto al carrito.
        
        Args:
            request: Request HTTP
            product: Producto a agregar
            quantity: Cantidad a agregar
            
        Returns:
            Item del carrito creado o actualizado
            
        Raises:
            ValueError: Si la cantidad es inválida o no hay stock
        """
        if quantity < 1:
            raise ValueError("La cantidad debe ser mayor a 0")
        
        # Verificar stock
        if hasattr(product, 'stock_quantity') and product.stock_quantity is not None:
            if quantity > product.stock_quantity:
                raise ValueError("No hay stock suficiente")
        
        cart = get_or_create_cart(request)
        
        with transaction.atomic():
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={
                    'quantity': quantity,
                    'unit_price': Decimal(str(product.price))
                }
            )
            
            if not created:
                item.quantity += quantity
                item.save()
            
            logger.info(
                "Producto agregado al carrito",
                extra={
                    "cart_id": cart.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": quantity,
                    "user_id": request.user.id if request.user.is_authenticated else None,
                }
            )
            
            return item
    
    @staticmethod
    def update_cart_item(
        request: HttpRequest,
        item_id: int,
        quantity: int
    ) -> CartItem:
        """
        Actualiza la cantidad de un item en el carrito.
        
        Args:
            request: Request HTTP
            item_id: ID del item a actualizar
            quantity: Nueva cantidad
            
        Returns:
            Item actualizado
            
        Raises:
            ValueError: Si la cantidad es inválida o el item no existe
        """
        if quantity < 0:
            raise ValueError("La cantidad no puede ser negativa")
        
        cart = get_or_create_cart(request)
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            
            if quantity == 0:
                item.delete()
                logger.info(
                    "Item eliminado del carrito",
                    extra={
                        "cart_id": cart.id,
                        "item_id": item_id,
                        "product_name": item.product.name,
                    }
                )
                return None
            else:
                item.quantity = quantity
                item.save()
                
                logger.info(
                    "Cantidad de item actualizada en el carrito",
                    extra={
                        "cart_id": cart.id,
                        "item_id": item_id,
                        "product_name": item.product.name,
                        "new_quantity": quantity,
                    }
                )
                
                return item
                
        except CartItem.DoesNotExist:
            raise ValueError("El item no existe en el carrito")
    
    @staticmethod
    def remove_from_cart(request: HttpRequest, item_id: int) -> bool:
        """
        Elimina un item del carrito.
        
        Args:
            request: Request HTTP
            item_id: ID del item a eliminar
            
        Returns:
            True si se eliminó exitosamente
            
        Raises:
            ValueError: Si el item no existe
        """
        cart = get_or_create_cart(request)
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            product_name = item.product.name
            item.delete()
            
            logger.info(
                "Item eliminado del carrito",
                extra={
                    "cart_id": cart.id,
                    "item_id": item_id,
                    "product_name": product_name,
                }
            )
            
            return True
            
        except CartItem.DoesNotExist:
            raise ValueError("El item no existe en el carrito")
    
    @staticmethod
    def clear_cart(request: HttpRequest) -> bool:
        """
        Vacía completamente el carrito.
        
        Args:
            request: Request HTTP
            
        Returns:
            True si se vació exitosamente
        """
        cart = get_or_create_cart(request)
        items_count = cart.items.count()
        
        cart.items.all().delete()
        
        logger.info(
            "Carrito vaciado",
            extra={
                "cart_id": cart.id,
                "items_removed": items_count,
                "user_id": request.user.id if request.user.is_authenticated else None,
            }
        )
        
        return True
    
    @staticmethod
    def get_cart_summary(cart: Cart) -> dict:
        """
        Obtiene un resumen del carrito.
        
        Args:
            cart: Carrito a resumir
            
        Returns:
            Diccionario con resumen del carrito
        """
        items = cart.items.select_related('product').all()
        
        total_items = sum(item.quantity for item in items)
        total_amount = sum(item.subtotal for item in items)
        
        return {
            'items': items,
            'total_items': total_items,
            'total_amount': total_amount,
            'items_count': len(items),
        }
    
    @staticmethod
    def merge_carts(user_cart: Cart, session_cart: Cart) -> Cart:
        """
        Fusiona un carrito de sesión con el carrito del usuario.
        
        Args:
            user_cart: Carrito del usuario autenticado
            session_cart: Carrito de la sesión anónima
            
        Returns:
            Carrito fusionado (user_cart)
        """
        if user_cart.id == session_cart.id:
            return user_cart
        
        with transaction.atomic():
            for session_item in session_cart.items.all():
                user_item, created = user_cart.items.get_or_create(
                    product=session_item.product,
                    defaults={
                        'quantity': session_item.quantity,
                        'unit_price': session_item.unit_price
                    }
                )
                
                if not created:
                    user_item.quantity += session_item.quantity
                    user_item.save()
            
            # Eliminar el carrito de sesión
            session_cart.delete()
            
            logger.info(
                "Carritos fusionados exitosamente",
                extra={
                    "user_cart_id": user_cart.id,
                    "session_cart_id": session_cart.id,
                    "user_id": user_cart.user.id if user_cart.user else None,
                }
            )
            
            return user_cart


class CartValidationService:
    """Servicio para validación del carrito."""
    
    @staticmethod
    def validate_cart_for_checkout(cart: Cart) -> dict:
        """
        Valida que el carrito esté listo para checkout.
        
        Args:
            cart: Carrito a validar
            
        Returns:
            Diccionario con resultado de validación
        """
        errors = []
        warnings = []
        
        if not cart.items.exists():
            errors.append("El carrito está vacío")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Verificar stock de productos
        for item in cart.items.select_related('product').all():
            product = item.product
            
            if not product.is_active:
                errors.append(f"El producto '{product.name}' no está disponible")
                continue
            
            if hasattr(product, 'stock_quantity') and product.stock_quantity is not None:
                if item.quantity > product.stock_quantity:
                    errors.append(
                        f"No hay suficiente stock para '{product.name}'. "
                        f"Disponible: {product.stock_quantity}, "
                        f"Solicitado: {item.quantity}"
                    )
        
        # Verificar precios
        for item in cart.items.select_related('product').all():
            if item.unit_price != item.product.price:
                warnings.append(
                    f"El precio de '{item.product.name}' ha cambiado. "
                    f"Precio actual: ${item.product.price}"
                )
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
        }
