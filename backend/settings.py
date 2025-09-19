from pathlib import Path; import os
BASE_DIR=Path(__file__).resolve().parent.parent
SECRET_KEY='dev-secret'; DEBUG=True; ALLOWED_HOSTS=['*']
INSTALLED_APPS=['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','rest_framework','inventario']
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}
LANGUAGE_CODE='es-cl'; TIME_ZONE='America/Santiago'; USE_I18N=True; USE_TZ=True
STATIC_URL='static/'; DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
