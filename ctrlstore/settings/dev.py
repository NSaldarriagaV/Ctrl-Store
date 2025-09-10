from .base import *
DEBUG = True
ALLOWED_HOSTS = []
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],   # si usas carpeta global
    "APP_DIRS": True,                   # para cargar templates dentro de apps
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]
    }
}]
