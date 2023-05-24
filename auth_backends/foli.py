import logging
import re
from datetime import date, datetime
import json
from urllib.parse import urlencode

import requests
from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from social_core.backends.legacy import LegacyAuth
from social_core.exceptions import AuthMissingParameter
from social_django.views import complete as complete_view

from tunnistamo import auditlog, ratelimit
from tunnistamo.exceptions import AccountTemporarilyLocked, AuthBackendUnavailable

logger = logging.getLogger(__name__)

class APIError(Exception):
    pass


class AuthenticationFailed(Exception):
    pass


class FoliLoginForm(forms.Form):
    id = 'foli_login_form'
    username = forms.CharField(label=_("Föli username"), max_length=32)
    password = forms.CharField(
        label=_("Password"),
        widget=forms.TextInput(attrs={'type': 'password'})
    )


class FoliAuth(LegacyAuth):
    name = 'foli'
    ID_KEY = 'username'
    PIN_KEY = 'password'
    FORM_HTML = 'foli/login.html'

    def get_user_id(self, details, response):
        return response['email']

    def uses_redirect(self):
        return False

    def api_request(self, method, path, **kwargs):
        url = '%s%s' % (self.setting('API_URL'), path)
        try:
            resp = getattr(requests, method)(url, **kwargs)
            if resp.status_code != 401:
                resp.raise_for_status()
        except requests.exceptions.RequestException as err:
            logger.exception('API call to %s failed' % path, exc_info=err)
            raise APIError('API call to %s failed: %s' % (path, str(err)))

        try:
            ret = resp.json()
        except TypeError as err:
            logger.exception('API returned invalid data', exc_info=err)
            raise APIError('API returned invalid JSON data: %s' % str(err))
        return ret

    def is_email_needed(self, **kwargs):
        return False

    def get_user_details(self, response):
        out = {}

        user_info = response
        email = user_info.get('email', None)
        if email is not None:
            email = email.strip().lower() or None
        out['email'] = email

        out['first_name'] = user_info.get('firstname', '').strip()
        out['last_name'] = user_info.get('lastname', '').strip()

        return out

    def start(self):
        request = self.strategy.request
        if request.method == 'POST':
            form = FoliLoginForm(request.POST)
            if form.is_valid():
                try:
                    user_info = self.get_user_info(form.cleaned_data)
                    return complete_view(request, self.name, user_info=user_info)
                except APIError as err:
                    # FIXME: Log to sentry
                    logger.exception('Unable to get borrower info', exc_info=err)
                    raise AuthBackendUnavailable()
                except AuthenticationFailed:
                    # TODO: Translaatio
                    form.add_error(None, _('Invalid username or password'))
        else:
            form = FoliLoginForm()

        login_method_uri = reverse('login')
        query_string = ''

        if request.GET:
            query_string = urlencode(request.GET)
            login_method_uri += '?' + query_string

        return render(request, self.FORM_HTML, {
            'form': form,
            'login_method_uri': login_method_uri,
            'query_string': query_string,
        })

    def _validate_settings(self):
        REQUIRED_SETTINGS = ['API_URL']
        for setting_name in REQUIRED_SETTINGS:
            if not self.setting(setting_name):
                raise ImproperlyConfigured('Required setting %s not found' % setting_name)

    def get_user_info(self, data):
        self._validate_settings()

        request = self.strategy.request
        username = self.data[self.ID_KEY].strip()
        borrower_card_pin = self.data[self.PIN_KEY].strip()

        ratelimit_params = dict(
            group='auth:%s' % self.name,
            key=lambda group, request: username,
            rate='5/h'
        )
        
        try:
            # Send login request. Settings must include SOCIAL_AUTH_FOLI_API_ID and SOCIAL_AUTH_FOLI_API_KEY
            result = self.api_request('post', '/login', auth=(settings.SOCIAL_AUTH_FOLI_API_ID, settings.SOCIAL_AUTH_FOLI_API_KEY), json=dict(
                username=username,
                password=borrower_card_pin)
            )
        except:
            auditlog.log_authentication_failure(request, self.name, identifier=username)
            raise AuthenticationFailed('Foli login request failure.')


        if result.get('result', None) == 'unknown user or password':
            auditlog.log_authentication_failure(request, self.name, identifier=username)
            raise AuthenticationFailed('Login returned "unknown user or password"')

        auditlog.log_authentication_success(request, self.name, identifier=username)
        # Reset the rate limiting on successful login
        ratelimit.get_usage(None, **ratelimit_params, reset=True)

        return result

    def auth_complete(self, *args, **kwargs):
        user_info = kwargs.get('user_info')
        if not user_info:
            raise AuthMissingParameter(self, 'user_info')

        kwargs.update({'response': user_info, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)
