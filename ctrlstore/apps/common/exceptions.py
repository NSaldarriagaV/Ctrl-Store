"""
Excepciones personalizadas para el proyecto Ctrl+Store.
Implementa manejo de errores de negocio siguiendo las guías de estilo.
"""

from __future__ import annotations


class CtrlStoreError(Exception):
    """Excepción base para errores del sistema Ctrl+Store."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(CtrlStoreError):
    """Error relacionado con autenticación."""
    pass


class AuthorizationError(CtrlStoreError):
    """Error relacionado con autorización."""
    pass


class ValidationError(CtrlStoreError):
    """Error de validación de datos."""
    pass


class BusinessLogicError(CtrlStoreError):
    """Error de lógica de negocio."""
    pass


# Errores específicos del catálogo
class ProductError(BusinessLogicError):
    """Error relacionado con productos."""
    pass


class CategoryError(BusinessLogicError):
    """Error relacionado con categorías."""
    pass


class StockError(ProductError):
    """Error relacionado con stock de productos."""
    pass


# Errores específicos del carrito
class CartError(BusinessLogicError):
    """Error relacionado con el carrito."""
    pass


class CartItemError(CartError):
    """Error relacionado con items del carrito."""
    pass


# Errores específicos de órdenes
class OrderError(BusinessLogicError):
    """Error relacionado con órdenes."""
    pass


class OrderItemError(OrderError):
    """Error relacionado con items de órdenes."""
    pass


# Errores específicos de pagos
class PaymentError(BusinessLogicError):
    """Error relacionado con pagos."""
    pass


class PaymentProcessingError(PaymentError):
    """Error en el procesamiento de pagos."""
    pass


class PaymentValidationError(PaymentError):
    """Error de validación de datos de pago."""
    pass


# Errores específicos de usuarios y roles
class UserError(BusinessLogicError):
    """Error relacionado con usuarios."""
    pass


class RoleError(BusinessLogicError):
    """Error relacionado con roles."""
    pass


# Errores específicos de analytics
class AnalyticsError(BusinessLogicError):
    """Error relacionado con analytics."""
    pass


class DataProcessingError(AnalyticsError):
    """Error en el procesamiento de datos."""
    pass
