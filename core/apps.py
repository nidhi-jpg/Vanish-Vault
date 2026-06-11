from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'VanishVault Core'
    
    def ready(self):
        """Import signals when app is ready"""
        pass
