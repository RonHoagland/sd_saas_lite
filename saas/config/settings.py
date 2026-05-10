# config/settings.py
# Assembled from:
#   Technical Architecture V2, Sections 3, 4, 6, 8, 10
#   Database Specification V2, Sections 4, 13
#   Multi-Tenancy Specification V1, Section 5

from csp.constants import NONCE
from decouple import config, Csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Core ─────────────────────────────────────────────────────────────────────

SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Field-level encryption key (32-byte symmetric key, base64url-encoded).
# Production: inject from secrets vault. Local dev: auto-generated into .env
# on first encryption operation if missing. See config/encryption.py.
FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY', default='')

# ─── Application Definition ───────────────────────────────────────────────────

INSTALLED_APPS = [
    # Staff admin (must be before django.contrib.admin for custom AdminSite)
    'staff.apps.StaffConfig',

    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # ServizDesk SDTA apps — Core frameworks (load first, other apps depend on these)
    'numbering.apps.NumberingConfig',
    'lifecycle.apps.LifecycleConfig',
    'value_lists.apps.ValueListsConfig',
    'notes.apps.NotesConfig',
    'documents.apps.DocumentsConfig',

    # ServizDesk SDTA apps — Domain modules
    'users.apps.UsersConfig',
    'crm.apps.CrmConfig',
    'inventory.apps.InventoryConfig',
    'warehouse.apps.WarehouseConfig',
    'procurement.apps.ProcurementConfig',
    'service.apps.ServiceConfig',
    'maintenance.apps.MaintenanceConfig',
    'tasks.apps.TasksConfig',
    'workforce.apps.WorkforceConfig',
    'automation.apps.AutomationConfig',
    'fleet.apps.FleetConfig',
    'infrastructure.apps.InfrastructureConfig',

    # Third-party
    'rest_framework',
    'django_filters',
    'django_celery_results',
    'axes',
    'csp',
]

# Custom User model — tenant employees.
# Source: Data Models V6, Section 1.1.
# StaffUser (staff/models.py) is NOT AUTH_USER_MODEL — it authenticates via
# StaffUserBackend which handles its own user retrieval independently.
AUTH_USER_MODEL = 'users.User'

# auth.W004 — Django warns that USERNAME_FIELD is not globally unique.
# Intentional: ServizDesk uses workspace-scoped uniqueness (tenant_id + username)
# per LITE_DECISIONS.md §N. The custom splash_login_view resolves the tenant
# from the Workspace form field before authenticating, so global uniqueness is
# not required.
SILENCED_SYSTEM_CHECKS = ['auth.W004']

# Authentication backends.
# StaffUserBackend first so /admin/ logins resolve to StaffUser.
# ModelBackend retained for Django internals (permissions framework).
AUTHENTICATION_BACKENDS = [
    'staff.backends.StaffUserBackend',
    'api.backends.SchemaSafeSessionBackend',
    'django.contrib.auth.backends.ModelBackend',
    'axes.backends.AxesStandaloneBackend',  # django-axes lockout enforcement
]

# ─── Middleware ────────────────────────────────────────────────────────────────
# Order is critical.
# AdminBypassMiddleware before TenantMiddleware so /admin/ paths bypass tenant scoping.

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'users.session_audit.SessionIdleTimeoutMiddleware',
    'config.middleware.AdminBypassMiddleware',       # /admin/ bypass — before TenantMiddleware
    'config.middleware.TenantMiddleware',            # tenant context for all other requests
    'config.middleware.InternalAPIKeyMiddleware',    # /internal/api/ key validation
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',                  # Content-Security-Policy
    'axes.middleware.AxesMiddleware',                # login lockout
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.servizdesk_ui',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ─── Database ─────────────────────────────────────────────────────────────────
# Source: Database Specification V2, Section 4.2.
# SQLite is strictly prohibited in all environments.

