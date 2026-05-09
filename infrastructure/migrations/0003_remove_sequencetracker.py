# Generated manually — legacy SequenceTracker replaced by numbering app.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0002_alter_striperesponse_raw_response'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SequenceTracker',
        ),
    ]
