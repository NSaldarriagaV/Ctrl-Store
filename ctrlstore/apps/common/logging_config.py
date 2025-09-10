"""
Configuración de logging estructurado para Ctrl+Store.
Implementa logging con IDs de negocio siguiendo las guías de estilo.
"""

import logging
import sys
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """Formateador para logs estructurados con contexto de negocio."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatea el log con información estructurada."""
        # Información básica del log
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Agregar información de contexto si está disponible
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'order_id'):
            log_data['order_id'] = record.order_id
        
        if hasattr(record, 'payment_id'):
            log_data['payment_id'] = record.payment_id
        
        if hasattr(record, 'product_id'):
            log_data['product_id'] = record.product_id
        
        if hasattr(record, 'cart_id'):
            log_data['cart_id'] = record.cart_id
        
        # Agregar información adicional del extra
        for key, value in record.__dict__.items():
            if key.startswith('extra_'):
                log_data[key[6:]] = value
        
        # Formatear como JSON simple
        import json
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> None:
    """Configura el sistema de logging para la aplicación."""
    
    # Configurar el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    
    # Handler para archivo (en producción)
    try:
        file_handler = logging.FileHandler('logs/ctrlstore.log')
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    except (OSError, PermissionError):
        # Si no se puede crear el archivo, solo usar consola
        pass
    
    root_logger.addHandler(console_handler)
    
    # Configurar loggers específicos
    _configure_app_loggers()


def _configure_app_loggers() -> None:
    """Configura loggers específicos para cada app."""
    
    app_loggers = [
        'ctrlstore.apps.authx',
        'ctrlstore.apps.catalog',
        'ctrlstore.apps.cart',
        'ctrlstore.apps.order',
        'ctrlstore.apps.payment',
        'ctrlstore.apps.analytics',
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = True


class BusinessLogger:
    """Logger especializado para operaciones de negocio."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_user_action(
        self,
        action: str,
        user_id: Optional[int] = None,
        **kwargs
    ) -> None:
        """Log para acciones de usuario."""
        self.logger.info(
            f"User action: {action}",
            extra={
                'user_id': user_id,
                'action': action,
                **kwargs
            }
        )
    
    def log_cart_operation(
        self,
        operation: str,
        cart_id: Optional[int] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> None:
        """Log para operaciones del carrito."""
        self.logger.info(
            f"Cart operation: {operation}",
            extra={
                'cart_id': cart_id,
                'user_id': user_id,
                'operation': operation,
                **kwargs
            }
        )
    
    def log_order_operation(
        self,
        operation: str,
        order_id: Optional[int] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> None:
        """Log para operaciones de órdenes."""
        self.logger.info(
            f"Order operation: {operation}",
            extra={
                'order_id': order_id,
                'user_id': user_id,
                'operation': operation,
                **kwargs
            }
        )
    
    def log_payment_operation(
        self,
        operation: str,
        payment_id: Optional[int] = None,
        order_id: Optional[int] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> None:
        """Log para operaciones de pago."""
        self.logger.info(
            f"Payment operation: {operation}",
            extra={
                'payment_id': payment_id,
                'order_id': order_id,
                'user_id': user_id,
                'operation': operation,
                **kwargs
            }
        )
    
    def log_product_operation(
        self,
        operation: str,
        product_id: Optional[int] = None,
        **kwargs
    ) -> None:
        """Log para operaciones de productos."""
        self.logger.info(
            f"Product operation: {operation}",
            extra={
                'product_id': product_id,
                'operation': operation,
                **kwargs
            }
        )
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log para errores con contexto."""
        self.logger.error(
            f"Error: {str(error)}",
            extra={
                'error_type': type(error).__name__,
                'error_message': str(error),
                **(context or {})
            },
            exc_info=True
        )


# Instancias de loggers para cada app
authx_logger = BusinessLogger('ctrlstore.apps.authx')
catalog_logger = BusinessLogger('ctrlstore.apps.catalog')
cart_logger = BusinessLogger('ctrlstore.apps.cart')
order_logger = BusinessLogger('ctrlstore.apps.order')
payment_logger = BusinessLogger('ctrlstore.apps.payment')
analytics_logger = BusinessLogger('ctrlstore.apps.analytics')
