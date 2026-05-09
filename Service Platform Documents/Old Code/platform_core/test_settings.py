from .settings import *



# Remove django_extensions if present to avoid test env errors
if 'django_extensions' in INSTALLED_APPS:
    INSTALLED_APPS.remove('django_extensions')

