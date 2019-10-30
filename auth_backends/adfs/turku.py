import logging
import json
from social_core.backends.saml import SAMLAuth, SAMLIdentityProvider
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
from django.core.cache import cache
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from tunnistamo.exceptions import FriendlySocialAuthException


logger = logging.getLogger(__name__)


class NoAssociatedOID(FriendlySocialAuthException):
    default_message = _('Your AD account does not have an associated OID')


class TurkuADFS(SAMLAuth):
    name = 'turku_adfs'
    metadata_url = 'https://sts.turku.fi/federationmetadata/2007-06/federationmetadata.xml'

    def generate_saml_config(self, idp=None):
        ret = super().generate_saml_config(idp)
        ret['security']['wantAssertionsSigned'] = True,
        # ADFS doesn't reply with NameID
        ret['security']['wantNameId'] = False
        return ret

    @cached_property
    def remote_metadata(self):
        """Load the IdP metadata from the remote server and cache it for future accesses"""

        cache_key = '%s-idp-metadata' % self.name
        cached_metadata = cache.get(cache_key)
        if cached_metadata:
            return json.loads(cached_metadata)

        config = OneLogin_Saml2_IdPMetadataParser.parse_remote(self.metadata_url)
        idp = config['idp']
        out = {
            'entity_id': idp['entityId'],
            'url': idp['singleSignOnService']['url'],
            'x509cert': idp['x509certMulti']['signing'][0],
        }
        cache.set(cache_key, json.dumps(out), timeout=24 * 3600)

        return out

    def get_idp(self, idp_name=None):
        if idp_name is None:
            idp_name = self.name
        elif idp_name != self.name:
            raise Exception('Only IDP name allowed is %s' % self.name)

        enabled_idps = self.setting('ENABLED_IDPS', {})
        if idp_name not in enabled_idps:
            idp_config = self.remote_metadata
        else:
            idp_config = enabled_idps[idp_name]

        idp_config['attr_user_permanent_id'] = 'http://schemas.microsoft.com/ws/2013/11/alternateloginid'
        idp_config['attr_email'] = 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress'
        idp_config['attr_full_name'] = 'http://schemas.xmlsoap.org/claims/CommonName'
        idp_config['attr_first_name'] = 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname'
        idp_config['attr_last_name'] = 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname'

        return SAMLIdentityProvider(idp_name, **idp_config)

    def get_allowed_idp_name(self, request):
        return self.name

    def get_user_id(self, details, response):
        # We override this method, because we don't want the 'turku_adfs:'
        # prefix from superclass. We support only one IdP.
        #
        # Also, the OID field is not set for all accounts, so we fail
        # authentication gracefully when that happens.
        idp = self.get_idp()
        attrs = response['attributes']
        uid = attrs.get(idp.conf['attr_user_permanent_id'])
        if isinstance(uid, list):
            uid = uid[0]
        if not uid or not isinstance(uid, str):
            logger.warn('Account has no OID field: %s\n' % attrs)
            raise NoAssociatedOID()
        return uid

    def is_email_needed(self, **kwargs):
        return False
