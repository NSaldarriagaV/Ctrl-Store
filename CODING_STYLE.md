# Guía de Estilo y Reglas de Programación - Ctrl+Store

## 1. Principios Generales

### 1.1 Filosofía
- **Legibilidad > Ingenio**: Prioriza código claro y explícito
- **Consistencia**: Si hay varias formas correctas, usa la del proyecto
- **"Thin Views, Fat Services"**: Vistas delgadas, lógica de negocio en services/
- **Inmutabilidad por defecto**: Evita mutar estructuras salvo que sea necesario
- **Idempotencia**: Operaciones críticas (pagos, generación de factura) deben ser idempotentes

### 1.2 Herramientas de Formateo
- **Formateo**: `black` (línea 100)
- **Imports**: `isort`
- **Linting**: `ruff`
- **Tipado**: `mypy`

### 1.3 Convenciones de Naming
- **Módulos/paquetes**: `snake_case`
- **Clases**: `PascalCase`
- **Funciones/variables**: `snake_case`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Templates**: `kebab-case.html`

### 1.4 Commits Git
Formato: `tipo(scope): resumen`

Tipos:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `refactor`: Refactorización
- `test`: Tests
- `docs`: Documentación
- `chore`: Tareas de mantenimiento

## 2. Organización del Proyecto

### 2.1 Estructura de Apps
```
ctrlstore/
├── settings/
├── apps/
│   ├── authx/          # Autenticación y usuarios
│   ├── catalog/        # Catálogo de productos
│   ├── cart/           # Carrito de compras
│   ├── order/          # Órdenes
│   ├── payment/        # Pagos
│   ├── billing/        # Facturación
│   ├── analytics/      # Analíticas
│   └── common/         # Utilidades comunes
```

### 2.2 Separación de Responsabilidades
- **No mezclar responsabilidades** entre apps
- **Settings 12-factor**: Variables sensibles por entorno, nunca en repo
- **Cada app tiene su propio namespace** en URLs

## 3. Reglas por Categoría

### 3.1 Rutas (URLs)
- Toda ruta debe estar asociada a un View
- Usar namespaces (`app_name`)
- Nombres consistentes: `catalog:product_detail`
- Nunca hardcodear URLs en templates
- Agrupar rutas en cada app
- Usar `reverse_lazy` en redirecciones

### 3.2 Vistas (Controllers)
- Preferir **Class Based Views** para CRUD
- Mantener **vistas delgadas**
- Autenticación y permisos claros
- Contexto mínimo y explícito
- Respuestas correctas: 404, 403, 400
- Evitar N+1 queries
- Paginación obligatoria en listados
- CSRF activo en POST

### 3.3 Modelos
- **Dinero → DecimalField**
- Implementar `__str__` y constraints
- Validación en `clean()`
- Operaciones críticas en `transaction.atomic()`
- QuerySets personalizados
- Índices en campos clave
- Signals con moderación

### 3.4 Formularios
- Validación en formularios, no en vistas
- Errores claros
- Nunca guardar datos sensibles de tarjeta
- Validadores centralizados

### 3.5 Templates
- Todas las vistas extienden `base.html`
- Templates siempre en HTML
- Nada de lógica de negocio
- Accesibilidad básica
- CSS organizados en `static/`

### 3.6 Servicios
- **Lógica pesada en services/**
- **Idempotencia obligatoria**
- Métodos estáticos para operaciones puras
- Logging estructurado con IDs de negocio

### 3.7 Seguridad
- CSRF siempre activo
- Escapar variables → evitar XSS
- Passwords con algoritmos fuertes
- Permisos de objeto: un cliente solo ve lo suyo

### 3.8 Observabilidad
- **Logging estructurado**
- Logs con `user_id`, `order_id`, `payment_id`
- Usar `BusinessLogger` para operaciones de negocio

### 3.9 Migraciones y Datos
- Una migración por cambio de modelo
- Datos de prueba en fixtures
- Comandos de management para setup

## 4. Principios DRY y ETC

### 4.1 DRY (Don't Repeat Yourself)
- Extraer lógica común a servicios
- Usar mixins para funcionalidad compartida
- Templates base y herencia
- Validadores reutilizables

### 4.2 ETC (Easier To Change)
- Configuración por entorno
- Servicios desacoplados
- Interfaces claras entre módulos
- Tests que faciliten refactoring

## 5. Ejemplos de Código

### 5.1 Vista Delgada con Servicio
```python
class ProductListView(TemplateView):
    """Vista delgada que delega lógica al servicio."""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(ProductService.get_products_context(self.request))
        return context
```

### 5.2 Servicio con Logging
```python
class ProductService:
    @staticmethod
    def create_product(name: str, price: Decimal) -> Product:
        try:
            product = Product.objects.create(name=name, price=price)
            catalog_logger.log_product_operation(
                "product_created",
                product_id=product.id,
                product_name=product.name
            )
            return product
        except Exception as e:
            catalog_logger.log_error(e, {"action": "create_product"})
            raise ProductError(f"Error al crear producto: {str(e)}")
```

### 5.3 Manejo de Errores
```python
try:
    item = CartService.add_to_cart(request, product, quantity)
    messages.success(request, f"{product.name} agregado al carrito.")
except StockError as e:
    messages.error(request, str(e))
except CartError as e:
    messages.error(request, str(e))
```

## 6. Comandos Útiles

### 6.1 Formateo y Linting
```bash
# Formatear código
black --line-length 100 .

# Organizar imports
isort .

# Linting
ruff check .

# Verificación de tipos
mypy .
```

### 6.2 Tests
```bash
# Ejecutar tests
python manage.py test

# Tests con coverage
coverage run --source='.' manage.py test
coverage report
```

## 7. Checklist de Code Review

- [ ] ¿Sigue las convenciones de naming?
- [ ] ¿Está la lógica de negocio en servicios?
- [ ] ¿Hay logging estructurado?
- [ ] ¿Se manejan errores apropiadamente?
- [ ] ¿Están los imports organizados?
- [ ] ¿Es el código legible y mantenible?
- [ ] ¿Hay tests para la funcionalidad?
- [ ] ¿Se siguen los principios DRY y ETC?

---

**Recuerda**: El código se escribe una vez pero se lee muchas veces. Prioriza la claridad y mantenibilidad.
