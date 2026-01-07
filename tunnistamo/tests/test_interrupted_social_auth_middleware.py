from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from django.test import RequestFactory
from social_core.exceptions import AuthFailed

from tunnistamo.middleware import InterruptedSocialAuthMiddleware


def test_interrupted_social_auth_middleware_redirect_preserves_next_param():
    """
    Regression test: ensure we redirect to /login/?next=<value> (not
    /login/?<value>=<value>) when social-auth flow is interrupted.
    """

    next_url = "/openid/authorize?client_id=clientid-1&redirect_uri=https%3A%2F%2Fservice-url%2Fcallback"

    class DummyStrategy:
        def __init__(self, next_value):
            self.session = {"next": next_value}

        def setting(self, name):
            # Allow middleware to handle exception (don't re-raise).
            assert name == "RAISE_EXCEPTIONS"
            return False

    rf = RequestFactory()
    request = rf.get("/accounts/turku_suomifi/login/callback/")
    request.social_strategy = DummyStrategy(next_url)
    request.backend = SimpleNamespace(name="turku_suomifi")

    middleware = InterruptedSocialAuthMiddleware(get_response=lambda req: req)
    response = middleware.process_exception(request, AuthFailed(request.backend, "cancelled"))

    assert response is not None
    assert response.status_code == 302

    parsed = urlparse(response["Location"])
    assert parsed.path == "/login/"

    qs = parse_qs(parsed.query)
    assert qs.get("next") == [next_url]

