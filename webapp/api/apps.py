from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        import api.signals  # noqa: F401
        from . import db_timing  # noqa: F401 ensures wrapper loads once