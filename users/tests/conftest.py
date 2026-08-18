import unittest

import pytest
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from oidc_provider.models import Client, ResponseType
from rest_framework.test import APIClient

from services.factories import ServiceFactory
from users.factories import UserFactory
from users.models import Application, LoginMethod, OidcClientOptions


@pytest.fixture()
def assertCountEqual():
    def do_test(a, b):
        tc = unittest.TestCase()
        tc.assertCountEqual(a, b)

    return do_test


@pytest.fixture()
def user_factory():
    User = get_user_model()  # NOQA

    def make_instance(**args):
        args.setdefault('username', get_random_string(12))
        args.setdefault('password', get_random_string(12))
        args.setdefault('email', '{}@example.com'.format(get_random_string(8)))

        instance = User.objects.create(**args)
        instance.set_password(args.pop('password'))
        instance.save()

        return instance

    return make_instance


@pytest.fixture()
def application_factory():
    def make_instance(**args):
        args.setdefault('name', get_random_string(8))
        args.setdefault('client_id', get_random_string(12))
        args.setdefault('user', None)
        args.setdefault('redirect_uris', None)
        args.setdefault('client_type', Application.CLIENT_PUBLIC)
        args.setdefault('authorization_grant_type', Application.GRANT_IMPLICIT)

        instance = Application.objects.create(**args)
        instance.save()

        return instance

    return make_instance


@pytest.fixture()
def oidcclient_factory():
    def make_instance(**args):
        args.setdefault('name', get_random_string(8))
        args.setdefault('client_type', 'public')
        args.setdefault('client_id', get_random_string(8))
        args.setdefault('redirect_uris', None)

        response_types = args.pop('response_types', ['id_token token'])
        instance = Client.objects.create(**args)

        instance.save()
        for response_type in response_types:
            instance.response_types.add(ResponseType.objects.get(value=response_type))

        return instance

    return make_instance


@pytest.fixture()
def oidcclientoptions_factory():
    def make_instance(**args):
        args.setdefault('site_type', 'test')

        instance = OidcClientOptions.objects.create(**args)
        instance.save()

        return instance

    return make_instance


@pytest.fixture()
def loginmethod_factory():
    def make_instance(**args):
        args.setdefault('provider_id', None)
        args.setdefault('name', get_random_string(8))
        args.setdefault('order', 1)

        instance = LoginMethod.objects.create(**args)
        instance.save()

        return instance

    return make_instance


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def user_api_client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    api_client.user = user
    return api_client


@pytest.fixture
def service():
    return ServiceFactory(target='client')
