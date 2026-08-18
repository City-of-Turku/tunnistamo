from django.db import migrations, models


def _existing_columns(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        return {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor, table_name
            )
        }


def _application_fields():
    return [
        (
            'hash_client_secret',
            models.BooleanField(default=True),
        ),
        (
            'allowed_origins',
            models.TextField(
                blank=True,
                default='',
                help_text='Allowed origins list to enable CORS, space separated',
            ),
        ),
        (
            'algorithm',
            models.CharField(blank=True, default='', max_length=5),
        ),
        (
            'registration_source',
            models.CharField(
                choices=[
                    ('manual', 'Manual'),
                    ('dcr', 'Dynamic Client Registration'),
                    ('cimd', 'Client ID Metadata Document'),
                ],
                default='manual',
                help_text='How this application was registered (manual, DCR per RFC 7591, or CIMD)',
                max_length=32,
            ),
        ),
        (
            'cimd_expires_at',
            models.DateTimeField(
                blank=True,
                default=None,
                help_text='When the cached Client ID Metadata Document should be re-fetched',
                null=True,
            ),
        ),
    ]


def add_oauth2_application_fields(apps, schema_editor):
    Application = apps.get_model('users', 'Application')
    existing_columns = _existing_columns(schema_editor, Application._meta.db_table)

    for name, field in _application_fields():
        if name in existing_columns:
            continue
        field.set_attributes_from_name(name)
        schema_editor.add_field(Application, field)


class Migration(migrations.Migration):
    """
    Add django-oauth-toolkit 3.x Application fields on users_application.

    users 0024 is a no-op dependency anchor for existing databases. oauth2_provider
    migrations do not always alter the swapped Application table, so we add the
    columns here explicitly.

    Some databases already received these columns from the pre-4.2 users 0024
    migration; skip any column that is already present.
    """

    dependencies = [
        ('users', '0025_add_last_api_use_field'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_oauth2_application_fields,
                    migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='application',
                    name='hash_client_secret',
                    field=models.BooleanField(default=True),
                ),
                migrations.AddField(
                    model_name='application',
                    name='allowed_origins',
                    field=models.TextField(
                        blank=True,
                        default='',
                        help_text='Allowed origins list to enable CORS, space separated',
                    ),
                ),
                migrations.AddField(
                    model_name='application',
                    name='algorithm',
                    field=models.CharField(blank=True, default='', max_length=5),
                ),
                migrations.AddField(
                    model_name='application',
                    name='registration_source',
                    field=models.CharField(
                        choices=[
                            ('manual', 'Manual'),
                            ('dcr', 'Dynamic Client Registration'),
                            ('cimd', 'Client ID Metadata Document'),
                        ],
                        default='manual',
                        help_text='How this application was registered (manual, DCR per RFC 7591, or CIMD)',
                        max_length=32,
                    ),
                ),
                migrations.AddField(
                    model_name='application',
                    name='cimd_expires_at',
                    field=models.DateTimeField(
                        blank=True,
                        default=None,
                        help_text='When the cached Client ID Metadata Document should be re-fetched',
                        null=True,
                    ),
                ),
            ],
        ),
    ]
