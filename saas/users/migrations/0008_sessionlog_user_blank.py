from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_sessionlog_tier_remove_session_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sessionlog",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="sessions",
                to="users.user",
            ),
        ),
    ]
