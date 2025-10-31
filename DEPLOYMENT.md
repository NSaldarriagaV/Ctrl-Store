## Despliegue con Docker en GCP

### Requisitos
- Docker / Docker Compose
- Cuenta en GCP (proyecto creado)
- VM (Compute Engine) o Cloud Run + Container Registry/Artifact Registry

### Docker local
1. Construir imagen
   ```bash
   docker build -t ctrlstore:latest .
   ```
2. Ejecutar (ejemplo con sqlite)
   ```bash
   docker run -p 8000:8000 --env-file .env.prod ctrlstore:latest
   ```

### Variables de entorno (ejemplo .env.prod)
```
DJANGO_SETTINGS_MODULE=ctrlstore.settings.prod
SECRET_KEY=change-me
ALLOWED_HOSTS=*
DATABASE_URL=postgres://user:pass@host:5432/db
LANGUAGE_CODE=es
TIME_ZONE=America/Bogota
``` 

### Pasos en GCP (VM)
1. Crear VM Ubuntu y abrir puertos 80/443
2. Instalar Docker y docker-compose
3. Copiar .env.prod y docker-compose.yml
4. Levantar stack: `docker compose up -d`
5. Configurar Nginx (reverse proxy) y certificado (Caddy/Certbot)

### Cloud Run (alternativa)
1. Subir imagen a Artifact Registry
2. Crear servicio en Cloud Run (port 8000)
3. Configurar variables de entorno y VPC para DB

### Dominio .tk (opcional)
- Apuntar dominio al IP público (A record) o al balanceador

### Healthcheck y logs
- Exponer `/healthz` simple
- Enviar logs a stdout (capturados por plataforma)



