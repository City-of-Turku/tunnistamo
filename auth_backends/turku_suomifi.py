import re
import base64
import json
import uuid
import hashlib
from importlib import import_module
from urllib.parse import urlencode
from datetime import datetime, date

import requests
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.urls import reverse
from django.utils import translation
from social_core.utils import handle_http_errors
from social_core.backends.legacy import LegacyAuth
from social_core.exceptions import (
    AuthMissingParameter, AuthFailed, AuthStateForbidden
)

from tunnistamo import auditlog


session_engine = import_module(settings.SESSION_ENGINE)


class SuomiFiAssociation(object):
    """ Use Association model to save the nonce by force."""

    def __init__(self, handle, secret='', issued=0, lifetime=0, assoc_type=''):
        self.handle = handle  # as nonce
        self.secret = secret.encode()  # not use
        self.issued = issued  # not use
        self.lifetime = lifetime  # not use
        self.assoc_type = assoc_type  # as state


class TurkuSuomiFiAuth(LegacyAuth):
    name = 'turku_suomifi'
    EXTRA_DATA = ['non_disclosure', 'postal_code', 'municipality_name', 'municipality_code']

    def api_url(self):
        return self.setting('API_URL')

    def uses_redirect(self):
        return False

    def is_email_needed(self, **kwargs):
        return False

    def get_user_id(self, details, response):
        return response['oid']

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        data = super().extra_data(user, uid, response, details, *args, **kwargs)
        data['session_index'] = response.get('session_index')
        return data

    def get_user_details(self, response):
        out = {}
        attrs = response['attributes']
        out['first_name'] = attrs.get('firstName', None)
        out['last_name'] = attrs.get('sn', None)

        out['municipality_code'] = attrs.get('KotikuntaKuntanumero', None)
        out['municipality_name'] = attrs.get('KotikuntaKuntaS', None)
        out['non_disclosure'] = attrs.get('TurvakieltoTieto', None)
        out['postal_code'] = attrs.get('VakinainenKotimainenLahiosoitePostinumero', None)

        birthdate = attrs.get('nationalIdentificationNumber', '')
        if birthdate:
            m = re.match(r'([0-9]{2})([0-9]{2})([0-9]{2})([A-])', birthdate)
            if not m:
                raise AuthFailed(self, 'Invalid birth date: %s' % birthdate)
            day, month, year, century = m.groups()
            if century == 'A':
                year = '20' + year
            else:
                year = '19' + year
            out['birthdate'] = date(int(year), int(month), int(day))
        return out

    def api_post(self, path, params, relay_state):
        url = '%s/%s' % (self.api_url(), path)
        now = datetime.utcnow().isoformat().split('.')[0] + 'Z'
        message_id = 'T' + str(uuid.uuid4())
        sp_name = self.setting('SP_NAME')

        data = {
            'message_id': message_id,
            'timestamp': now,
        }
        data.update(params)
        msg = json.dumps(data)
        msg_body = urlencode({
            'SAMLRequest': base64.b64encode(msg.encode('utf8')).decode('utf8'),
            'RelayState': relay_state,
        })
        auth_line = (sp_name + now + msg_body + self.setting('API_KEY')).encode('utf8')
        auth = hashlib.sha256(auth_line).hexdigest()
        headers = {
            'X-TURKU-SP': sp_name,
            'X-TURKU-TS': now,
            'Authorization': auth,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        resp = requests.post(url, headers=headers, data=msg_body)
        return resp

    def get_and_store_nonce(self, url, secret):
        # Create a nonce
        nonce = self.strategy.random_string(64)
        # Store the nonce
        association = SuomiFiAssociation(nonce, secret=secret)
        self.strategy.storage.association.store(url, association)
        return nonce

    def get_nonce(self, nonce):
        try:
            obj = self.strategy.storage.association.get(
                server_url=self.api_url(),
                handle=nonce
            )[0]
            obj.secret = base64.b64decode(obj.secret).decode()
            return obj
        except IndexError:
            pass

    def remove_nonce(self, nonce_id):
        self.strategy.storage.association.remove([nonce_id])

    def auth_html(self):
        request = self.strategy.request

        auditlog.log_authentication_request(request, self.name)
        REQUIRED_SETTINGS = ['API_URL', 'API_KEY', 'SP_NAME']
        for setting_name in REQUIRED_SETTINGS:
            if not self.setting(setting_name):
                raise ImproperlyConfigured('Required setting %s not found' % setting_name)

        callback_url = reverse('social:complete', kwargs=dict(backend=self.name))
        if REDIRECT_FIELD_NAME in self.data:
            callback_url += '?' + urlencode({REDIRECT_FIELD_NAME: self.data[REDIRECT_FIELD_NAME]})
        callback_url = self.strategy.build_absolute_uri(callback_url)

        # When the session cookies is set with SameSite=lax, we lose access
        # to the cookie when the User Agent returns with the SAML response
        # (through a POST request). We store the session ID in the database
        # and refer to it with a randomly generated nonce that we store
        # in the RelayState SAML parameter.

        session = request.session
        # If the session hasn't ever been saved, it doesn't have a session
        # key yet.
        if not session.is_empty() and not session.session_key:
            session.save()
        relay_state = self.get_and_store_nonce(self.api_url(), session.session_key or '')

        language = translation.get_language()
        if language not in ('fi', 'en', 'sv'):
            language = 'fi'

        params = {
            'callback_url': callback_url,
            'language': language
        }

        # FIXME: generate proper nonce
        resp = self.api_post('esuomifi/v1/authnrequest/simple', params, relay_state)
        resp.raise_for_status()

        return HttpResponse(resp.content)

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        if 'SAMLResponse' not in self.data:
            raise AuthMissingParameter(self, 'SAMLResponse')
        if 'RelayState' not in self.data:
            raise AuthMissingParameter(self, 'RelayState')

        nonce = self.data['RelayState']
        nonce_obj = self.get_nonce(nonce)
        if not nonce_obj:
            raise AuthStateForbidden(self, 'Invalid nonce in RelayState: %s' % nonce)

        # Remove the association object to prevent re-use attacks.
        self.remove_nonce(nonce_obj.id)

        request = self.strategy.request
        if not request.session.session_key and nonce_obj.secret:
            session = session_engine.SessionStore(nonce_obj.secret)
            request.session = self.strategy.session = session

        # FIXME: verify AuthCode

        resp = base64.b64decode(self.data['SAMLResponse']).decode('utf8')
        data = json.loads(resp)
        status_code = data.get('status_code', '')
        if status_code.lower() != 'success':
            auditlog.log_authentication_failure(request, self.name)
            raise AuthFailed(self, 'Authentication unsuccessful: %s' % status_code)

        oid = data.get('oid', '')
        if not oid:
            raise AuthMissingParameter(self, 'oid')

        auditlog.log_authentication_success(request, self.name, identifier=oid)

        response = {
            'oid': oid,
            'attributes': data.get('attributes', {}),
            'session_index': data.get('session_index', ''),
        }
        kwargs.update({'response': response, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    def create_logout_response(self, social_user, redirect_uri):
        session_index = social_user.extra_data.get('session_index')
        if not session_index:
            return None

        logout_complete_uri = reverse('auth_backends:logout_callback', kwargs=dict(backend=self.name))
        params = {
            'callback_url': self.strategy.absolute_uri(logout_complete_uri),
            'session_index': session_index,
        }

        resp = self.api_post('esuomifi/v1/logoutrequest/simple', params, relay_state=redirect_uri or '')
        resp.raise_for_status()
        return HttpResponse(resp)

    def logout_complete(self):
        # FIXME: verify AuthCode
        redirect_uri = self.data['RelayState']
        if redirect_uri == 'null':
            redirect_uri = None
        return HttpResponseRedirect(redirect_uri or settings.LOGIN_REDIRECT_URL)
