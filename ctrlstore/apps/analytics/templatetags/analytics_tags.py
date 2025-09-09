# Crea el paquete templatetags con __init__.py y este archivo
from django import template
from ctrlstore.apps.analytics.models import ProductSalesAggregate

register = template.Library()

@register.simple_tag
def top_sellers(limit=3):
    return ProductSalesAggregate.objects.select_related("product").order_by("-units_sold", "-revenue")[:limit]
