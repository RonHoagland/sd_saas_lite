# config/celery.py
# Source: Technical Architecture V2, Section 6.5.
#
# Celery application with:
#   - Autodiscovery of tasks in all INSTALLED_APPS.
#   - Task routing to dedicated queues.
#   - Celery Beat schedule for periodic tasks.

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('sdta')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# ═══════════════════════════════════════════════════════════════════════════════
# TASK ROUTING
# ═══════════════════════════════════════════════════════════════════════════════
# Route tasks to dedicated queues so workers can be scaled independently.
#
# Queues:
#   default      — general-purpose (health checks, lightweight tasks)
#   documents    — file processing (virus scans, uploads)
#   maintenance  — periodic cleanup (retention purge, session cleanup)
#
# Workers are started per-queue:
#   celery -A config worker -Q default,documents --concurrency=4
#   celery -A config worker -Q maintenance --concurrency=2

app.conf.task_routes = {
    # Document processing
    'documents.scan_uploaded_file': {'queue': 'documents'},
    'documents.purge_infected_files': {'queue': 'maintenance'},
    'documents.purge_stale_pending': {'queue': 'maintenance'},

    # System maintenance
    'system.retention_purge_audit_logs': {'queue': 'maintenance'},
    'system.retention_purge_sessions': {'queue': 'maintenance'},
    'system.health_check': {'queue': 'default'},
}

# Fallback: unrouted tasks go to the default queue.
app.conf.task_default_queue = 'default'


# ═══════════════════════════════════════════════════════════════════════════════
# CELERY BEAT SCHEDULE (periodic tasks)
# ═══════════════════════════════════════════════════════════════════════════════
# Run with: celery -A config beat --loglevel=info
#
# In production, use a single Beat instance (not multiple) to avoid
# duplicate task dispatches. Use django-celery-beat for DB-backed
# schedules if dynamic scheduling is needed later.

app.conf.beat_schedule = {
    # ── Document cleanup ──────────────────────────────────────────────────

    'purge-infected-files-daily': {
        'task': 'documents.purge_infected_files',
        'schedule': crontab(hour=3, minute=0),  # 3:00 AM UTC daily
        'options': {'queue': 'maintenance'},
    },

    'purge-stale-pending-hourly': {
        'task': 'documents.purge_stale_pending',
        'schedule': crontab(minute=30),  # every hour at :30
        'options': {'queue': 'maintenance'},
    },

    # ── Retention purges ──────────────────────────────────────────────────

    'retention-purge-audit-logs-weekly': {
        'task': 'system.retention_purge_audit_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week='sunday'),  # Sunday 2:00 AM UTC
        'options': {'queue': 'maintenance'},
    },

    'retention-purge-sessions-daily': {
        'task': 'system.retention_purge_sessions',
        'schedule': crontab(hour=4, minute=0),  # 4:00 AM UTC daily
        'options': {'queue': 'maintenance'},
    },

    # ── Health check ──────────────────────────────────────────────────────

    'health-check-every-5-minutes': {
        'task': 'system.health_check',
        'schedule': 300.0,  # every 5 minutes
        'options': {'queue': 'default'},
    },
}
