from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OidcApisConfig(AppConfig):
    name = 'oidc_apis'
    verbose_name = _('API support for OpenID Connect')
