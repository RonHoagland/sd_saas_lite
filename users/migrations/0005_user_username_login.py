from django.db import migrations, models


def populate_usernames(apps, schema_editor):
    User = apps.get_model('users', 'User')
    existing = set(
        User.objects.exclude(username__isnull=True).exclude(username='').values_list('username', flat=True)
    )

    for user in User.objects.all().order_by('created_on', 'id'):
        if user.username:
            continue

        base = 'user'
        if user.email:
            base = user.email.split('@', 1)[0] or 'user'
        base = base.lower().strip()[:140] or 'user'

        candidate = base
        counter = 1
        while candidate in existing:
            candidate = f'{base}{counter}'
            counter += 1

        user.username = candidate
        user.save(update_fields=['username'])
        existing.add(candidate)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_sessionlog_permission_snapshot_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE users_user ADD COLUMN IF NOT EXISTS username varchar(150);",
                    reverse_sql="ALTER TABLE users_user DROP COLUMN IF EXISTS username;",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='user',
                    name='username',
                    field=models.CharField(blank=True, max_length=150, null=True),
                ),
            ],
        ),
        migrations.RunPython(populate_usernames, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "UPDATE users_user "
                        "SET username = 'user' || substr(id::text, 1, 8) "
                        "WHERE username IS NULL OR username = '';"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE users_user ALTER COLUMN username SET NOT NULL;",
                    reverse_sql="ALTER TABLE users_user ALTER COLUMN username DROP NOT NULL;",
                ),
                migrations.RunSQL(
                    sql=(
                        "DO $$ BEGIN "
                        "IF NOT EXISTS ("
                        "  SELECT 1 FROM pg_constraint WHERE conname = 'users_user_username_key'"
                        ") THEN "
                        "  ALTER TABLE users_user ADD CONSTRAINT users_user_username_key UNIQUE (username); "
                        "END IF; "
                        "END $$;"
                    ),
                    reverse_sql=(
                        "ALTER TABLE users_user DROP CONSTRAINT IF EXISTS users_user_username_key;"
                    ),
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='user',
                    name='username',
                    field=models.CharField(max_length=150, unique=True),
                ),
            ],
        ),
    ]
