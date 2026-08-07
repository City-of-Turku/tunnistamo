import datetime
import json
from calendar import timegm

import jwt
import responses
from social_core.tests.backends.oauth import OAuth2Test


class YleTunnusOAuth2Test(OAuth2Test):
    app_id = 'an-app-id'
    app_key = 'an-app-key'
    client_key = app_id
    client_secret = 'a-secret-key'
    jwt_secret = 'jwt-secret-key'

    backend_path = 'yletunnus.backends.YleTunnusOAuth2'
    expected_uid = '1234567890abcdef12345678'
    expected_email = 'yletunnus@example.com'
    expected_username = expected_email

    def extra_settings(self):
        settings = super().extra_settings()
        settings.update({
            'SOCIAL_AUTH_{0}_KEY'.format(self.name): self.app_id,
            'SOCIAL_AUTH_{0}_APP_ID'.format(self.name): self.app_id,
            'SOCIAL_AUTH_{0}_APP_KEY'.format(self.name): self.app_key,
            'SOCIAL_AUTH_{0}_SECRET'.format(self.name): self.client_secret,
            'SOCIAL_AUTH_{0}_JWT_SECRET'.format(self.name): self.jwt_secret,
        })
        return settings

    def get_id_token(self, client_key=None, expiration_datetime=None,
                     issue_datetime=None):
        """
        Return the id_token to be added to the access token body.
        """
        return {
            'iss': 'https://auth.api.yle.fi',
            'aud': client_key,
            'exp': expiration_datetime,
            'iat': issue_datetime,
            'sub': self.expected_uid,
            'email': self.expected_email,
            'scopes': 'sub email'
        }

    def build_access_token_body(self, client_key=None, tamper_message=False,
                                expiration_datetime=None,
                                issue_datetime=None):
        client_key = client_key or self.client_key
        now = datetime.datetime.utcnow()
        expiration_datetime = expiration_datetime or (now + datetime.timedelta(seconds=30))
        issue_datetime = issue_datetime or now
        id_token = self.get_id_token(
            client_key, timegm(expiration_datetime.utctimetuple()),
            timegm(issue_datetime.utctimetuple())
        )

        body = {'access_token': jwt.encode(id_token, self.jwt_secret, algorithm='HS256'),
                'token_type': 'bearer'}
        if tamper_message:
            id_token['sub'] = '1235'
            body['access_token'] = jwt.encode(id_token, self.jwt_secret, algorithm='HS256')

        return json.dumps(body)

    def auth_handlers(self, start_url):
        target_url = self.handle_state(
            start_url, self.strategy.build_absolute_uri(self.complete_url)
        )
        self.complete_url = target_url

        responses.add(
            responses.GET,
            start_url,
            status=301,
            headers={'Location': target_url},
        )
        responses.add(responses.GET, target_url, status=200, body="foobar")
        return target_url

    def pre_complete_callback(self, start_url):
        responses.add(
            self._method(self.backend.ACCESS_TOKEN_METHOD),
            url=self.backend.access_token_url(),
            status=200,
            body=self.build_access_token_body(),
            content_type="application/json",
        )

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL': True
        })
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL': True
        })
        self.do_partial_pipeline()
