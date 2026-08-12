# Turku production deployment notes

## Code upgrade steps

- Run migrations (see **Django 4.2 migration notes** below if upgrading from pre-4.2)
- Compile translations: `python manage.py compilemessages`
- Collect static files: `python manage.py collectstatic --noinput`
- Reload uWSGI

### Django 4.2 migration notes

Tunnistamo uses a custom `users.Application` model (`OAUTH2_PROVIDER_APPLICATION_MODEL`).
Application table changes come from **`oauth2_provider` migrations**, not duplicate `users` migrations.

On an existing database (e.g. test/production), run:

```bash
# post_logout_redirect_uris already exists on users_application from older users migrations
python manage.py migrate oauth2_provider 0007_application_post_logout_redirect_uris --fake

python manage.py migrate --noinput
```

If `migrate` fails on another already-existing Application column, fake that specific
`oauth2_provider` migration and re-run `migrate`.

If you previously hit `InconsistentMigrationHistory` for `users.0020_populate_cors_allowed_origins`,
deploy the fixed migration files first, then run the commands above.

## Installation

### Basics

- Install Tunnistamo and Postgres
- Go through the code upgrade steps above.
- Place `local_settings.py` in repo root and put the settings in the following sections there.
- Create a superuser for the Django admin UI.

### uWSGI

Because of the size of the HTTP requests related to OIDC, the default uWSGI buffer size of 4k will not be enough. Increase it by configuring the following in your uWSGI .ini file:

```
[uwsgi]
...
buffer-size=32768
```

### Turku suomi.fi auth backend

- Configure the following settings:

```python
SOCIAL_AUTH_TURKU_SUOMIFI_API_URL = 'https://<server>:<port>/tunnistautuminen/api'
SOCIAL_AUTH_TURKU_SUOMIFI_API_KEY = '<api key>'
SOCIAL_AUTH_TURKU_SUOMIFI_SP_NAME = '<sp name>'
```

- Make sure the API URL is accessible from the server.

### VASKI library card backend (Axiell Aurora)

- Configure the following settings:

```python
SOCIAL_AUTH_AXIELL_AURORA_API_URL = 'https://<server>:<port>'
SOCIAL_AUTH_AXIELL_AURORA_API_USERNAME = '<username>'
SOCIAL_AUTH_AXIELL_AURORA_API_PASSWORD = '<pasword>'
```

- Make sure the API URL is accessible from the server.

### Turku ADFS auth backend

- Generate keypair for ADFS SAML authentication

```shell
openssl req -subj "/C=FI/L=Turku/O=City of Turku/CN=tunnistamo.turku.fi" -new -x509 -days 3652 -nodes -out turku_adfs.crt -keyout turku_adfs.key
```

- Move the certificate and the key file somewhere safe and point the `SAML_CERTIFICATE_PATH` environment variable to that directory. The default is `<repo root>/certs`. Ensure the directory is only accessible by the UWSGI user.
- Make sure `https://sts.turku.fi` is accessible.
- Configure the ADFS backend settings:

```
SOCIAL_AUTH_TURKU_ADFS_TECHNICAL_CONTACT = {
    'givenName': 'Turun kaupunki',
    'emailAddress': 'turun.kaupunki@turku.fi',
}
SOCIAL_AUTH_TURKU_ADFS_SUPPORT_CONTACT = {
    'givenName': 'Turun kaupunki',
    'emailAddress': 'turun.kaupunki@turku.fi',
}
SOCIAL_AUTH_TURKU_ADFS_ORG_INFO = {
    "en-US": {
        "name": "Turku",
        "displayname": "City of Turku",
        "url": "https://www.turku.fi"
    },
    "fi-FI": {
        "name": "Turku",
        "displayname": "Turun kaupunki",
        "url": "https://www.turku.fi"
    },
    "sv-FI": {
        "name": "Åbo",
        "displayname": "Åbo stad",
        "url": "https://www.turku.fi"
    },
}
SOCIAL_AUTH_TURKU_ADFS_SP_ENTITY_ID = "https://tunnistamo.turku.fi/"
SOCIAL_AUTH_TURKU_ADFS_SP_PUBLIC_CERT = open(os.path.join(env('SAML_CERTIFICATE_PATH'), 'turku_adfs.crt')).read()
SOCIAL_AUTH_TURKU_ADFS_SP_PRIVATE_KEY = open(os.path.join(env('SAML_CERTIFICATE_PATH'), 'turku_adfs.key')).read()
```

