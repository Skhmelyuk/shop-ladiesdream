import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')

app = Celery('shop')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-novaposhta-every-night': {
        'task': 'orders.tasks.sync_novaposhta_data',
        'schedule': crontab(hour=3, minute=0), # Щодня о 3:00 ночі
    },
    'cancel-unpaid-orders-hourly': {
        'task': 'orders.tasks.cancel_unpaid_orders',
        'schedule': crontab(minute=0), # Кожну годину
    },
    'send-abandoned-cart-reminders-every-30-min': {
        'task': 'orders.tasks.send_abandoned_cart_reminders',
        'schedule': crontab(minute='*/30'), # Кожні 30 хвилин
    },
    'send-daily-sales-report-at-21-00': {
        'task': 'orders.tasks.send_daily_sales_report',
        'schedule': crontab(hour=21, minute=0), # Щодня о 21:00
    },
    'send-weekly-sales-report-monday-09-00': {
        'task': 'orders.tasks.send_weekly_sales_report',
        'schedule': crontab(day_of_week=1, hour=9, minute=0), # Щотижня в понеділок о 9:00 ранку
    },
    'clear-expired-sessions-and-carts-weekly': {
        'task': 'orders.tasks.clear_expired_sessions_and_carts',
        'schedule': crontab(day_of_week=0, hour=3, minute=0), # Щотижня в неділю о 3:00 ночі
    },
    'send-birthday-greetings-daily-10-00': {
        'task': 'orders.tasks.send_birthday_greetings',
        'schedule': crontab(hour=10, minute=0), # Щодня о 10:00 ранку
    },
    'send-winback-campaign-daily-11-00': {
        'task': 'orders.tasks.send_winback_campaign',
        'schedule': crontab(hour=11, minute=0), # Щодня о 11:00 ранку
    },
    'track-novaposhta-parcels-every-2-hours': {
        'task': 'orders.tasks.track_novaposhta_parcels',
        'schedule': crontab(hour='*/2', minute=0), # Кожні 2 години
    },
    'reconcile-online-payments-nightly': {
        'task': 'orders.tasks.reconcile_online_payments',
        'schedule': crontab(hour=0, minute=30), # Щоночі о 00:30
    },
    'generate-xml-feeds-nightly': {
        'task': 'main.tasks.generate_xml_feeds',
        'schedule': crontab(hour=2, minute=0), # Щоночі о 02:00
    },
}

