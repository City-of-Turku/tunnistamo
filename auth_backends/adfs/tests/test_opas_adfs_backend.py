import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from auth_backends.adfs.opas import OpasADFS
from social_django.utils import load_strategy


EMAIL_CLAIM = 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress'
GIVEN_NAME_CLAIM = 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname'
SURNAME_CLAIM = 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname'


@pytest.fixture
def opas_backend(settings, monkeypatch):
    settings.SOCIAL_AUTH_OPAS_ADFS_SP_ENTITY_ID = 'https://tunnistamo.test/'
    settings.SOCIAL_AUTH_OPAS_ADFS_SP_PUBLIC_CERT = 'dummy-cert'
    settings.SOCIAL_AUTH_OPAS_ADFS_SP_PRIVATE_KEY = 'dummy-key'

    monkeypatch.setattr(
        OpasADFS,
        'remote_metadata',
        {
            'entity_id': 'https://login.microsoftonline.com/test/',
            'url': 'https://login.microsoftonline.com/test/saml2',
            'x509cert': 'dummy-idp-cert',
        },
    )

    request = RequestFactory().get('/accounts/opas_adfs/login/')
    request.session = SessionStore()
    return OpasADFS(load_strategy(request))


def _build_response(attributes):
    return {
        'idp_name': 'opas_adfs',
        'attributes': attributes,
    }


def test_get_user_details_without_optional_claims(opas_backend):
    response = _build_response({
        EMAIL_CLAIM: 'teacher@example.com',
        GIVEN_NAME_CLAIM: 'Test',
        SURNAME_CLAIM: 'Teacher',
    })

    details = opas_backend.get_user_details(response)

    assert details['email'] == 'teacher@example.com'
    assert details['first_name'] == 'Test'
    assert details['last_name'] == 'Teacher'
    assert 'school_role' not in details


def test_get_user_details_includes_school_role_when_present(opas_backend):
    response = _build_response({
        EMAIL_CLAIM: 'teacher@example.com',
        OpasADFS.ROLE_CLAIM: ['Teacher'],
    })

    details = opas_backend.get_user_details(response)

    assert details['school_role'] == 'Teacher'
