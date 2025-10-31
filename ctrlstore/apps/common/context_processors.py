"""Context processor para inyectar información del clima en todos los templates."""
from .weather import get_medellin_weather


def weather_info(request):
    """Inyecta 'weather' en el contexto de todos los templates."""
    try:
        weather_data = get_medellin_weather()
    except Exception:
        weather_data = {"temp_c": None, "summary": "Clima no disponible"}
    return {"weather": weather_data}
