"""Template tags para mostrar información del clima."""
from django import template
from ctrlstore.apps.common.weather import get_medellin_weather

register = template.Library()


@register.simple_tag
def get_weather():
    """Retorna el clima actual de Medellín."""
    return get_medellin_weather()

