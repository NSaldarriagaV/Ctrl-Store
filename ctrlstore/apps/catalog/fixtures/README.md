# Fixtures de Demostración - Ctrl+Store

## Productos de Demostración Disponibles

### `demo_products.json` (Original)
Productos básicos originales del sistema:
- Laptop Gamer ASUS ROG
- MacBook Pro 16"
- PlayStation 5
- Xbox Series X
- Mouse Logitech G502
- Teclado Mecánico Redragon
- Monitor LG UltraWide 34"
- Monitor Gamer Samsung Odyssey

### `demo_products_electronics.json` (Nuevo)
Productos electrónicos completos con especificaciones técnicas:
- **iPhone 15 Pro Max** - $1,299.99 (Especificaciones móviles completas)
- **MacBook Pro 16" M3 Max** - $3,499.99 (Especificaciones de laptop)
- **PlayStation 5 Pro** - $699.99 (Especificaciones de consola gaming)
- **Samsung Odyssey G7 32"** - $899.99 (Especificaciones de monitor gaming)
- **Logitech MX Master 3S** - $99.99 (Especificaciones de periférico)
- **ASUS TUF Gaming A15** - $1,399.99 (Laptop gaming completo)
- **Xbox Series X** - $499.99 (Consola con especificaciones completas)

## Cómo Cargar los Fixtures

### Productos Originales
```bash
python manage.py loaddata demo_products.json
```

### Productos Electrónicos Completos
```bash
python manage.py loaddata demo_products_electronics.json
```

### Ambos (Recomendado para demostración completa)
```bash
python manage.py loaddata demo_products.json
python manage.py loaddata demo_products_electronics.json
```

## Características de los Productos de Demostración

### ✅ Especificaciones Técnicas Completas
- Información básica (marca, modelo, precio)
- Especificaciones por categoría (móviles, PC, gaming)
- Características adicionales en JSON
- Stock y estado configurados

### ✅ Categorías Utilizadas
- **Laptops** (categoria: 1) - Para laptops y computadores portátiles
- **Consolas** (categoria: 2) - Para consolas de videojuegos
- **Accesorios** (categoria: 3) - Para periféricos y accesorios
- **Monitores** (categoria: 4) - Para pantallas y monitores

### ✅ Estados de Productos
- **Activos**: Todos los productos están activos
- **Destacados**: iPhone, MacBook Pro, PS5 Pro, Xbox Series X, Samsung Odyssey
- **Stock**: Cantidades realistas (8-35 unidades)

## Notas Importantes

1. **IDs Únicos**: Los nuevos productos usan IDs 100+ para evitar conflictos
2. **Compatibilidad**: Funciona con las categorías existentes
3. **Especificaciones**: Cada producto tiene especificaciones técnicas completas
4. **Realismo**: Precios y especificaciones basados en productos reales

## Para Desarrolladores

Si necesitas agregar más productos de demostración:
1. Usa IDs únicos (200+)
2. Asigna a categorías existentes (1-4)
3. Incluye especificaciones completas
4. Mantén precios realistas
5. Configura stock y estado apropiados

