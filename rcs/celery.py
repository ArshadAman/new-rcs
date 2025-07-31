import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rcs.settings')

app = Celery('rcs')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
