# Generated manually on 2026-01-25 to allow user deletion with only login records

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='user',
            field=models.ForeignKey(
                blank=True,
                help_text='User (null if authentication failed)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
