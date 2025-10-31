# API de Productos en Stock - Ctrl+Store

## Información del Servicio

**URL Base:** `http://127.0.0.1:8000` (cambiar por tu dominio en producción)

**Endpoint:** `/api/products/in-stock/`

**Método:** `GET`

**Autenticación:** No requiere autenticación (público)

## Descripción

Este endpoint retorna una lista de productos activos que están actualmente en stock, incluyendo información básica y enlace directo a la página de detalle de cada producto.

## Parámetros de Consulta (Opcionales)

- `featured` (opcional): Filtrar solo productos destacados
  - Valores aceptados: `true`, `1`, `yes`
  - Ejemplo: `?featured=true`

## Formato de Respuesta

### Estructura

```json
{
  "results": [
    {
      "id": 1,
      "name": "Laptop X",
      "price": 3500000.0,
      "detail_url": "/p/1/"
    },
    {
      "id": 2,
      "name": "Smartphone Y",
      "price": 1200000.0,
      "detail_url": "/p/2/"
    }
  ]
}
```

### Campos

- `id` (integer): ID único del producto
- `name` (string): Nombre del producto
- `price` (float): Precio en COP (pesos colombianos)
- `detail_url` (string): URL relativa para ver el detalle del producto (debe concatenarse con la URL base)

## Ejemplos de Uso

### 1. Obtener todos los productos en stock

```bash
curl http://127.0.0.1:8000/api/products/in-stock/
```

### 2. Obtener solo productos destacados

```bash
curl http://127.0.0.1:8000/api/products/in-stock/?featured=true
```

### 3. Ejemplo en Python (requests)

```python
import requests

# Obtener todos los productos
response = requests.get('http://127.0.0.1:8000/api/products/in-stock/')
data = response.json()

for product in data['results']:
    print(f"{product['name']}: ${product['price']:,.0f}")
    print(f"Ver más: http://127.0.0.1:8000{product['detail_url']}")
```

### 4. Ejemplo en JavaScript (fetch)

```javascript
fetch('http://127.0.0.1:8000/api/products/in-stock/')
  .then(response => response.json())
  .then(data => {
    data.results.forEach(product => {
      console.log(`${product.name}: $${product.price.toLocaleString()}`);
      console.log(`Ver más: http://127.0.0.1:8000${product.detail_url}`);
    });
  });
```

### 5. Ejemplo en Django (consumir desde otro proyecto)

```python
import requests

def get_products_from_ctrlstore():
    url = 'http://127.0.0.1:8000/api/products/in-stock/'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['results']
    return []

# Usar en una vista
def productos_aliados(request):
    products = get_products_from_ctrlstore()
    return render(request, 'productos_aliados.html', {'products': products})
```

## Limitaciones

- Máximo 100 productos por consulta
- Solo productos activos (`is_active=True`)
- Solo productos con stock disponible (`stock_quantity > 0`)
- Ordenados por: destacados primero, luego por fecha de creación (más recientes primero)

## Códigos de Estado HTTP

- `200 OK`: Consulta exitosa
- `404 Not Found`: Ruta no encontrada (verificar URL)
- `500 Internal Server Error`: Error del servidor

## Notas Importantes

1. **URL del detalle:** El campo `detail_url` es relativo. Para construir la URL completa, concaténalo con la URL base del servidor.
   - Ejemplo: Si `detail_url = "/p/1/"` y tu servidor está en `http://127.0.0.1:8000`, la URL completa es `http://127.0.0.1:8000/p/1/`

2. **Precios:** Todos los precios están en pesos colombianos (COP) y son números decimales.

3. **Límite de resultados:** El endpoint retorna máximo 100 productos. Si necesitas más, implementa paginación en tu lado o contacta al equipo para aumentar el límite.

## Contacto

Para preguntas o problemas con la API, contactar al equipo de Ctrl+Store.

