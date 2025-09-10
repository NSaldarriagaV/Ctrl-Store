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
.venv\Scripts\Activate
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

### 4. Migraciones y base de datos
```bash
python manage.py migrate
```

### 5. Crear superusuario (para usar el admin de Django)
```bash
python manage.py createsuperuser
```

### 6. Correr el servidor cada vez que se abra el proyecto
```bash
# Configurar variable de entorno para usar settings de desarrollo
$env:DJANGO_SETTINGS_MODULE = "ctrlstore.settings.dev"
# Ejecutar servidor Django
python manage.py runserver
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
python manage.py loaddata complete_catalog.json
```
