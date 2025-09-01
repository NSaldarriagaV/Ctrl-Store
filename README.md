# Ctrl-Store

Proyecto e-commerce desarrollado con **Django**.

## Configuración del entorno local

### 1. Clonar el repositorio
```bash
git clone https://github.com/NSaldarriagaV/Ctrl-Store.git
cd Ctrl-Store
```

### 2. Crear un entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

**Solo ejecución:**
```bash
pip install -r requirements.txt
```

**Para desarrollo (incluye black, isort, ruff, mypy):**
```bash
pip install -r requirements-dev.txt
```

### 4. Configurar variable de entorno para usar settings de desarrollo

$env:DJANGO_SETTINGS_MODULE = "ctrlstore.settings.dev"


### 5. Migraciones y base de datos
```bash
python manage.py migrate
```

### 6. Crear superusuario (para usar el admin de Django)
```bash
python manage.py createsuperuser
```

### 7. Correr el servidor
```bash
python manage.py runserver
```

El proyecto estará disponible en:  
[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Datos de demo

Se incluye un fixture con categorías y productos de ejemplo:

```bash
python manage.py loaddata demo_products.json
```
