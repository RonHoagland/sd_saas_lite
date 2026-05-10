# SessionLog: tier snapshot at login; drop redundant session_id (UUID pk is the session record id).

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_per_tenant_username_email_unique"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sessionlog",
            name="session_id",
        ),
        migrations.AddField(
            model_name="sessionlog",
            name="tier_at_login",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Lite", "Lite"),
                    ("Plus", "Plus"),
                    ("Pro", "Pro"),
                    ("Enterprise", "Enterprise"),
                ],
                help_text="Tenant subscription tier at login (immutable snapshot for audits).",
                max_length=12,
            ),
        ),
    ]
