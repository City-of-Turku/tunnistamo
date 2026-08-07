"""Regenerate Suomi.fi SAML redirect signature fixtures (run inside Docker)."""
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tunnistamo.test_settings')
sys.path.insert(0, '/app')
django.setup()

from urllib.parse import parse_qs, urlencode, urlparse

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from freezegun import freeze_time
from oidc_provider.models import Client as OIDCClient
from onelogin.saml2.utils import OneLogin_Saml2_Utils as SAMLUtils
from social_django.models import UserSocialAuth

from tunnistamo.tests.test_suomifi_authentication import (
    CLIENT_ID,
    ID_TOKEN_JWT,
    ID_TOKEN_JWT_INVALID,
    REDIRECT_URI,
    RELAY_STATE,
    SERVER_NAME,
    TEST_PASSWORD,
    TEST_USER,
    create_oidc_client,
    create_oidc_token,
    create_social_user,
    create_user,
    load_file,
)
from users.models import Application, LoginMethod, OidcClientOptions

SAMLUtils.generate_unique_id = lambda: 'MESSAGE_ID_FOR_TEST'
DATA_DIR = '/app/tunnistamo/tests/data'


def reset_db():
    OidcClientOptions.objects.all().delete()
    LoginMethod.objects.all().delete()
    Application.objects.all().delete()
    UserSocialAuth.objects.all().delete()
    OIDCClient.objects.all().delete()
    get_user_model().objects.all().delete()


def save(name, value):
    path = os.path.join(DATA_DIR, name)
    with open(path, 'w') as handle:
        handle.write(value)
    print('updated', name)


@freeze_time('2019-01-01 12:00:00', tz_offset=2)
def main():
    reset_db()
    client = Client(HTTP_HOST=SERVER_NAME)
    oidc_client = create_oidc_client()

    auth_response = client.get(
        reverse('authorize') + '?' + urlencode({
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'response_type': 'code',
        }),
        follow=True,
    )
    login_qs = parse_qs(urlparse(auth_response.redirect_chain[-1][0]).query)
    save('suomifi_login_signature.b64', login_qs['Signature'][0])

    user = create_user(get_user_model())
    create_social_user(user)
    create_oidc_token(user, oidc_client)
    client.login(username=TEST_USER, password=TEST_PASSWORD)
    session = client.session
    session['social_auth_last_login_backend'] = 'suomifi'
    session.save()

    logout_response = client.get(
        reverse('end-session') + '?' + urlencode({
            'id_token_hint': ID_TOKEN_JWT,
            'post_logout_redirect_uri': REDIRECT_URI,
        })
    )
    logout_qs = parse_qs(urlparse(logout_response.url).query)
    save('suomifi_logout_signature.b64', logout_qs['Signature'][0])
    logout_request = SAMLUtils.decode_base64_and_inflate(logout_qs['SAMLRequest'][0])
    with open(os.path.join(DATA_DIR, 'suomifi_logout_request.xml'), 'wb') as handle:
        handle.write(logout_request)
    print('updated suomifi_logout_request.xml')

    client = Client(HTTP_HOST=SERVER_NAME)
    user = get_user_model().objects.get(username=TEST_USER)
    social_user = UserSocialAuth.objects.get(user=user, provider='suomifi')
    social_user.extra_data = {
        'name_id': 'SUOMIFI_SESSION_IDENTIFIER',
        'session_index': 'SUOMIFI_SESSION_INDEX',
    }
    social_user.save()
    create_oidc_token(user, oidc_client)
    client.login(username=TEST_USER, password=TEST_PASSWORD)
    session = client.session
    session['social_auth_last_login_backend'] = 'suomifi'
    session.save()
    invalid_logout_response = client.get(
        reverse('end-session') + '?' + urlencode({
            'id_token_hint': ID_TOKEN_JWT_INVALID,
            'post_logout_redirect_uri': REDIRECT_URI,
        })
    )
    invalid_qs = parse_qs(urlparse(invalid_logout_response.url).query)
    save('suomifi_logout_without_relaystate_signature.b64', invalid_qs['Signature'][0])

    client = Client(HTTP_HOST=SERVER_NAME)
    idp_response = client.get(
        reverse('auth_backends:logout_callback', kwargs={'backend': 'suomifi'}) + '?' + urlencode({
            'SAMLRequest': load_file('suomifi_idp_logout_request_encoded.b64').decode(),
            'RelayState': RELAY_STATE,
            'SigAlg': 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256',
            'Signature': load_file('suomifi_idp_logout_signature.b64').decode(),
        })
    )
    idp_qs = parse_qs(urlparse(idp_response.url).query)
    save('suomifi_idp_logout_response_signature.b64', idp_qs['Signature'][0])


if __name__ == '__main__':
    main()
