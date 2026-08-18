import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from auth_backends.adfs.turku import TurkuADFS
from social_django.utils import load_strategy


OID_CLAIM = 'http://schemas.microsoft.com/ws/2013/11/alternateloginid'
GIVEN_NAME_CLAIM = 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname'
SURNAME_CLAIM = 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname'


@pytest.fixture
def turku_backend(settings, monkeypatch):
    settings.SOCIAL_AUTH_TURKU_ADFS_SP_ENTITY_ID = 'https://tunnistamo.test/'
    settings.SOCIAL_AUTH_TURKU_ADFS_SP_PUBLIC_CERT = 'dummy-cert'
    settings.SOCIAL_AUTH_TURKU_ADFS_SP_PRIVATE_KEY = 'dummy-key'

    monkeypatch.setattr(
        TurkuADFS,
        'remote_metadata',
        {
            'entity_id': 'https://login.microsoftonline.com/test/',
            'url': 'https://login.microsoftonline.com/test/saml2',
            'x509certMulti': {'signing': ['dummy-idp-cert']},
        },
    )

    request = RequestFactory().get('/accounts/turku_adfs/login/')
    request.session = SessionStore()
    return TurkuADFS(load_strategy(request))


def _build_response(attributes):
    return {
        'idp_name': 'turku_adfs',
        'attributes': attributes,
    }


def test_get_user_details_without_optional_claims(turku_backend):
    response = _build_response({
        OID_CLAIM: 'user-oid-123',
        GIVEN_NAME_CLAIM: 'Test',
        SURNAME_CLAIM: 'User',
    })

    details = turku_backend.get_user_details(response)

    assert details['first_name'] == 'Test'
    assert details['last_name'] == 'User'


def test_get_user_id_uses_oid_claim(turku_backend):
    response = _build_response({
        OID_CLAIM: 'user-oid-123',
    })

    uid = turku_backend.get_user_id({}, response)

    assert uid == 'user-oid-123'