DATABASES = {
    # Runtime application user — subject to RLS.
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('SDTA_DB_NAME', default='serviz_db'),
        'USER': config('SDTA_DB_USER', default='djangouser'),
        'PASSWORD': config('SDTA_DB_PASSWORD'),
        'HOST': config('SDTA_DB_HOST', default='localhost'),
        'PORT': config('SDTA_DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': config('SDTA_DB_SSLMODE', default='require'),
        },
        'CONN_MAX_AGE': 60,
    },
    # Worker alias — sdta_migration user, BYPASSRLS=TRUE.
    # Used by: background tasks (cross-tenant reads), Django admin (staff access),
    #          rolling retention purge tasks.
    # Source: Database Specification V2, Section 4.2; Multi-Tenancy Spec V1, Section 7.
    'worker': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('SDTA_DB_NAME', default='serviz_db'),
        'USER': config('SDTA_MIGRATION_DB_USER', default='djangouser'),
        'PASSWORD': config('SDTA_MIGRATION_DB_PASSWORD'),
        'HOST': config('SDTA_DB_HOST', default='localhost'),
        'PORT': config('SDTA_DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': config('SDTA_DB_SSLMODE', default='require'),
        },
        'CONN_MAX_AGE': 60,
        # In tests, route worker queries to the same physical DB as default.
        # This lets TenantModelAdmin (which uses .using('worker')) see data
        # created via the default alias without requiring two real DB users.
        'TEST': {
            'MIRROR': 'default',
        },
    },
}

# ─── Password Validation ───────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Override Django's default 3-day reset window.
# Source: Technical Architecture V2, Section 8.1; Multi-Tenancy Spec V1, Section 9.
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours

# ─── Internationalisation ──────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'          # All timestamps stored in UTC. Display TZ from TenantPreference.
USE_I18N = True
USE_TZ = True

# ─── Static & Media ───────────────────────────────────────────────────────────

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Bump when site.css (or any page stylesheet linked from templates) changes.
# Used as a `?v=` cache-buster on <link> tags in base.html and splash_login.html.
SERVIZDESK_UI_ASSET_VERSION = '32'

# App version displayed on the login splash. Bump on every meaningful release.
# Format: MAJOR.MINOR.PATCH. Started 2026-04-24 at 0.11.1 (post Phase 1.1 shell rewrite).
SERVIZDESK_VERSION = '0.11.1'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'   # Local dev only. Production uses DigitalOcean Spaces.

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── File Storage (S3 / DigitalOcean Spaces) ─────────────────────────────────
# Source: Technical Architecture V2, Section 5.
# Production: DigitalOcean Spaces (S3-compatible).
# Local dev: falls back to MEDIA_ROOT filesystem when SDTA_STORAGE_BACKEND='local'.
#
# File keys follow the pattern:
#   {tenant_id}/{entity_type}/{entity_id}/{uuid}_{original_filename}
#
# Presigned URLs expire after SDTA_PRESIGNED_URL_EXPIRY seconds.

SDTA_STORAGE_BACKEND = config('SDTA_STORAGE_BACKEND', default='local')  # 'local' | 's3'

# S3-compatible settings (used when SDTA_STORAGE_BACKEND='s3')
SDTA_S3_ACCESS_KEY = config('SDTA_S3_ACCESS_KEY', default='')
SDTA_S3_SECRET_KEY = config('SDTA_S3_SECRET_KEY', default='')
SDTA_S3_BUCKET_NAME = config('SDTA_S3_BUCKET_NAME', default='servizdesk-files')
SDTA_S3_REGION = config('SDTA_S3_REGION', default='nyc3')
SDTA_S3_ENDPOINT_URL = config(
    'SDTA_S3_ENDPOINT_URL',
    default='https://nyc3.digitaloceanspaces.com',
)

# File upload constraints.
#
# File Upload Specification V1 §3.1 names 100 MB as the SDTA-tier ceiling,
# but the platform default is intentionally conservative — a single bad
# upload at 100 MB can quickly eat a tenant's storage quota. Operators that
# need the full ceiling override SDTA_MAX_FILE_SIZE_MB=100 in their .env.
SDTA_MAX_FILE_SIZE_MB = config('SDTA_MAX_FILE_SIZE_MB', default=25, cast=int)
SDTA_ALLOWED_MIME_TYPES = [
    # Documents
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'text/csv',
    # Images
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/svg+xml',
]

# Presigned URL expiry (seconds).
#
# File Upload Specification V1 §5.3 mandates 15 minutes (900s). Short-lived
# URLs are essential because the URL is the entire authentication for the
# download — once issued, anyone with the URL can fetch the file until it
# expires. Override only when you have a specific operational reason.
SDTA_PRESIGNED_URL_EXPIRY = config('SDTA_PRESIGNED_URL_EXPIRY', default=900, cast=int)

