"""
Django settings for brixacore project.

BrixaCore - Platform Core Infrastructure
Python 3.11 | Django 5.0 | PostgreSQL (production) / SQLite (development)

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-r+=h^phr#!y#h_6q9lsm7hyh4lof503bpy2@#uv0(_a)aobwtn")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# CSRF Settings for Django 4.0+
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "django_htmx",
    # BrixaCore apps
    "core.apps.CoreConfig",
    "identity.apps.IdentityConfig",
    "audit.apps.AuditConfig",
    "lifecycle.apps.LifecycleConfig",
    "numbering.apps.NumberingConfig",
    "backup.apps.BackupConfig",
    "files.apps.FilesConfig",
    "app_shell.apps.AppShellConfig",
    "value_lists.apps.ValueListsConfig",
    "django_extensions",
    # Base Modules (Lite V3.1)
    "people.apps.PeopleConfig",
    "products.apps.ProductsConfig",
    "clients.apps.ClientsConfig",
    "contacts.apps.ContactsConfig",
    "addresses.apps.AddressesConfig",
    "phones.apps.PhonesConfig",
    "emails.apps.EmailsConfig",
    "notes.apps.NotesConfig",
    "documents.apps.DocumentsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "audit.middleware.AuditMiddleware",
    "identity.middleware.RolePermissionMiddleware",
]

ROOT_URLCONF = "platform_core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.branding",
            ],
        },
    },
]

WSGI_APPLICATION = "platform_core.wsgi.application"


# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
# PostgreSQL (production)

from django.core.exceptions import ImproperlyConfigured

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
# PostgreSQL matches production environment

if os.getenv("DB_ENGINE") != "postgresql":
    raise ImproperlyConfigured("Only PostgreSQL is supported. Please set DB_ENGINE=postgresql in your environment.")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "brixacore"),
        "USER": os.getenv("DB_USER", "brixacore"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (user-uploaded files)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
# Note: BrixaCore uses UUID PKs in BaseModel, but Django's migration system needs BigAutoField
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth Settings
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

