# Crea el paquete templatetags con __init__.py y este archivo
from django import template
from ctrlstore.apps.analytics.models import ProductSalesAggregate
from ctrlstore.apps.analytics.services import top_viewed

register = template.Library()

@register.simple_tag
def top_sellers(limit=3):
    return ProductSalesAggregate.objects.select_related("product").order_by("-units_sold", "-revenue")[:limit]

register = template.Library()

@register.simple_tag
def top_viewed_products(limit=3, days=None):
    """
    Uso: {% top_viewed_products 3 7 as topv %}  -> top 3 de los últimos 7 días
         {% top_viewed_products 3 as topv %}    -> top 3 global
    Retorna lista de dicts {product, views}
    """
    items = top_viewed(limit=limit, days=days)
    return [{"product": p, "views": v} for (p, v) in items]