# ─── Session & Security Cookies ───────────────────────────────────────────────
# Source: Technical Architecture V2, Section 8.1.
#
# Browsers will not store or send "Secure" session cookies on plain http://.
# That looks like a logout after every refresh or runserver auto-reload.
#
# When DEBUG is True we default to HTTP-friendly cookies so .env copies that set
# SESSION_COOKIE_SECURE=True (production parity) do not break local runserver.
# Override with FORCE_SECURE_COOKIES=True only if you use HTTPS locally (e.g. mkcert).
#
# When DEBUG is False, Secure defaults to True; set SDTA_USE_HTTP_COOKIES=True only
# for private HTTP staging (never on the public internet).

FORCE_SECURE_COOKIES = config('FORCE_SECURE_COOKIES', default=False, cast=bool)
SDTA_USE_HTTP_COOKIES = config(
    'SDTA_USE_HTTP_COOKIES',
    default=DEBUG,
    cast=bool,
)

if SDTA_USE_HTTP_COOKIES and not FORCE_SECURE_COOKIES:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Django session cookie lifetime — generous ceiling; sliding idle timeout for
# auth UX is enforced in SessionIdleTimeoutMiddleware via TenantPreference.session_timeout_minutes.
SESSION_COOKIE_AGE = config(
    'SDTA_SESSION_COOKIE_MAX_AGE',
    default=86400 * 7,
    cast=int,
)
SESSION_SAVE_EVERY_REQUEST = True

# Fallback idle allowance (seconds) when TenantPreference has no session_timeout_minutes.
SDTA_SESSION_IDLE_TIMEOUT_SECONDS = config(
    'SDTA_SESSION_IDLE_TIMEOUT_SECONDS',
    default=1800,
    cast=int,
)
CSRF_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0 if DEBUG else 31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False if DEBUG else True, cast=bool)
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

# ─── Django REST Framework ───────────────────────────────────────────────────
# Source: Internal API Specification V1.

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.StandardPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'standard': '100/minute',
        'uploads': '20/minute',
    },
    'EXCEPTION_HANDLER': 'api.exceptions.sdta_exception_handler',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],
}

# ─── Celery ───────────────────────────────────────────────────────────────────
# Source: Technical Architecture V2, Section 6.5.

CELERY_BROKER_URL = config('CELERY_BROKER_URL')   # rediss://:pass@host:6379/0 in production
CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_EXTENDED = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# ─── django-axes (Login Lockout) ──────────────────────────────────────────────
# Source: Technical Architecture V2, Section 8.7.
# Lock after 5 failed attempts. Auto-unlock after 30 minutes.

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 0.5        # 30 minutes in hours
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']

# ─── django-csp ───────────────────────────────────────────────────────────────
# Source: Technical Architecture V2, Section 8.8.
# Per-request nonce generation — must NOT be replaced with a static Nginx header.
#
# django-csp 4.x API: use CONTENT_SECURITY_POLICY dict instead of the old
# CSP_* tuple settings that were dropped in 4.0.
# Use csp.constants.NONCE (not the string 'nonce') so CSPMiddleware injects
# 'nonce-VALUE' into the header when {{ request.csp_nonce }} is evaluated.

CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ["'self'"],
        # Bootstrap + Lucide are vendored into static/vendor/ (LITE_DECISIONS.md §M),
        # so script-src needs only 'self' + the nonce for inline shell scripts.
        # Stripe is Plus+ (not used in Lite templates) but kept whitelisted ahead of
        # the Plus build; harmless in Lite where no <script> references it.
        'script-src':  ["'self'", NONCE, 'https://js.stripe.com'],
        'style-src':   ["'self'", "'unsafe-inline'"],
        'img-src':     ["'self'", 'data:', 'https:'],
        'font-src':    ["'self'"],
        'frame-src':   ['https://js.stripe.com'],
        # Pusher (real-time, Plus+) and Stripe API remain allowed for future tiers.
        'connect-src': ["'self'", 'https://api.stripe.com', 'wss://ws.pusherapp.com'],
    },
}

# ─── Stripe ───────────────────────────────────────────────────────────────────

STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# ─── Internal API ─────────────────────────────────────────────────────────────

INTERNAL_API_KEY = config('INTERNAL_API_KEY', default='')
SDTA_INTERNAL_BASE_URL = config('SDTA_INTERNAL_BASE_URL', default='http://localhost:8001')

# ─── Pusher ───────────────────────────────────────────────────────────────────

PUSHER_APP_ID = config('PUSHER_APP_ID', default='')
PUSHER_KEY = config('PUSHER_KEY', default='')
PUSHER_SECRET = config('PUSHER_SECRET', default='')
PUSHER_CLUSTER = config('PUSHER_CLUSTER', default='')
