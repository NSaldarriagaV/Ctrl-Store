# Pruebas Unitarias del Catálogo

## Descripción

Este documento describe las pruebas unitarias implementadas para el módulo de catálogo (`ctrlstore.apps.catalog`). Las pruebas validan el funcionamiento correcto de los filtros de productos y la función `get_main_specs()`.

## Ubicación

Las pruebas se encuentran en: `ctrlstore/apps/catalog/tests.py`

## Requisitos

- Django instalado y configurado
- Base de datos de pruebas (se crea automáticamente al ejecutar las pruebas)
- No se requieren dependencias externas (API, servicios remotos, etc.)

## Ejecución de Pruebas

### Ejecutar todas las pruebas del catálogo

```bash
python manage.py test ctrlstore.apps.catalog.tests.CatalogTests
```

### Ejecutar con settings específicos

```bash
python manage.py test ctrlstore.apps.catalog.tests.CatalogTests --settings=ctrlstore.settings.dev
```

### Ejecutar una prueba específica

```bash
# Por nombre de método
python manage.py test ctrlstore.apps.catalog.tests.CatalogTests.test_get_main_specs_gaming

# Por patrón
python manage.py test ctrlstore.apps.catalog.tests.CatalogTests.test_get_main_specs
```

### Ejecutar con verbosidad aumentada

```bash
# Ver más detalles
python manage.py test ctrlstore.apps.catalog.tests.CatalogTests --verbosity=2

# Ver aún más información
python manage.py test ctrlstore.apps.catalog.tests.CatalogTests --verbosity=3
```

### Ejecutar todas las pruebas del proyecto

```bash
python manage.py test
```

## Pruebas Implementadas

### 1. `test_product_list_filter_by_category`

**Descripción:** Valida que el filtro por categoría funciona correctamente usando el parámetro `?cat=slug`.

**Qué prueba:**
- Filtro por categoría gaming muestra solo productos gaming
- Filtro por categoría computadores muestra solo productos de computadores
- Los productos de otras categorías no aparecen en el resultado filtrado

**Parámetros probados:**
- `?cat=gaming`
- `?cat=computadores`

**Resultado esperado:** ✅ PASS

---

### 2. `test_product_list_filter_gaming`

**Descripción:** Valida el filtro específico para productos gaming usando `?gaming=true`.

**Qué prueba:**
- Solo productos con `category_type='gaming'` aparecen
- Productos de otras categorías (computadores, celulares) no aparecen

**Parámetros probados:**
- `?gaming=true`

**Resultado esperado:** ✅ PASS

---

### 3. `test_product_list_excludes_inactive`

**Descripción:** Verifica que los productos inactivos (`is_active=False`) no aparecen en el listado.

**Qué prueba:**
- Productos con `is_active=False` no se muestran
- Solo productos activos aparecen en los resultados

**Resultado esperado:** ✅ PASS

---

### 4. `test_get_main_specs_gaming`

**Descripción:** Prueba la función `get_main_specs()` para productos de tipo gaming.

**Qué prueba:**
- Retorna un diccionario con las especificaciones principales
- Incluye campos: "Plataforma", "Género"
- Los valores coinciden con las especificaciones del producto

**Resultado esperado:**
```python
{
    "Plataforma": "PC",
    "Género": "Acción"
}
```

**Resultado esperado:** ✅ PASS

---

### 5. `test_get_main_specs_computadores`

**Descripción:** Prueba la función `get_main_specs()` para productos de computadores.

**Qué prueba:**
- Retorna un diccionario con las especificaciones principales
- Incluye campos: "Procesador", "RAM", "Almacenamiento", "GPU"
- Los valores coinciden con las especificaciones del producto
- Formato correcto del almacenamiento: "SSD 512GB"

**Resultado esperado:**
```python
{
    "Procesador": "Intel i7",
    "RAM": "16GB",
    "Almacenamiento": "SSD 512GB",
    "GPU": "NVIDIA RTX 3060"
}
```

