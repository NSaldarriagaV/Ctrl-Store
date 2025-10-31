"""Servicio para obtener clima de Medellín usando Open-Meteo API."""
import json
import time
from urllib.request import urlopen

_CACHE = {}
_CACHE_TTL = 300  # 5 minutos


def get_medellin_weather():
    """
    Obtiene el clima actual de Medellín desde Open-Meteo.
    Retorna dict con 'temp_c' y 'summary'.
    Usa caché de 5 minutos.
    """
    cache_key = "medellin"
    now = time.time()
    
    # Verificar caché
    if cache_key in _CACHE:
        cached_time, cached_data = _CACHE[cache_key]
        if now - cached_time < _CACHE_TTL:
            return cached_data
    
    # Obtener datos de la API
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=6.2518&longitude=-75.5636"
        "&current=temperature_2m,weather_code"
        "&timezone=America/Bogota"
    )
    
    try:
        with urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        current = data.get("current", {})
        temp = current.get("temperature_2m")
        code = current.get("weather_code", 0)
        
        # Mapear código a descripción
        descriptions = {
            0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado",
            3: "Nublado", 45: "Niebla", 48: "Niebla escarchada",
            51: "Llovizna débil", 53: "Llovizna", 55: "Llovizna fuerte",
            61: "Lluvia débil", 63: "Lluvia", 65: "Lluvia fuerte",
            71: "Nieve débil", 73: "Nieve", 75: "Nieve fuerte",
            80: "Chubascos débiles", 81: "Chubascos", 82: "Chubascos fuertes",
            95: "Tormenta"
        }
        summary = descriptions.get(int(code), "Desconocido")
        
        result = {
            "temp_c": float(temp) if temp is not None else None,
            "summary": summary
        }
        
    except Exception:
        result = {
            "temp_c": None,
            "summary": "Clima no disponible"
        }
    
    # Guardar en caché
    _CACHE[cache_key] = (now, result)
    return result
