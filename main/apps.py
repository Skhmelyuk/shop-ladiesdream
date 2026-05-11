from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import admin_site  # noqa: F401 — ensure admin_site is fully initialized first
        import main.admin
