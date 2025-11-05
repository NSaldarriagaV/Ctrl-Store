### HU28 – Inversión de dependencias para reportes (PDF/Excel)

**ID:** #39  
**Fecha de implementación:** 2025-11-04  
**Responsable:** Nicolás Saldarriaga  
**Aplicación:** `authx` / `order`

---

## 🧠 Descripción

Como **administrador**, quiero **descargar reportes en PDF o Excel** desde el sistema para poder **compartirlos fácilmente**.  
Esta historia de usuario introdujo el principio de **inversión de dependencias (Dependency Inversion)**, desacoplando la lógica de generación de reportes del formato específico (CSV, PDF o Excel).

---

## 🎯 Objetivos de la HU

- Permitir la descarga de reportes de ventas en múltiples formatos: **CSV**, **PDF** y **Excel**.  
- Implementar una arquitectura extensible y desacoplada, aplicando el **principio de inversión de dependencias (D de SOLID)**.  
- Facilitar la **realización de pruebas unitarias** sin depender del framework o del formato del archivo.

---

## 🏗️ Arquitectura implementada

### 1. Clases creadas en `ctrlstore/apps/order/reporting.py`

| Clase | Responsabilidad |
|--------|------------------|
| `ReportGenerator` | Clase abstracta base (interfaz) que define el contrato para generar reportes. |
| `CsvReportGenerator` | Implementación concreta para reportes en formato CSV. |
| `PdfReportGenerator` | Implementación concreta para reportes en formato PDF (usando ReportLab). |
| `ExcelReportGenerator` | Implementación concreta para reportes en formato XLSX (usando OpenPyXL). |
| `SalesReportService` | Servicio que construye los datos de ventas (sin conocer el formato final). |

Estas clases siguen el patrón **Estrategia (Strategy Pattern)**, donde el servicio de reportes depende de una **abstracción** (`ReportGenerator`), no de una implementación específica.

---

## ⚙️ Cambios en vistas (`authx/views.py`)

Se reemplazó la antigua vista `AdminSalesExportCSVView` por una nueva clase genérica:

```python
class AdminSalesExportView(AdminRequiredMixin, View):
    """
    Exportación del historial filtrado en CSV / PDF / Excel.
    Usa inversión de dependencias (ReportGenerator).
    """
```

La vista ahora:
- Inyecta dinámicamente el generador correcto (`CsvReportGenerator`, `PdfReportGenerator` o `ExcelReportGenerator`) según el parámetro `?format=`.
- Construye el archivo usando `SalesReportService`.
- Retorna el archivo con el MIME-Type y extensión adecuados.

### Ejemplo de rutas soportadas:
```
/admin/sales/export/?format=csv
/admin/sales/export/?format=pdf
/admin/sales/export/?format=excel
```

---

## 🧪 Pruebas Unitarias

Archivo: `ctrlstore/apps/order/test_sales_report_service.py`

### Objetivo de la prueba
Validar que el servicio `SalesReportService`:

- Construye correctamente las filas de datos desde órdenes reales.
- Funciona independientemente del formato de salida (gracias a la interfaz `ReportGenerator`).

### Uso de fixtures
Se creó un `order_factory` en `conftest.py` que genera:

- Usuario único (`User`) con email aleatorio.  
- Categoría y producto únicos (`Category`, `Product`).  
- Orden (`Order`) y sus ítems (`OrderItem`) con valores consistentes (`line_total = precio * cantidad`).

### Resultado
Tras ajustar constraints de unicidad (`email`, `category.name`) y valores no nulos (`line_total`), todas las pruebas pasaron exitosamente ✅.

---

## 🧩 Dependencias agregadas

| Librería | Propósito |
|-----------|------------|
| `reportlab` | Generación de archivos PDF. |
| `openpyxl` | Generación de archivos Excel (.xlsx). |
| `pytest-django` | Ejecución de pruebas unitarias en Django. |

**Instalación:**
```bash
pip install reportlab openpyxl pytest-django
```

---

## 🧭 Resultados

- ✅ **Inversión de dependencias aplicada correctamente.**  
  El servicio `SalesReportService` depende de la abstracción `ReportGenerator`.
- ✅ **Extensibilidad garantizada.**  
  Se pueden agregar nuevos formatos (por ejemplo, JSON o XML) sin modificar el código existente.
- ✅ **Testabilidad mejorada.**  
  Los tests unitarios usan un `FakeReportGenerator` para validar la lógica sin generar archivos reales.
- ✅ **Interfaz de administrador funcional.**  
  Los administradores pueden descargar los reportes directamente desde el panel, en cualquiera de los tres formatos.

---

## 🖼️ Ejemplo visual en el panel admin

En las vistas `AdminSalesHistoryView` y `AdminSalesReportView` se agregaron botones:

```html
<a href="?format=csv" class="btn btn-outline-secondary btn-sm">Descargar CSV</a>
<a href="?format=pdf" class="btn btn-outline-secondary btn-sm">Descargar PDF</a>
<a href="?format=excel" class="btn btn-outline-secondary btn-sm">Descargar Excel</a>
```

Cada botón genera automáticamente el archivo con el formato seleccionado.

---

## 📄 Conclusión

Esta HU implementa el principio de **Dependency Inversion**, haciendo que la generación de reportes dependa de una **interfaz común**, no de clases concretas.

Se logró:
- Un sistema más **modular**, **escalable** y **testeable**.
- Soporte para **múltiples formatos de reporte** desde la misma vista.
- Una base sólida para futuras extensiones (por ejemplo, reportes automáticos por email o gráficos en PDF).

---

**Estado final:** ✅ Completada y verificada  
**Commit asociado:** `feat: implement sales report dependency inversion (HU28)`  
