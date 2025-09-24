Jugoso Market – Inventario y POS

Aplicación Django para gestionar categorías, proveedores, productos, compras y ventas (POS).
Tema claro/oscuro con Tailwind (CDN) y UX pensada para teclado.

Requisitos

Python 3.12 o 3.13

Pip

PostgreSQL 14+ (requerido por la evaluación)

SQLite solo como alternativa local para pruebas rápidas.

Instalación (PostgreSQL por defecto)
Windows (PowerShell)
# 1) Clonar
git clone <URL_DEL_REPO>
cd jugoso_inventario

# 2) Entorno virtual
python -m venv .venv
. .venv\Scripts\Activate.ps1

# 3) Dependencias
pip install -r requirements.txt

# 4) Variables de entorno
copy .env.example .env
# Abre .env y configura PostgreSQL:
# DEBUG=True
# SECRET_KEY=django-insecure-cambia_esta_clave
# DB_ENGINE=postgres
# DB_NAME=jugoso_db
# DB_USER=postgres
# DB_PASSWORD=TU_PASSWORD
# DB_HOST=localhost
# DB_PORT=5432

# 5) Migraciones + superusuario
python manage.py migrate
python manage.py createsuperuser

# 6) Ejecutar
python manage.py runserver

macOS / Linux
git clone <URL_DEL_REPO>
cd jugoso_inventario

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edita .env con tus credenciales de PostgreSQL (ver bloque de arriba)

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver


Notas

Verifica que el servicio de PostgreSQL esté iniciado.

Si solo quieres probar sin PostgreSQL, en .env cambia DB_ENGINE=sqlite
(pero no cumple el requisito de la evaluación).

Cumplimiento de la evaluación
Modelos exigidos por la pauta

Categoria (id, nombre único, descripcion opcional)

Proveedor (id, razon_social/nombre, rut, email, telefono)

Bodega (id, nombre, ubicacion)

Producto (id, sku/codigo único, nombre, categoria FK, proveedor FK, precio, stock_actual)

Movimiento (id, producto FK, bodega FK, tipo: ENTRADA/SALIDA/MERMA, cantidad, fecha, observacion)

Estado actual del proyecto

Incluye: Categoria, Proveedor, Producto.

Incluye: Compra (equivalente a ENTRADA) y Venta (equivalente a SALIDA).

Pendiente para 100% de alineación: Bodega y Movimiento (incluyendo MERMA).

Si se mantiene el modelo actual, se documenta equivalencia Compra ↔ Entrada y Venta ↔ Salida;
no obstante, faltaría MERMA y Bodega para cumplir íntegramente la pauta.

Admin de Django

Modelos registrados en admin.py.

Producto personalizado con list_display, search_fields, list_filter.

Se adjuntan capturas en docs/evidencias/.

CRUD y reglas

CRUD completo para Producto y Proveedor (crear, listar, detalle, editar, eliminar).

Stock:

Compra incrementa stock (Entrada).

Venta descuenta stock (Salida) sin permitir negativos.

(Pendiente) Merma: restar stock sin permitir negativos (lo cubrirá el modelo Movimiento al integrarse).

Rutas principales

/categorias/, /proveedores/, /productos/

/compras/ (Entrada)

/ventas/ (Salida / POS)

Al agregar Bodega y Movimiento: /bodegas/, /movimientos/
y vista/endpoint con histórico por producto.

Evidencias (capturas)

En docs/evidencias/:

migraciones.png – migraciones aplicadas sin errores.

dependencias.png – dependencias instaladas.

(Sugerido) captura de tablas creadas en PostgreSQL (psql o cliente GUI).

Base de datos

Este repo está preparado para PostgreSQL por defecto mediante .env.
Variables mínimas en .env:

DEBUG=True
SECRET_KEY=django-insecure-cambia_esta_clave

# PostgreSQL (recomendado por la pauta)
DB_ENGINE=postgres
DB_NAME=jugoso_db
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD
DB_HOST=localhost
DB_PORT=5432


Alternativa local (no recomendada para la evaluación):
DB_ENGINE=sqlite (usa db.sqlite3 sin configurar credenciales).

Funcionalidades

Categorías: CRUD

Proveedores: CRUD

Productos: CRUD con codigo (SKU), precio, stock, stock_minimo, activo

Compras: carga de ítems (incrementa stock)

POS (Ventas):

Selector y autocompletado por nombre/código

Cálculo de subtotales y total en vivo

Descuento de stock al guardar (sin negativos)

Reporte: productos con stock bajo

Evidencias en docs/evidencias/

Estructura
inventario/           # App principal
  models.py
  views.py
  forms.py
templates/inventario/ # Plantillas
  base.html
  compra_nueva.html
  pos_venta.html
  ...
backend/              # settings/urls/wsgi
docs/evidencias/      # imágenes para el informe

Flujo sugerido

Crear categorías y proveedores

Crear productos (el código SKU puede autogenerarse si lo dejas vacío)

Registrar compras (opcional) para subir stock

Vender en POS:

Buscar por nombre/código (autocompletar)

Agregar líneas, ajustar cantidades/precio

Guardar (descuenta stock)

Comandos útiles
# Crear migraciones tras cambios en modelos
python manage.py makemigrations
python manage.py migrate

# Crear usuario admin
python manage.py createsuperuser

# Recolectar estáticos (si los usas en despliegue)
python manage.py collectstatic

Troubleshooting

PowerShell no ejecuta Activate.ps1

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .venv\Scripts\Activate.ps1


PostgreSQL no arranca / reinicio del servicio (Windows, admin)

sc.exe query postgresql-x64-17
sc.exe start postgresql-x64-17
sc.exe stop postgresql-x64-17


Revisa logs en C:\Program Files\PostgreSQL\17\data\log\.

Buenas prácticas del repo

No versionamos:

db.sqlite3

__pycache__/, *.pyc

datos reales en .env (usa .env.example)

La documentación y evidencias viven en docs/.

Autor

Richard Contreras
Contacto: rcontreraslepilaf@gmail.com