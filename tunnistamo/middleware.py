import json
import logging
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils import timezone
from django.utils.http import urlencode, url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.messages.api import MessageFailure
from ipware import get_client_ip
from social_core.exceptions import SocialAuthBaseException
from oidc_provider.lib.errors import BearerTokenError
from django.contrib.auth import REDIRECT_FIELD_NAME

from .exceptions import FriendlySocialAuthException


logger = logging.getLogger(__name__)


class InterruptedSocialAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def get_redirect_uri(self, request, exception):
        strategy = request.social_strategy
        redirect_uri = reverse('login')
        next_url = strategy.session.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            redirect_uri += '?%s' % urlencode({REDIRECT_FIELD_NAME: next_url})
        return redirect_uri

    # Override raise_exception() to allow redirect also when debug is enabled
    def raise_exception(self, request, exception):
        strategy = request.social_strategy
        return strategy.setting('RAISE_EXCEPTIONS')

    def get_message(self, request, exception):
        # If we know that the exception will have a user-friendly,
        # translated message, we can confidently show that to the
        # user.
        if isinstance(exception, FriendlySocialAuthException):
            return str(exception)

        # Otherwise, a general message.
        return _('Authentication failed.')

    def process_exception(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        if strategy is None or self.raise_exception(request, exception):
            return

        if not isinstance(exception, SocialAuthBaseException):
            return

        logger.info(str(exception), exc_info=exception)

        backend = getattr(request, 'backend', None)
        backend_name = getattr(backend, 'name', 'unknown-backend')

        url = self.get_redirect_uri(request, exception)
        message = self.get_message(request, exception)
        try:
            messages.error(request, message,
                           extra_tags='social-auth ' + backend_name)
        except MessageFailure:
            pass

        if url:
            return redirect(url)


class OIDCExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, BearerTokenError):
            response = HttpResponseForbidden()
            auth_fields = [
                'error="{}"'.format(exception.code),
                'error_description="{}"'.format(exception.description)
            ]
            if 'scope' in request.POST:
                auth_fields = ['Bearer realm="{}"'.format(request.POST['scope'])] + auth_fields
            response.__setitem__('WWW-Authenticate', ', '.join(auth_fields))
            return response


class RestrictedAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, 'user', None) and request.user.is_authenticated and \
           request.session.get('_auth_user_backend') in settings.RESTRICTED_AUTHENTICATION_BACKENDS:
            if request.user.last_login + timedelta(seconds=settings.RESTRICTED_AUTHENTICATION_TIMEOUT) < timezone.now():
                logger.info('Restricted session has timed out. Session started at {}'.format(request.user.last_login))
                response = HttpResponseRedirect(request.get_full_path())
                request.session.delete()
                return response
        return self.get_response(request)


class ContentSecurityPolicyMiddleware(object):
    HEADER_ENFORCING = 'Content-Security-Policy'
    HEADER_REPORTING = 'Content-Security-Policy-Report-Only'

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def get_csp_settings(settings):
        return getattr(settings, 'CONTENT_SECURITY_POLICY', None)

    @staticmethod
    def find_policy(csp_settings):
        return csp_settings is not None and csp_settings.get('policy') is not None

    def __call__(self, request):
        response = self.get_response(request)
        csp_settings = ContentSecurityPolicyMiddleware.get_csp_settings(settings)
        if not ContentSecurityPolicyMiddleware.find_policy(csp_settings):
            return response

        if csp_settings.get('report_only') is True:
            header = self.HEADER_REPORTING
        else:
            header = self.HEADER_ENFORCING
        response[header] = csp_settings['policy']

        if csp_settings.get('report_groups') and len(csp_settings.get('report_groups', {})) > 0:
            response['Report-To'] = json.dumps(csp_settings['report_groups'])
        return response


class RealClientIPMiddleware(object):
    """Set REMOTE_ADDR header based on data from trusted proxies"""

    # These headers might be used to determine the client IP address.
    # Paranoid as we are, we drop all of them after setting the right
    # client IP address from a trusted proxy.
    REMOVE_HEADERS = [
        'HTTP_X_FORWARDED_FOR',
        'X_FORWARDED_FOR',
        'HTTP_CLIENT_IP',
        'HTTP_X_REAL_IP',
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'HTTP_VIA',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

        for header_name in self.REMOVE_HEADERS:
            if header_name in request.META:
                del request.META[header_name]

        remote_addr = request.META.get('REMOTE_ADDR')

        trusted_proxies = getattr(settings, 'TRUSTED_PROXIES', [])
        for proxy_ip in trusted_proxies:
            if remote_addr == proxy_ip:
                from_trusted_proxy = True
                break
        else:
            from_trusted_proxy = False

        if from_trusted_proxy and forwarded_for:
            client_ip, _ = get_client_ip(request)
            if client_ip:
                request.META['REMOTE_ADDR'] = str(client_ip)

        return self.get_response(request)
