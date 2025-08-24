from pathlib import Path
from datetime import timedelta
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment (.env)
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-key-please-change")
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = ["*"]  # für Dev; in Produktion einschränken

# slf_backend/settings.py
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost", ".cloudworkstations.dev"]
)

# WICHTIG: ab Django 4.x/5.x müssen hier Schema + Domain rein (und Wildcards sind erlaubt)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://*.cloudworkstations.dev",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
)



INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Drittanbieter
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "channels",

    # Eigene Apps
    "accounts",
    "game",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # muss weit oben stehen
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"  # für Channels/WebSockets

# DB: lokal SQLite, auf Render dann DATABASE_URL (Postgres)
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth: Custom User ---
AUTH_USER_MODEL = "accounts.User"

# --- DRF + JWT (Basis; Endpoints folgen in Schritt 2) ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# --- CORS (Frontend-URLs später präzisieren) ---
CORS_ALLOW_ALL_ORIGINS = True  # Dev. In Prod: CORS_ALLOWED_ORIGINS = ["https://..."]

# --- Channels: InMemory für Dev (Prod -> Redis) ---
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

