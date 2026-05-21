from django.apps import AppConfig
from django.db.models.signals import post_migrate


def setup_periodic_tasks(sender, **kwargs):
    try:
        from django_celery_beat.models import PeriodicTask, CrontabSchedule
    except ImportError:
        return
        
    from django.db.utils import OperationalError, ProgrammingError
    from django.utils import timezone
    from shop.celery import app as celery_app
    
    OLD_ENGLISH_NAMES = [
        'sync-novaposhta-every-night',
        'cancel-unpaid-orders-hourly',
        'send-abandoned-cart-reminders-every-30-min',
        'send-daily-sales-report-at-21-00',
        'send-weekly-sales-report-monday-09-00',
        'clear-expired-sessions-and-carts-weekly',
        'send-birthday-greetings-daily-10-00',
        'send-winback-campaign-daily-11-00',
        'track-novaposhta-parcels-every-2-hours',
        'reconcile-online-payments-nightly',
        'generate-xml-feeds-nightly',
    ]
    
    try:
        # Видаляємо застарілі англійські назви задач, якщо вони є в БД
        PeriodicTask.objects.filter(name__in=OLD_ENGLISH_NAMES).delete()
        
        for name, task_info in celery_app.conf.beat_schedule.items():
            schedule = task_info['schedule']
            task = task_info['task']
            
            crontab_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=schedule._orig_minute,
                hour=schedule._orig_hour,
                day_of_week=schedule._orig_day_of_week,
                day_of_month=schedule._orig_day_of_month,
                month_of_year=schedule._orig_month_of_year,
                timezone=timezone.get_current_timezone_name()
            )
            
            PeriodicTask.objects.update_or_create(
                name=name,
                defaults={
                    'crontab': crontab_schedule,
                    'task': task,
                    'description': f"Автоматично імпортовано з celery.py"
                }
            )
    except (OperationalError, ProgrammingError):
        pass


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        import orders.admin
        post_migrate.connect(setup_periodic_tasks, sender=self)

