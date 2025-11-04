## Endpoints – Proveer y consumir

### Proveer (este proyecto)
- GET /api/products/in-stock/
  - Descripción: Lista productos activos y en stock
  - Respuesta: JSON con `{ id, name, price, detail_url }`
  - Ejemplo:
  ```json
  {
    "results": [
      {"id": 1, "name": "Laptop X", "price": 3500000, "detail_url": "/catalog/p/laptop-x/"}
    ]
  }
  ```
  - Parámetros: `featured=true|1` (opcional)

### Consumir – Equipo precedente
- Ruta en UI: /productos-aliados
- Fuente: URL JSON provista por el equipo anterior (configurable por env)
- Render: listado con nombre, precio y enlace externo o detalle local

### Consumir – Tercero (clima de Medellín)
- Servicio usado: Open-Meteo 
- Render: banner en cabecera con temperatura y estado actual
 - Caché: 5 minutos en memoria, fallback "Clima no disponible" si falla

### Notas
- Documentar en README variables de entorno (URL aliados, API key clima)
- Manejar timeouts y errores (mostrar fallback en UI)



