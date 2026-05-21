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
    
    TASK_NAMES_MAPPING = {
        'sync-novaposhta-every-night': '🔄 Синхронізація відділень Нової Пошти',
        'cancel-unpaid-orders-hourly': '❌ Скасування неоплачених замовлень',
        'send-abandoned-cart-reminders-every-30-min': '🛒 Нагадування про покинуті кошики',
        'send-daily-sales-report-at-21-00': '📊 Щоденний звіт про продажі',
        'send-weekly-sales-report-monday-09-00': '📈 Тижневий звіт про продажі',
        'clear-expired-sessions-and-carts-weekly': '🧹 Очищення застарілих сесій та кошиків',
        'send-birthday-greetings-daily-10-00': '🎂 Привітання з Днем народження',
        'send-winback-campaign-daily-11-00': '💖 Повернення "сплячих" клієнтів (Win-back)',
        'track-novaposhta-parcels-every-2-hours': '🚚 Автоматичний трекінг ТТН Нової Пошти',
        'reconcile-online-payments-nightly': '💳 Контроль онлайн-оплат (LiqPay/Monobank)',
        'generate-xml-feeds-nightly': '🛍️ Генерація XML-фідів для Google/Facebook',
    }
    
    try:
        for name, task_info in celery_app.conf.beat_schedule.items():
            schedule = task_info['schedule']
            task = task_info['task']
            friendly_name = TASK_NAMES_MAPPING.get(name, name)
            
            # Якщо завдання вже існує зі старою назвою-ідентифікатором, оновлюємо її
            if name != friendly_name:
                if PeriodicTask.objects.filter(name=friendly_name).exists():
                    PeriodicTask.objects.filter(name=name).delete()
                else:
                    PeriodicTask.objects.filter(name=name).update(name=friendly_name)
            
            crontab_schedule, created = CrontabSchedule.objects.get_or_create(
                minute=schedule._orig_minute,
                hour=schedule._orig_hour,
                day_of_week=schedule._orig_day_of_week,
                day_of_month=schedule._orig_day_of_month,
                month_of_year=schedule._orig_month_of_year,
                timezone=timezone.get_current_timezone_name()
            )
            
            PeriodicTask.objects.update_or_create(
                name=friendly_name,
                defaults={
                    'crontab': crontab_schedule,
                    'task': task,
                    'description': f"Автоматично імпортовано з celery.py: {name}"
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

