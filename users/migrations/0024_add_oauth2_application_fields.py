from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_allowedorigin'),
    ]

    operations = [
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
    ]
