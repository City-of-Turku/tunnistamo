from __future__ import unicode_literals

import logging
import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from helusers.models import AbstractUser
from ipware import get_client_ip
from oauth2_provider.models import AbstractApplication
from oidc_provider.models import Client
from parler.models import TranslatableModel, TranslatedFields

from users.utils import get_geo_location_data_for_ip

logger = logging.getLogger(__name__)


class User(AbstractUser):
    # Override first_name to allow it to be longer
    first_name = models.CharField(_('first name'), max_length=100, blank=True)

    primary_sid = models.CharField(max_length=100, unique=True)
    last_login_backend = models.CharField(max_length=100, null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True, verbose_name=_('birthdate'))

    def save(self, *args, **kwargs):
        if not self.primary_sid:
            self.primary_sid = uuid.uuid4()
        return super(User, self).save(*args, **kwargs)


def get_provider_ids():
    from django.conf import settings
    from social_core.backends.utils import load_backends
    return [(name, name) for name in load_backends(settings.AUTHENTICATION_BACKENDS).keys()]


class LoginMethod(TranslatableModel):
    disabled = models.BooleanField(
                default=False, verbose_name=_('disable login method'),
                help_text=_('Set if this login method should be unselectable')
            )
    
    provider_id = models.CharField(
        max_length=50, unique=True,
        choices=sorted(get_provider_ids()))
    logo_url = models.URLField(null=True, blank=True)
    order = models.PositiveIntegerField(null=True)
    require_registered_client = models.BooleanField(
        default=False, verbose_name=_('require registered client'),
        help_text=_('Set if this login method is not allowed when the login flow is started without an OIDC client')
    )

    translations = TranslatedFields(
        name=models.CharField(verbose_name=_('name'), max_length=100),
        short_description=models.TextField(verbose_name=_('short description'), null=True, blank=True),
    )

    def __str__(self):
        return "{} ({})".format(self.name, self.provider_id)

    class Meta:
        ordering = ('order',)

    
    def clean(self, *args, **kwargs):
        if self.disabled and not self.short_description:
            raise ValidationError(_('Short description is required if login method is disabled.'))

class OptionsBase(models.Model):
    SITE_TYPES = (
        ('dev', 'Development'),
        ('test', 'Testing'),
        ('production', 'Production')
    )
    site_type = models.CharField(max_length=20, choices=SITE_TYPES, null=True,
                                 verbose_name='Site type')
    login_methods = models.ManyToManyField(LoginMethod)
    include_ad_groups = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Application(OptionsBase, AbstractApplication):
    post_logout_redirect_uris = models.TextField(
        blank=True,
        default='',
        verbose_name=_(u'Post Logout Redirect URIs'),
        help_text=_(u'Enter each URI on a new line.'))

    class Meta:
        ordering = ('site_type', 'name')


class OidcClientOptions(OptionsBase):
    oidc_client = models.OneToOneField(Client, related_name='options', on_delete=models.CASCADE,
                                       verbose_name=_("OIDC Client"))

    def __str__(self):
        return 'Options for OIDC Client "{}"'.format(self.oidc_client.name)

    class Meta:
        verbose_name = _("OIDC Client Options")
        verbose_name_plural = _("OIDC Client Options")


class AllowedOrigin(models.Model):
    key = models.CharField(max_length=300, null=False, primary_key=True)


class UserLoginEntryManager(models.Manager):
    def create_from_request(self, request, service, **kwargs):
        kwargs.setdefault('user', request.user)

        if 'ip_address' not in kwargs:
            kwargs['ip_address'] = get_client_ip(request)[0]

        if 'geo_location' not in kwargs:
            try:
                kwargs['geo_location'] = get_geo_location_data_for_ip(kwargs['ip_address'])
            except Exception as e:
                # catch all exceptions here because we don't want any geo location related error
                # to make the whole login entry creation fail.
                logger.exception('Error getting geo location data for an IP: {}'.format(e))

        return self.create(service=service, **kwargs)


class UserLoginEntry(models.Model):
    user = models.ForeignKey(User, verbose_name=_('user'), related_name='login_entries', on_delete=models.CASCADE)
    service = models.ForeignKey(
        'services.Service', verbose_name=_('service'), related_name='user_login_entries', on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(verbose_name=_('timestamp'), db_index=True)
    ip_address = models.CharField(verbose_name=_('IP address'), max_length=50, null=True, blank=True)
    geo_location = JSONField(verbose_name=_('geo location'), null=True, blank=True)

    objects = UserLoginEntryManager()

    class Meta:
        verbose_name = _('user login entry')
        verbose_name_plural = _('user login entries')
        ordering = ('timestamp',)

    def save(self, *args, **kwargs):
        if not self.timestamp:
            self.timestamp = now()
        super().save(*args, **kwargs)
