from django.db import migrations


class Migration(migrations.Migration):
    """
    Application schema changes for django-oauth-toolkit 3.x are applied by
    oauth2_provider migrations on the swappable users.Application model.

    This migration exists as a dependency anchor for later users migrations.
    """

    dependencies = [
        ('oauth2_provider', '0020_cimd_application_fields'),
        ('users', '0019_allowedorigin'),
    ]

    operations = []
