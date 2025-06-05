from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ems.djangoapps.core'
    label = 'core'
    verbose_name = 'Core'

    def ready(self):
        # Import signal handlers
        pass
