#!/usr/bin/env bash
set -e

echo "==> Variables de entorno detectadas por el contenedor:"
env | grep DB_ || echo "(sin variables DB_)"
echo "==> Fin de impresión de entorno"
echo ""

# ✅ Espera robusta a Postgres (máx 45s)
if [ -n "${DB_HOST}" ]; then
  echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}"
  echo "Esperando a Postgres en ${DB_HOST}:${DB_PORT:-5432}..."
  for i in $(seq 1 45); do
    # si puede abrir el puerto, rompe el bucle
    (echo > /dev/tcp/${DB_HOST}/${DB_PORT:-5432}) >/dev/null 2>&1 && break
    sleep 1
  done
fi

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Collectstatic..."
python manage.py collectstatic --noinput

exec "$@"
