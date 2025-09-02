import logging
from django.apps import AppConfig

LOGGER = logging.getLogger("main")

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        from . import signals
