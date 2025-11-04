# Consumo de API Externa - Bloomberry

## Descripción

Ctrl+Store consume la API pública de productos de **Bloomberry**, nuestro socio comercial, para mostrar sus productos en nuestra plataforma.

## Endpoint Consumido

**URL:** `https://bloomberry-app-1067375337365.us-central1.run.app/products/api/`

**Método:** `GET`

**Autenticación:** No requerida (público)

## Implementación

### Ubicación en el Código

- **Servicio:** `ctrlstore/apps/catalog/services.py` → función `get_bloomberry_products()`
- **Vista:** `ctrlstore/apps/catalog/views.py` → clase `ProductosAliadosView`
- **Ruta:** `/productos-aliados/`
- **Template:** `templates/catalog/productos-aliados.html`

### Formato de Datos Recibidos

La API de Bloomberry retorna un array JSON con productos en este formato:

```json
[
  {
    "id": 1,
    "nombre": "Lip Balm",
    "descripcion": "Bálsamo hidratante para labios...",
    "precio": 15000.0,
    "stock": 10,
    "imagen": "http://...",
    "detalle_url": "http://..."
  }
]
```

### Normalización

Nuestro servicio normaliza los datos recibidos al formato interno:

```python
{
    "id": int,
    "name": str,  # desde "nombre"
    "description": str,  # desde "descripcion"
    "price": float,  # desde "precio"
    "stock": int,
    "image_url": str,  # desde "imagen"
    "detail_url": str  # desde "detalle_url"
}
```

## Funcionalidad

### Página de Productos Aliados

**URL:** `http://127.0.0.1:8000/productos-aliados/`

**Características:**
- ✅ Muestra todos los productos disponibles de Bloomberry
- ✅ Cards con imagen, nombre, descripción, precio y stock
- ✅ Badge "Producto Aliado" para identificar origen
- ✅ Enlace directo al detalle en el sitio de Bloomberry
- ✅ Manejo de errores si la API no está disponible
- ✅ Información visible sobre la fuente de datos

### Navegación

Los productos aliados están accesibles desde:
- **Menú principal:** Botón "Productos Aliados" en la navbar
- **URL directa:** `/productos-aliados/`

## Manejo de Errores

El servicio implementa manejo robusto de errores:

- ✅ Timeout de 5 segundos para evitar bloqueos
- ✅ Logging de errores para debugging
- ✅ Retorna lista vacía si hay problemas (no rompe la página)
- ✅ Mensaje amigable al usuario si no hay productos disponibles

## Indicadores Visuales

En la página de productos aliados se muestra claramente:

1. **Badge "Producto Aliado"** en cada producto
2. **Alerta informativa** explicando que son productos de Bloomberry
3. **Sección al final** con información técnica de la API consumida
4. **Enlaces externos** marcados con icono `fa-external-link-alt`

## Logging

Los logs registran:
- Éxito: Cantidad de productos consumidos
- Errores: Detalles de fallos de conexión o procesamiento

**Ubicación de logs:** `ctrlstore.apps.catalog.services`

## Ejemplo de Uso

```python
from ctrlstore.apps.catalog.services import get_bloomberry_products

# Obtener productos
products = get_bloomberry_products()

# products es una lista de dicts con productos normalizados
for product in products:
    print(f"{product['name']}: ${product['price']:,.0f}")
```

## Pruebas

Para probar el consumo de la API:

1. Visita: `http://127.0.0.1:8000/productos-aliados/`
2. Verifica que se muestren los productos de Bloomberry
3. Verifica que los enlaces externos funcionen correctamente

## Consideraciones Técnicas

- **Cache:** No implementado actualmente (se consume en cada petición)
- **Rate Limiting:** No aplicado (API pública)
- **Timeout:** 5 segundos por defecto
- **Dependencia:** Requiere `requests` instalado (`requirements.txt`)

## Configuración

La URL de la API está definida en `ctrlstore/apps/catalog/services.py`:

```python
BLOOMBERRY_API_URL = "https://bloomberry-app-1067375337365.us-central1.run.app/products/api/"
```

Para cambiar la URL, modifica esta constante.

## Mejoras Futuras

- [ ] Implementar caché (Redis/Memcached) para reducir llamadas
- [ ] Agregar refresh automático cada X minutos
- [ ] Manejar paginación si Bloomberry la implementa
- [ ] Agregar filtros/búsqueda en productos aliados

## Referencias

- **API de Bloomberry:** https://bloomberry-app-1067375337365.us-central1.run.app/products/api/
- **Documentación de nuestra API:** [`docs/API_PRODUCTOS.md`](API_PRODUCTOS.md)

