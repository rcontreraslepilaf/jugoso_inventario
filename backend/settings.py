from pathlib import Path
import os
from dotenv import load_dotenv

# === Rutas base ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === Variables de entorno (.env) ===
# Coloca un archivo .env en BASE_DIR con las claves de DB, debug, etc.
load_dotenv(BASE_DIR / '.env')

# === Seguridad / Debug ===
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

# === Apps instaladas ===
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # REST API
    'rest_framework',

    # Tu app
    'inventario.apps.InventarioConfig',
]

# === Middlewares ===
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# === URLs / WSGI ===
ROOT_URLCONF = 'backend.urls'
WSGI_APPLICATION = 'backend.wsgi.application'

# === Templates ===
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Carpeta global de templates del proyecto:
        'DIRS': [BASE_DIR / 'templates'],
        # También busca templates dentro de cada app (inventario/templates/inventario/)
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# === Base de datos (PostgreSQL por .env; fallback a SQLite en dev local) ===
DB_ENGINE = os.getenv('DB_ENGINE')
if DB_ENGINE:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,                         # ej: django.db.backends.postgresql
            'NAME': os.getenv('DB_NAME', ''),            # ej: inventario_db
            'USER': os.getenv('DB_USER', ''),            # ej: postgres
            'PASSWORD': os.getenv('DB_PASSWORD', ''),    # ej: postgres
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', ''),
        }
    }
else:
    # Fallback para desarrollo si no hay DB real configurada
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# === Validadores (opcional en dev) ===
AUTH_PASSWORD_VALIDATORS = []

# === Localización ===
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# === Archivos estáticos y media ===
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# === DRF (opcional) ===
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# === IDs por defecto ===
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
