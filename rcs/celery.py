import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rcs.settings')

app = Celery('rcs')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-scheduled-review-emails-daily': {
        'task': 'rcs.orders.tasks.send_scheduled_review_emails',
        'schedule': crontab(hour=0, minute=0),  # runs daily at midnight
    },
    'auto-publish-reviews-daily': {
        'task': 'rcs.reviews.tasks.periodic_auto_publish_reviews',
        'schedule': crontab(hour=1, minute=0),  # runs daily at 1am
    },
}
