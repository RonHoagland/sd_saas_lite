# value_lists/apps.py
from django.apps import AppConfig


class ValueListsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'value_lists'
    verbose_name = 'Value Lists'
