# Dockerfile
FROM python:3.11-slim

# Config global de Python y pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ✅ Paquetes necesarios para PIL/xhtml2pdf + Postgres + Cairo/Pango
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    pkg-config \
    libcairo2 libcairo2-dev \
    libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Configura el directorio de trabajo
WORKDIR /app

# Instala dependencias Python
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Copia todo el código del proyecto
COPY . /app

# Copia y da permisos al entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ✅ Aquí está la línea CLAVE
# Asegura que Django use el settings correcto (evita dummy backend)
ENV DJANGO_SETTINGS_MODULE=ctrlstore.settings.base

ENTRYPOINT ["/entrypoint.sh"]

# Exponer el puerto 8080 que usa Cloud Run
EXPOSE 8080

COPY media /app/media

# Usar gunicorn en lugar de runserver (más estable en producción)
CMD exec gunicorn ctrlstore.wsgi:application --bind :8080 --workers 2 --threads 4 --timeout 0

