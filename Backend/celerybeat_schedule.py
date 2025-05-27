from celery.schedules import crontab
from datetime import timedelta

CELERY_BEAT_SCHEDULE = {
    'send-appointment-reminders-every-hour': {
        'task': 'core.periodic_tasks.periodic_appointment_reminder',
        'schedule': crontab(minute=0, hour='*'),  # every hour
    },
    'send-appointment-followups-every-hour': {
        'task': 'core.periodic_tasks.periodic_appointment_followup',
        'schedule': crontab(minute=10, hour='*'),  # every hour, 10 minutes past
    },
}
