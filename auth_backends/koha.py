import logging
import re
from datetime import date, datetime
from urllib.parse import urlencode

import requests
from django import forms
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


class KohaLoginForm(forms.Form):
    id = 'koha_login_form'
    borrower_card_id = forms.CharField(label=_("Library card identifier"), max_length=32)
    borrower_pin = forms.CharField(
        label=_("Card PIN"),
        max_length=4,
        widget=forms.TextInput(attrs={'type': 'password'})
    )


class KohaAuth(LegacyAuth):
    name = 'koha'
    ID_KEY = 'borrower_card_id'
    PIN_KEY = 'borrower_pin'
    FORM_HTML = 'koha/login.html'

    def get_user_id(self, details, response):
        return response['borrowernumber']

    def uses_redirect(self):
        return False

    def api_request(self, method, path, **kwargs):
        url = '%s%s' % (self.setting('API_URL'), path)

        try:
            resp = getattr(requests, method)(url, **kwargs)
            if resp.status_code not in [200, 400]:
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

        borrower_info = response
        email = borrower_info.get('email', None)
        if email is not None:
            email = email.strip().lower() or None
        out['email'] = email

        out['first_name'] = borrower_info.get('firstname', '').strip()
        out['last_name'] = borrower_info.get('surname', '').strip()

        return out

    def start(self):
        request = self.strategy.request
        if request.method == 'POST':
            form = KohaLoginForm(request.POST)
            if form.is_valid():
                try:
                    borrower_info = self.get_borrower_info(form.cleaned_data)
                    return complete_view(request, self.name, borrower_info=borrower_info)
                except APIError as err:
                    # FIXME: Log to sentry
                    logger.exception('Unable to get borrower info', exc_info=err)
                    raise AuthBackendUnavailable()
                except AuthenticationFailed:
                    form.add_error(None, _('Invalid card number or PIN'))
        else:
            form = KohaLoginForm()

        login_method_uri = reverse('login')
        if request.GET:
            login_method_uri += '?' + urlencode(request.GET)

        return render(request, self.FORM_HTML, {'form': form, 'login_method_uri': login_method_uri})

    def _validate_settings(self):
        REQUIRED_SETTINGS = ['API_URL']
        for setting_name in REQUIRED_SETTINGS:
            if not self.setting(setting_name):
                raise ImproperlyConfigured('Required setting %s not found' % setting_name)

    def get_borrower_info(self, data):
        self._validate_settings()

        request = self.strategy.request
        borrower_card_id = self.data[self.ID_KEY].strip()
        borrower_card_pin = self.data[self.PIN_KEY].strip()

        ratelimit_params = dict(
            group='auth:%s' % self.name,
            key=lambda group, request: borrower_card_id,
            rate='5/h'
        )
        limit = ratelimit.get_usage(None, **ratelimit_params, increment=True)
        if limit['should_limit']:
            auditlog.log_authentication_rate_limited(request, self.name, identifier=borrower_card_id)
            raise AccountTemporarilyLocked()

        result = self.api_request('post', '/contrib/kohasuomi/borrowers/status', files={
            'uname': (None, borrower_card_id),
            'passwd': (None, borrower_card_pin),
        })
        if 'error' in result and result['error'] == 'Authentication failed for the given username and password.':
            auditlog.log_authentication_failure(request, self.name, identifier=borrower_card_id)
            raise AuthenticationFailed('Login returned "Login failed."')

        borrower_info = result

        auditlog.log_authentication_success(request, self.name, identifier=borrower_card_id)
        # Reset the rate limiting on successful login
        ratelimit.get_usage(None, **ratelimit_params, reset=True)

        return borrower_info

    def auth_complete(self, *args, **kwargs):
        borrower_info = kwargs.get('borrower_info')
        if not borrower_info:
            raise AuthMissingParameter(self, 'borrower_info')

        kwargs.update({'response': borrower_info, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)
