import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citing_retracted.settings')

app = Celery('citing_retracted')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'refresh-retracted-papers-daily': {
        'task': 'papers.tasks.refresh_retracted_papers',
        'schedule': 13.0 * 60 * 60,  # 8 AM EST = 1 PM UTC (13:00)
        'options': {'queue': 'default'}
    },
    'refresh-citations-daily': {
        'task': 'papers.tasks.refresh_citations',
        'schedule': 13.5 * 60 * 60,  # 8:30 AM EST = 1:30 PM UTC (13:30) - stagger by 30 minutes
        'options': {'queue': 'default'}
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 