**Resultado esperado:** ✅ PASS

---

### 6. `test_get_main_specs_celulares`

**Descripción:** Prueba la función `get_main_specs()` para productos de celulares/tablets.

**Qué prueba:**
- Retorna un diccionario con las especificaciones principales
- Incluye campos: "Pantalla", "RAM", "Almacenamiento", "Cámara"
- Los valores coinciden con las especificaciones del producto

**Resultado esperado:**
```python
{
    "Pantalla": "6.5\" 1080x2400",
    "RAM": "8GB",
    "Almacenamiento": "128GB",
    "Cámara": "48MP"
}
```

**Resultado esperado:** ✅ PASS

---

### 7. `test_get_main_specs_without_specifications`

**Descripción:** Prueba el caso límite cuando un producto no tiene especificaciones.

**Qué prueba:**
- Retorna un diccionario vacío `{}`
- No lanza excepciones
- Maneja correctamente productos sin `ProductSpecification`

**Resultado esperado:** ✅ PASS

## Resultado Esperado de Ejecución Completa

Al ejecutar todas las pruebas, deberías ver:

```
Found 7 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.......
----------------------------------------------------------------------
Ran 7 tests in 0.988s

OK
Destroying test database for alias 'default'...
```

### Interpretación del Resultado

- **`Found 7 test(s)`**: Se encontraron 7 pruebas para ejecutar
- **`Creating test database`**: Django crea una base de datos temporal para las pruebas
- **`System check identified no issues`**: No hay problemas de configuración
- **`.......`**: Cada punto (.) representa una prueba que pasó exitosamente
- **`Ran 7 tests in 0.988s`**: Todas las pruebas se ejecutaron en menos de 1 segundo
- **`OK`**: Todas las pruebas pasaron correctamente
- **`Destroying test database`**: La base de datos temporal se elimina automáticamente

## Códigos de Salida

- **0**: Todas las pruebas pasaron exitosamente
- **1**: Una o más pruebas fallaron o hubo errores

## Manejo de Errores

### Si una prueba falla

Verás un mensaje detallado indicando:
- Qué prueba falló
- Qué assert falló
- Valores esperados vs valores obtenidos

Ejemplo de salida cuando falla una prueba:

```
FAIL: test_get_main_specs_gaming (ctrlstore.apps.catalog.tests.CatalogTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tests.py", line 129, in test_get_main_specs_gaming
    self.assertEqual(specs["Plataforma"], "PC")
AssertionError: 'Xbox' != 'PC'
```

### Solución de problemas comunes

1. **ImportError**: Verifica que todas las dependencias estén instaladas
2. **DatabaseError**: Asegúrate de que la configuración de base de datos sea correcta
3. **AssertionError**: Revisa los datos de prueba en `setUp()` y los valores esperados

## Integración Continua (CI)

Estas pruebas están diseñadas para ejecutarse en CI sin dependencias externas:

- ✅ No requieren conexión a internet
- ✅ No requieren servicios externos
- ✅ Usan base de datos en memoria (SQLite por defecto)
- ✅ Se ejecutan de forma aislada e independiente

### Ejemplo para GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python manage.py test ctrlstore.apps.catalog.tests.CatalogTests
```

## Mantenimiento

### Agregar nuevas pruebas

1. Agrega el método en la clase `CatalogTests`
2. Usa el prefijo `test_` para el nombre del método
3. Usa docstrings para documentar qué prueba
4. Ejecuta las pruebas para verificar que pasen

### Ejemplo de nueva prueba

```python
def test_nueva_funcionalidad(self):
    """Prueba la nueva funcionalidad X."""
    # Arrange
    producto = Product.objects.create(...)
    
    # Act
    resultado = producto.nueva_funcionalidad()
    
    # Assert
    self.assertEqual(resultado, valor_esperado)
```

## Contacto

Para preguntas sobre las pruebas, consultar al equipo de desarrollo.

