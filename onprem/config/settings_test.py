# config/settings_test.py
# Test-specific settings that override production settings.
# Uses the real PostgreSQL instance (same server as service01) so that
# Row-Level Security, multi-role behaviour, and constraint checks are exercised
# against the actual database engine.
#
# Usage (from the service03/ directory):
#   python manage.py test tests --settings=config.settings_test -v 2
#
# For CSP, axes, and RLS on a real DB clone, see PRODUCTION_PARITY_CHECKLIST.md.
#
# Pre-requisites:
#   1. PostgreSQL is running on 127.0.0.1:5432 (service01's server).
#   2. PostgreSQL reachable at SDTA_DB_HOST (defaults below match common local
#      dev: database serviz_db, user djangouser). For RLS split-roles, use
#      scripts/setup_postgres.sql and override env vars.
#   3. Python 3.12 is active (required by Django 6.0).

import os

# ─── Environment variables ────────────────────────────────────────────────────
# Inject defaults before importing production settings so that
# python-decouple's config() calls resolve correctly without a real .env.
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-secret-key-not-for-production-use')
os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')

# PostgreSQL — same credentials as .env (mirrors service01's server)
os.environ.setdefault('SDTA_DB_NAME',               'serviz_db')
os.environ.setdefault('SDTA_DB_USER',               'djangouser')
os.environ.setdefault('SDTA_DB_PASSWORD',           'buddA123')
os.environ.setdefault('SDTA_MIGRATION_DB_USER',     'djangouser')
os.environ.setdefault('SDTA_MIGRATION_DB_PASSWORD', 'buddA123')
os.environ.setdefault('SDTA_DB_HOST',               '127.0.0.1')
os.environ.setdefault('SDTA_DB_PORT',               '5432')
os.environ.setdefault('SDTA_DB_SSLMODE',            'disable')

os.environ.setdefault('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')

# Pull in everything from the production settings
from config.settings import *  # noqa: F401, F403, E402

# ─── PostgreSQL test databases ────────────────────────────────────────────────
# Django creates test_<SDTA_DB_NAME> automatically during `manage.py test`.
# sdta_migration needs CREATEDB privilege (granted in setup_postgres.sql).
# The worker alias mirrors default so both connections hit the same test DB;
# sdta_migration's BYPASSRLS means it sees all rows regardless of RLS policies.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.environ['SDTA_DB_NAME'],
        'USER':     os.environ['SDTA_DB_USER'],
        'PASSWORD': os.environ['SDTA_DB_PASSWORD'],
        'HOST':     os.environ['SDTA_DB_HOST'],
        'PORT':     os.environ['SDTA_DB_PORT'],
        'OPTIONS':  {'sslmode': os.environ['SDTA_DB_SSLMODE']},
    },
    'worker': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.environ['SDTA_DB_NAME'],
        'USER':     os.environ['SDTA_MIGRATION_DB_USER'],
        'PASSWORD': os.environ['SDTA_MIGRATION_DB_PASSWORD'],
        'HOST':     os.environ['SDTA_DB_HOST'],
        'PORT':     os.environ['SDTA_DB_PORT'],
        'OPTIONS':  {'sslmode': os.environ['SDTA_DB_SSLMODE']},
        # Mirror to default: both aliases share the same test database so that
        # TenantModelAdmin queries (.using('worker')) see data created by the
        # default alias within the same test transaction.
        'TEST': {
            'MIRROR': 'default',
        },
    },
}

# ─── Disable django-axes in tests ─────────────────────────────────────────────
AXES_ENABLED = False

# Remove axes backend so force_login() works without hitting axes middleware.
AUTHENTICATION_BACKENDS = [
    'staff.backends.StaffUserBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ─── Speed up password hashing ────────────────────────────────────────────────
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ─── Email backend — suppress all outbound emails ─────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# ─── Remove CSP and Axes from INSTALLED_APPS ──────────────────────────────────
# CSP middleware is not needed during unit tests and axes is disabled above.
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in ('csp', 'axes')]

MIDDLEWARE = [
    mw for mw in MIDDLEWARE
    if not any(x in mw for x in ('csp.middleware', 'axes.middleware'))
]

# ─── Celery — run tasks synchronously in tests ────────────────────────────────
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ─── Logging — silence routine output during tests ───────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {'class': 'logging.NullHandler'},
    },
    'root': {
        'handlers': ['null'],
    },
}