### Login methods

Add the supported login methods either through the Django admin UI or by `manage.py loaddata`:

```json
[
{
    "model": "users.loginmethod",
    "pk": 1,
    "fields": {
        "provider_id": "axiell_aurora",
        "background_color": "#00c8f2",
        "logo_url": null,
        "order": 1,
        "require_registered_client": false
    }
},
{
    "model": "users.loginmethod",
    "pk": 2,
    "fields": {
        "provider_id": "turku_adfs",
        "background_color": null,
        "logo_url": null,
        "order": 100,
        "require_registered_client": false
    }
},
{
    "model": "users.loginmethod",
    "pk": 3,
    "fields": {
        "provider_id": "turku_suomifi",
        "background_color": null,
        "logo_url": null,
        "order": 0,
        "require_registered_client": false
    }
},
{
    "model": "users.loginmethodtranslation",
    "pk": 1,
    "fields": {
        "language_code": "fi",
        "name": "Suomi.fi-tunnistautuminen",
        "short_description": "",
        "master": 3
    }
},
{
    "model": "users.loginmethodtranslation",
    "pk": 2,
    "fields": {
        "language_code": "fi",
        "name": "Vaski-kirjastokortti",
        "short_description": "",
        "master": 1
    }
},
{
    "model": "users.loginmethodtranslation",
    "pk": 3,
    "fields": {
        "language_code": "fi",
        "name": "Turun kaupungin ty\u00f6ntekij\u00e4t",
        "short_description": "",
        "master": 2
    }
},
{
    "model": "users.loginmethodtranslation",
    "pk": 4,
    "fields": {
        "language_code": "en",
        "name": "Suomi.fi authentication",
        "short_description": "",
        "master": 3
    }
},
{
    "model": "users.loginmethodtranslation",
    "pk": 5,
    "fields": {
        "language_code": "en",
        "name": "Vaski library card",
        "short_description": "",
        "master": 1
    }
},
{
    "model": "users.loginmethodtranslation",
    "pk": 6,
    "fields": {
        "language_code": "en",
        "name": "City of Turku employees",
        "short_description": "",
        "master": 2
    }
}
]
```

### Site general content

Add a new `generalcontent` singleton from the Django admin UI (content app, GeneralContent model)
or with the `loaddata` command:

```json
[
{
    "model": "content.generalcontent",
    "pk": 1,
    "fields": {}
},
{
    "model": "content.generalcontenttranslation",
    "pk": 1,
    "fields": {
        "language_code": "fi",
        "site_owner_name": "Turun kaupunki",
        "privacy_policy_url": "https://www.turku.fi/tietosuoja",
        "master": 1
    }
},
{
    "model": "content.generalcontenttranslation",
    "pk": 2,
    "fields": {
        "language_code": "en",
        "site_owner_name": "City of Turku",
        "privacy_policy_url": "https://www.turku.fi/en/turku-info/privacy-policy",
        "master": 1
    }
},
{
    "model": "content.generalcontenttranslation",
    "pk": 3,
    "fields": {
        "language_code": "sv",
        "site_owner_name": "\u00c5bo stad",
        "privacy_policy_url": "https://www.turku.fi/sv/information-om-abo/datasekretess",
        "master": 1
    }
}
]
```

### Add OIDC API configuration

- From the Django admin UI, add an API domain with an identifier of `https://auth.turku.fi`.
- Configure each OIDC API and corresponding OIDC clients as required.

### Periodic tasks

Run the following commands about once per day (e.g. through cron):

- OIDC provider key creation and expiration: `manage.py manage_openid_keys`
- Expired session removal: `manage.py clearsessions`
