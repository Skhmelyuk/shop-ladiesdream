from django.apps import AppConfig


class DiscountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'discounts'

    def ready(self):
        import discounts.admin
