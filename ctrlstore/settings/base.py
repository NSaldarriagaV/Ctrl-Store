from pathlib import Path
import os
import environ
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ✅ Carga .env solo si existe (no pisa variables ya presentes en el entorno Docker)
env = environ.Env()
env_file_docker = BASE_DIR / ".env.docker"
env_file_local = BASE_DIR / ".env"
if env_file_docker.exists():
    environ.Env.read_env(str(env_file_docker))
elif env_file_local.exists():
    environ.Env.read_env(str(env_file_local))

# ────────────────────────────────────────────────────────────────────────────────
# Core
# ────────────────────────────────────────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY", default="dev-only-secret")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

# i18n / tz
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

LANGUAGES = (
    ("es", _("Español")),
    ("en", _("English")),
)

INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Apps del proyecto
    "ctrlstore.apps.authx",
    "ctrlstore.apps.catalog",
    "ctrlstore.apps.cart",
    "ctrlstore.apps.order",
    "ctrlstore.apps.payment",
    "ctrlstore.apps.billing",
    "ctrlstore.apps.analytics",
    "ctrlstore.apps.common",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ctrlstore.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "ctrlstore.apps.cart.context_processors.cart_info",
                "ctrlstore.apps.common.context_processors.weather_info",
            ],
        },
    },
]

WSGI_APPLICATION = "ctrlstore.wsgi.application"

# ────────────────────────────────────────────────────────────────────────────────
# Base de datos (prioriza SIEMPRE variables de entorno; fallback a SQLite)
# Coerción explícita a str y 'or' para evitar valores vacíos.
# ────────────────────────────────────────────────────────────────────────────────
ENGINE = str(os.environ.get("DB_ENGINE") or "django.db.backends.sqlite3")
NAME = str(os.environ.get("DB_NAME") or (BASE_DIR / "db.sqlite3"))
USER = str(os.environ.get("DB_USER") or "")
PASSWORD = str(os.environ.get("DB_PASSWORD") or "")
HOST = str(os.environ.get("DB_HOST") or "")
PORT = str(os.environ.get("DB_PORT") or "")

# Debug opcional de conexión (solo si exportas DEBUG_DB=1)
if os.environ.get("DEBUG_DB") == "1":
    print("==> [DEBUG_DB] ENGINE:", ENGINE)
    print("==> [DEBUG_DB] NAME:", NAME)
    print("==> [DEBUG_DB] HOST:", HOST, "PORT:", PORT, "USER:", USER)

DATABASES = {
    "default": {
        "ENGINE": ENGINE,
        "NAME": NAME,
        "USER": USER,
        "PASSWORD": PASSWORD,
        "HOST": HOST,
        "PORT": PORT,
    }
}

# ────────────────────────────────────────────────────────────────────────────────
# Password validators
# ────────────────────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ────────────────────────────────────────────────────────────────────────────────
# Static & media
# ────────────────────────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Usuario personalizado y auth redirects
AUTH_USER_MODEL = "authx.User"
LOGIN_URL = "authx:login"
LOGIN_REDIRECT_URL = "catalog:product_list"
LOGOUT_REDIRECT_URL = "catalog:product_list"

# Locales
LOCALE_PATHS = [BASE_DIR / "locale"]
