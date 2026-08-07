from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0024_add_oauth2_application_fields'),
        ('users', '0023_add_login_method_disabled_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_api_use',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name='Latest API token usage date',
            ),
        ),
    ]
