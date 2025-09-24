Jugoso Inventario — Django + PostgreSQL

Alumno: Richard Contreras
Profesora: Carla Bravo
Asignatura: Back End
Título: Sistema de Inventario en Django
Fecha: 23-09-2025

Sistema de Inventario que gestiona categorías, proveedores, bodegas, productos y movimientos de stock (ENTRADA / SALIDA / MERMA).
La aplicación expone vistas HTML y endpoints abiertos (sin autenticación) con Django REST Framework.

1) Requisitos

Python 3.12

PostgreSQL 17+

pip / venv

2) Instalación rápida
# 1) Crear y activar entorno (Windows PowerShell)
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1

# 2) Instalar dependencias
pip install -r requirements.txt

# 3) Variables de entorno
# Copiar la plantilla y completar credenciales reales
copy .env.example .env
# Editar .env con los datos de tu Postgres

# 4) Migrar la base de datos
python manage.py migrate

# 5) (Opcional) Crear superusuario para /admin
python manage.py createsuperuser

# 6) Ejecutar servidor
python manage.py runserver
# Abrir: http://127.0.0.1:8000/

3) Variables de entorno (.env)

Archivo .env (no se versiona). Usa .env.example como plantilla:

DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=inventario_db
DB_USER=postgres
DB_PASSWORD=__REEMPLAZA_AQUI__
DB_HOST=localhost
DB_PORT=5432

4) Modelos principales

Categoria: id, nombre (único), descripcion (opcional)

Proveedor: id, razon_social, rut, email, telefono

Bodega: id, nombre, ubicacion

Producto: id, sku (único), nombre, categoria (FK), proveedor (FK), precio, stock_actual (default=0)

Movimiento: id, producto (FK), bodega (FK), tipo (ENTRADA/SALIDA/MERMA), cantidad, fecha, observacion

Reglas clave

sku único

SALIDA/MERMA no permiten que el stock quede negativo

ENTRADA suma al stock

5) Admin de Django

Modelos registrados. En Producto se personalizó:

list_display: sku, nombre, categoria, proveedor, precio, stock_actual

search_fields: nombre, sku

list_filter: categoria, proveedor

Acceso: http://127.0.0.1:8000/admin/

6) Endpoints (DRF, abiertos)

Base: http://127.0.0.1:8000/

GET/POST /categorias/

GET/POST /proveedores/

GET/POST /bodegas/

GET/POST /productos/

GET/POST /movimientos/

Histórico de movimientos por producto

GET /productos/<id>/movimientos/

Notas de negocio en API

Crear Movimiento:

tipo = ENTRADA → stock += cantidad

tipo = SALIDA|MERMA → stock -= cantidad (si quedaría negativo → 400 con error)

Validación: cantidad > 0

7) Evidencias (capturas)

Guía de revisión rápida con imágenes en docs/evidencias/:

Tablas en PostgreSQL (\dt)


Servidor corriendo


Admin / Producto (list_display + filtros + búsqueda)
(agregar captura si corresponde)

POST Movimiento ENTRADA (stock sube)
(agregar captura de DRF/Browsable API o Postman)

POST Movimiento SALIDA (rechazo si deja negativo)
(agregar captura con error de validación)

Histórico por producto
(agregar captura de /productos/<id>/movimientos/)

8) Entregables

Código del proyecto (este repositorio)

Evidencias (carpeta docs/evidencias/)

Informe 2–3 páginas en docs/Informe_Sistema_Inventario_Richard_Contreras.docx

README.md (este archivo)

9) Notas de desarrollo

.env no se versiona (ignorado por .gitignore)

Se usa PostgreSQL como motor en backend/settings.py vía variables de entorno

Si DB_ENGINE no está definido, el proyecto puede usar SQLite como fallback (modo desarrollo)

10) Licencia

Uso académico.