# Celery Beat Schedule (Periodic Tasks)

from celery.schedules import crontab

# Schedule for periodic tasks
CELERY_BEAT_SCHEDULE = {
    'cleanup-old-sessions': {
        'task': 'app.workers.celery_app.cleanup_old_sessions_task',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}
