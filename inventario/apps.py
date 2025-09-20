from django.apps import AppConfig
import importlib

class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario'

    def ready(self):
        importlib.import_module('inventario.signals')
