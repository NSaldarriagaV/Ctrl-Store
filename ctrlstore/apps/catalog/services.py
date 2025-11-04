"""Servicios para el catálogo."""
import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# URL de la API del equipo aliado (Bloomberry)
BLOOMBERRY_API_URL = "https://bloomberry-app-1067375337365.us-central1.run.app/products/api/"


def get_bloomberry_products(timeout: int = 5) -> list[dict]:
    """
    Consume la API de productos de Bloomberry y retorna lista de productos.
    
    Args:
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        Lista de productos en formato dict. Retorna lista vacía si hay error.
    """
    try:
        response = requests.get(BLOOMBERRY_API_URL, timeout=timeout)
        response.raise_for_status()
        products = response.json()
        
        # Normalizar formato si es necesario
        normalized = []
        for p in products:
            normalized.append({
                "id": p.get("id"),
                "name": p.get("nombre", p.get("name", "")),
                "description": p.get("descripcion", p.get("description", "")),
                "price": float(p.get("precio", p.get("price", 0))),
                "stock": p.get("stock", 0),
                "image_url": p.get("imagen", p.get("image_url", "")),
                "detail_url": p.get("detalle_url", p.get("detail_url", "")),
            })
        
        logger.info(f"Consumidos {len(normalized)} productos de Bloomberry")
        return normalized
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al consumir API de Bloomberry: {e}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado al procesar productos de Bloomberry: {e}")
        return []
