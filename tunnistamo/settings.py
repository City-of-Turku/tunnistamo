"""
Django settings for tunnistamo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

import environ

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, ""),
    DATABASE_URL=(str, "postgres:///tunnistamo"),
    CACHE_URL=(str, "locmemcache://tunnistamo"),
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS = (list, []),
    USE_X_FORWARDED_HOST=(bool, True),
    USE_X_FORWARDED_PORT=(bool, True),
    IPWARE_META_PRECEDENCE_ORDER = (list, []),
    TUNNISTAMO_THEME=(str, 'helsinki'),
    TRUSTED_PROXIES=(list, []),

    STATIC_URL=(str, '/static/'),
    STATIC_ROOT=(str, os.path.join(BASE_DIR, 'static')),
    MEDIA_ROOT=(str, os.path.join(BASE_DIR, 'media')),
    MEDIA_URL=(str, '/media/'),
    NODE_MODULES_ROOT=(str, os.path.join(BASE_DIR, 'node_modules')),

    # Authentication settings
    SOCIAL_AUTH_FACEBOOK_KEY=(str, ""),
    SOCIAL_AUTH_FACEBOOK_SECRET=(str, ""),

    SOCIAL_AUTH_GITHUB_KEY=(str, ""),
    SOCIAL_AUTH_GITHUB_SECRET=(str, ""),

    SOCIAL_AUTH_GOOGLE_KEY=(str, ""),
    SOCIAL_AUTH_GOOGLE_SECRET=(str, ""),

    SOCIAL_AUTH_HELSINKI_ADFS_KEY=(str, ""),
    SOCIAL_AUTH_HELSINKI_ADFS_SECRET=(str, ""),

    SOCIAL_AUTH_ESPOO_ADFS_KEY=(str, ""),
    SOCIAL_AUTH_ESPOO_ADFS_SECRET=(str, ""),

    SOCIAL_AUTH_SUOMIFI_SP_ENTITY_ID=(str, ""),
    SOCIAL_AUTH_SUOMIFI_SP_PUBLIC_CERT=(str, ""),
    SOCIAL_AUTH_SUOMIFI_SP_PRIVATE_KEY=(str, ""),

    # JSON values, default values can be found further down in the settings
    SOCIAL_AUTH_SUOMIFI_ORG_INFO=(str, ""),
    SOCIAL_AUTH_SUOMIFI_TECHNICAL_CONTACT=(str, ""),
    SOCIAL_AUTH_SUOMIFI_SUPPORT_CONTACT=(str, ""),
    SOCIAL_AUTH_SUOMIFI_ENABLED_IDPS=(str, ""),
    SOCIAL_AUTH_SUOMIFI_UI_INFO=(str, ""),
    SOCIAL_AUTH_SUOMIFI_UI_LOGO=(str, ""),

    # Needs to be true for Dockerfile collectstatic, since cert files don't yet exist then
    SKIP_CERTIFICATES=(str, ""),
)

if os.path.exists(os.path.join(BASE_DIR, '.env')):
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

DEBUG = env("DEBUG")

# Added
SITE_URL='localhost:8000'
USE_X_FORWARDED_HOST = env('USE_X_FORWARDED_HOST')
USE_X_FORWARDED_PORT = env('USE_X_FORWARDED_PORT')

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

X_FRAME_OPTIONS = 'DENY'

TUNNISTAMO_THEME = env('TUNNISTAMO_THEME')

# The list of IP addresses that are considered trusted proxies. If REMOTE_ADDR
# matches one of these addresses, X-Forwarded-For header will be trusted and the
# client IP address is read from there.
TRUSTED_PROXIES = env('TRUSTED_PROXIES')

# Application definition

INSTALLED_APPS = (
    'admin_site',  # replaces 'django.contrib.admin'
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    'themes',
    'parler',
    'compressor',
    'bootstrap4',

    'oauth2_provider',
    'users',
    'oidc_provider',

    'social_django',

    'rest_framework',
    'corsheaders',
    'svg',
    'crequest',
    'django_filters',

    'helusers',
    'content',

    'yletunnus',
    'hkijwt',
    'oidc_apis',
    'devices',
    'identities',
    'services',
    'key_manager',
    'auth_backends',

    'translation_checker',

    'utils',
)

MIDDLEWARE = (
    'tunnistamo.middleware.RealClientIPMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tunnistamo.middleware.RestrictedAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.CustomDatabaseWhitelistCorsMiddleware',
    'crequest.middleware.CrequestMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'tunnistamo.middleware.InterruptedSocialAuthMiddleware',
    'tunnistamo.middleware.OIDCExceptionMiddleware',
    'tunnistamo.middleware.ContentSecurityPolicyMiddleware'
)

AUTHENTICATION_BACKENDS = [
    'auth_backends.eduhelfi.EduHelFiAzure',
    'auth_backends.espoo.EspooAzure',
    'auth_backends.adfs.helsinki.HelsinkiADFS',
    'auth_backends.google.GoogleOAuth2CustomName',
    'auth_backends.adfs.helsinki_library_asko.HelsinkiLibraryAskoADFS',
    'yletunnus.backends.YleTunnusOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
    'auth_backends.suomifi.SuomiFiSAMLAuth',
    'auth_backends.axiell_aurora.AuroraAuth',
    'auth_backends.adfs.turku.TurkuADFS',
    'auth_backends.adfs.opas.OpasADFS',
    'auth_backends.turku_suomifi.TurkuSuomiFiAuth',
    'auth_backends.koha.KohaAuth',
    'auth_backends.foli.FoliAuth',
]

RESTRICTED_AUTHENTICATION_BACKENDS = (
    'auth_backends.suomifi.SuomiFiSAMLAuth',
)
RESTRICTED_AUTHENTICATION_TIMEOUT = 60 * 60

ROOT_URLCONF = 'tunnistamo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'themes.context_processors.theme_variables',
                'content.context_processors.general_content',
            ],
        },
    },
]

WSGI_APPLICATION = 'tunnistamo.wsgi.application'

#
# Database
#
DATABASES = {"default": env.db("DATABASE_URL")}

#
# Internationalization
#
LANGUAGE_CODE = 'fi'

LANGUAGES = (
    ('fi', 'Finnish'),
    ('en', 'English'),
    ('sv', 'Swedish')
)

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGE_SESSION_KEY = 'ui-language'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/profile/'

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
AUTH_USER_MODEL = 'users.User'

# When should the session expire if the user has requested that we remember
# them?
SESSION_COOKIE_AGE_REMEMBER_ME = 7 * 24 * 3600  # 7 days
# Expiration time when "remember me" is not requested
SESSION_COOKIE_AGE = 30 * 60  # 30 mins

# ID Tokens should expire no later than SESSION_COOKIE_AGE
OIDC_IDTOKEN_EXPIRE = SESSION_COOKIE_AGE
# Access tokens should expire at the same time with the ID Token.
# They can be refreshed with a) the refresh token or b) silent renewal
OIDC_TOKEN_EXPIRE = OIDC_IDTOKEN_EXPIRE



MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'npm.finders.NpmFinder',
    'compressor.finders.CompressorFinder',
)

STATIC_ROOT = env("STATIC_ROOT")
STATIC_URL = env('STATIC_URL')

MEDIA_ROOT = env("MEDIA_ROOT")
MEDIA_URL = env('MEDIA_URL')

NODE_MODULES_PATH = env("NODE_MODULES_ROOT")
STATICFILES_DIRS = [
    ('styles', os.path.join(BASE_DIR, 'themes', 'styles')),
]

SVG_DIRS = [
    os.path.join(NODE_MODULES_PATH, 'simple-icons', 'icons'),
    os.path.join(BASE_DIR, 'themes', 'static', 'svg'),
]

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', '%s/.bin/node-sass --importer=%s/node-sass-tilde-importer {infile} {outfile}' % (NODE_MODULES_PATH, NODE_MODULES_PATH)),  # noqa
)

# Bootstrap is included through our main style file
BOOTSTRAP4 = {
    'css_url': None,
    'javascript_url': None,
    'include_jquery': False,
    'success_css_class': None,
}

NPM_FILE_PATTERNS = {
    'bootstrap': ['dist/js/*', 'scss/*'],
    'open-city-design': ['src/assets/*']
}


SITE_ID = 1

PARLER_LANGUAGES = {SITE_ID: [{'code': code} for (code, name) in LANGUAGES]}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(module)s %(asctime)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'generic': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'requests': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'sorl.thumbnail': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}

CORS_ORIGIN_ALLOW_ALL = False
CORS_URLS_REGEX = r'.*/(\.well-known/openid-configuration|v1|openid|api-tokens|jwt-token).*'


OAUTH2_PROVIDER_APPLICATION_MODEL = 'users.Application'
OAUTH2_PROVIDER = {
    'CLIENT_SECRET_GENERATOR_LENGTH': 96,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

COOKIE_PREFIX = 'sso'  # FIXME: get from env
CSRF_COOKIE_NAME = '%s-csrftoken' % COOKIE_PREFIX
SESSION_COOKIE_NAME = '%s-sessionid' % COOKIE_PREFIX
LANGUAGE_COOKIE_NAME = '%s-ui-language' % COOKIE_PREFIX

# Disable the SameSite parameter for cookies. Silent renew relies on iframes,
# so the new Django default of 'SameSite=lax' breaks the functionality. This
# will need to be revisited before Chrome 80 is out, because then Chrome will
# default to 'SameSite=lax' if the parameter is missing.
SESSION_COOKIE_SAMESITE = None
# Make sure cookies are only being sent through encrypted protocols by default.
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Enable various protections in SecureMiddleware
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 365 * 24 * 3600  # One year

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_AUTHENTICATION_METHOD = 'email'

ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_UNIQUE_EMAIL = True

# django-oidc-provider settings for OpenID Connect support
OIDC_USERINFO = 'tunnistamo.oidc.get_userinfo'
OIDC_IDTOKEN_INCLUDE_CLAIMS = True
OIDC_IDTOKEN_SUB_GENERATOR = 'tunnistamo.oidc.sub_generator'
OIDC_EXTRA_SCOPE_CLAIMS = 'oidc_apis.scopes.CombinedScopeClaims'
OIDC_AFTER_USERLOGIN_HOOK = 'oidc_apis.utils.after_userlogin_hook'

# key_manager settings for RSA Key
KEY_MANAGER_RSA_KEY_LENGTH = 4096
KEY_MANAGER_RSA_KEY_MAX_AGE = 3 * 30
KEY_MANAGER_RSA_KEY_EXPIRATION_PERIOD = 7


TEST_NON_SERIALIZED_APPS = ['adfs_provider']


#
# Caching
#
CACHES = {
    'default': env.cache('CACHE_URL')
}


# Social Auth
SOCIAL_AUTH_PIPELINE = (
    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. On some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    'social_core.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    'social_core.pipeline.social_auth.social_uid',

    # Verifies that the current auth process is valid within the current
    # project, this is where emails and domains whitelists are applied (if
    # defined).
    'social_core.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated in the site.
    'social_core.pipeline.social_auth.social_user',


    # Add `new_uuid` argument to the pipeline.
    'users.pipeline.get_user_uuid',
    # Sets the `username` argument.
    'users.pipeline.get_username',
    # Enforce email address.
    'users.pipeline.require_email',
    # Deny duplicate email or associate to an existing user by email
    'users.pipeline.associate_by_email',

    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    # 'social_core.pipeline.user.get_username',

    # Send a validation email to the user to verify its email address.
    # 'social_core.pipeline.mail.mail_validation',

    # Associates the current social details with another user account with
    # a similar email address.
    # 'social_core.pipeline.social_auth.associate_by_email',

    # Create a user account if we haven't found one yet.
    'social_core.pipeline.user.create_user',

    # Verify that the user doesn't have existing social account with another provider.
    'users.pipeline.check_existing_social_associations',

    # Create the record that associated the social account with this user.
    'social_core.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social_core.pipeline.social_auth.load_extra_data',

    # Update the user record with any changed info from the auth service.
    'social_core.pipeline.user.user_details',

    # Update AD groups
    'users.pipeline.update_ad_groups',

    # Save last login backend to user data
    'users.pipeline.save_social_auth_backend'
)

SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ['email', 'first_name', 'last_name']

SOCIAL_AUTH_FACEBOOK_KEY = env("SOCIAL_AUTH_FACEBOOK_KEY")
SOCIAL_AUTH_FACEBOOK_SECRET = env("SOCIAL_AUTH_FACEBOOK_SECRET")
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'public_profile']
# Request that Facebook includes email address in the returned details
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id,name,email',
}
# Allow setting the auth_type in GET parameters
SOCIAL_AUTH_FACEBOOK_AUTH_EXTRA_ARGUMENTS = {'auth_type': ''}

SOCIAL_AUTH_GITHUB_KEY = env("SOCIAL_AUTH_GITHUB_KEY")
SOCIAL_AUTH_GITHUB_SECRET = env("SOCIAL_AUTH_GITHUB_SECRET")
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']

SOCIAL_AUTH_GOOGLE_KEY = env("SOCIAL_AUTH_GOOGLE_KEY")
SOCIAL_AUTH_GOOGLE_SECRET = env("SOCIAL_AUTH_GOOGLE_SECRET")
SOCIAL_AUTH_GOOGLE_SCOPE = ['email']
SOCIAL_AUTH_GOOGLE_USE_UNIQUE_USER_ID = True

SOCIAL_AUTH_HELSINKI_ADFS_KEY = env("SOCIAL_AUTH_HELSINKI_ADFS_KEY")
SOCIAL_AUTH_HELSINKI_ADFS_SECRET = env("SOCIAL_AUTH_HELSINKI_ADFS_SECRET")

SOCIAL_AUTH_ESPOO_ADFS_KEY = env("SOCIAL_AUTH_ESPOO_ADFS_KEY")
SOCIAL_AUTH_ESPOO_ADFS_SECRET = env("SOCIAL_AUTH_ESPOO_ADFS_SECRET")

###
# The following section contains values required by Social Auth Suomi.fi
# authentication.

# Suomi.fi common values.
# Values for these come from Suomi.fi requirements and/or service metadata.

# Suomi.fi requires that all SAML messages and assertions are signed.
SOCIAL_AUTH_SUOMIFI_SECURITY_CONFIG = {'authnRequestsSigned': True,
                                       'logoutRequestSigned': True,
                                       'logoutResponseSigned': True,
                                       'wantAssertionsSigned': True}
# A list of user attributes Suomi.fi provides on concise level.
SOCIAL_AUTH_SUOMIFI_SP_EXTRA = {
    'NameIDFormat': 'urn:oasis:names:tc:SAML:2.0:nameid-format:transient',
    'attributeConsumingService': {
        'serviceName': 'Tunnistamo',
        'requestedAttributes': [{'friendlyName': 'electronicIdentificationNumber',
                                 'name': 'urn:oid:1.2.246.22'},
                                {'friendlyName': 'nationalIdentificationNumber',
                                 'name': 'urn:oid:1.2.246.21'},
                                {'friendlyName': 'cn',
                                 'name': 'urn:oid:2.5.4.3'},
                                {'friendlyName': 'displayName',
                                 'name': 'urn:oid:2.16.840.1.113730.3.1.241'},
                                {'friendlyName': 'givenName',
                                 'name': 'urn:oid:2.5.4.42'},
                                {'friendlyName': 'sn',
                                 'name': 'urn:oid:2.5.4.4'},
                                {'friendlyName': 'FirstName',
                                 'name': 'http://eidas.europa.eu/attributes/naturalperson/CurrentGivenName'},
                                {'friendlyName': 'KotikuntaKuntanumero',
                                 'name': 'urn:oid:1.2.246.517.2002.2.18'},
                                {'friendlyName': 'KotikuntaKuntaS',
                                 'name': 'urn:oid:1.2.246.517.2002.2.19'},
                                {'friendlyName': 'KotikuntaKuntaR',
                                 'name': 'urn:oid:1.2.246.517.2002.2.20'},
                                {'friendlyName': 'VakinainenKotimainenLahiosoiteS',
                                 'name': 'urn:oid:1.2.246.517.2002.2.4'},
                                {'friendlyName': 'VakinainenKotimainenLahiosoiteR',
                                 'name': 'urn:oid:1.2.246.517.2002.2.5'},
                                {'friendlyName': 'VakinainenKotimainenLahiosoitePostinumero',
                                 'name': 'urn:oid:1.2.246.517.2002.2.6'},
                                {'friendlyName': 'VakinainenKotimainenLahiosoitePostitoimipaikkaS',
                                 'name': 'urn:oid:1.2.246.517.2002.2.7'},
                                {'friendlyName': 'VakinainenKotimainenLahiosoitePostitoimipaikkaR',
                                 'name': 'urn:oid:1.2.246.517.2002.2.8'},
                                {'friendlyName': 'VakinainenUlkomainenLahiosoite',
                                 'name': 'urn:oid:1.2.246.517.2002.2.11'},
                                {'friendlyName': 'VakinainenUlkomainenLahiosoitePaikkakuntaJaValtioS',
                                 'name': 'urn:oid:1.2.246.517.2002.2.12'},
                                {'friendlyName': 'VakinainenUlkomainenLahiosoitePaikkakuntaJaValtioR',
                                 'name': 'urn:oid:1.2.246.517.2002.2.13'},
                                {'friendlyName': 'VakinainenUlkomainenLahiosoitePaikkakuntaJaValtioSelvakielinen',
                                 'name': 'urn:oid:1.2.246.517.2002.2.14'},
                                {'friendlyName': 'VakinainenUlkomainenLahiosoiteValtiokoodi',
                                 'name': 'urn:oid:1.2.246.517.2002.2.15'},
                                {'friendlyName': 'TilapainenKotimainenLahiosoiteS',
                                 'name': 'urn:oid:1.2.246.517.2002.2.31'},
                                {'friendlyName': 'TilapainenKotimainenLahiosoiteR',
                                 'name': 'urn:oid:1.2.246.517.2002.2.32'},
                                {'friendlyName': 'TilapainenKotimainenLahiosoitePostinumero',
                                 'name': 'urn:oid:1.2.246.517.2002.2.33'},
                                {'friendlyName': 'TilapainenKotimainenLahiosoitePostitoimipaikkaS',
                                 'name': 'urn:oid:1.2.246.517.2002.2.34'},
                                {'friendlyName': 'TilapainenKotimainenLahiosoitePostitoimipaikkaR',
                                 'name': 'urn:oid:1.2.246.517.2002.2.35'},
                                {'friendlyName': 'mail',
                                 'name': 'urn:oid:0.9.2342.19200300.100.1.3'}]
    },
}
# Accepted Suomi.fi authentication methods.
SOCIAL_AUTH_SUOMIFI_ENTITY_ATTRIBUTES = [
    {
        'name': 'FinnishAuthMethod',
        'nameFormat': 'urn:oasis:names:tc:SAML:2.0:attrname-format:uri',
        'values': [
            'http://ftn.ficora.fi/2017/loa3',
            'http://eidas.europa.eu/LoA/high',
            'http://ftn.ficora.fi/2017/loa2',
            'http://eidas.europa.eu/LoA/substantial',
            'urn:oid:1.2.246.517.3002.110.5',
            'urn:oid:1.2.246.517.3002.110.6',
            # 'urn:oid:1.2.246.517.3002.110.999'  # Test authentication service
        ]
    },
    {
        'friendlyName': 'VthVerificationRequired',
        'name': 'urn:oid:1.2.246.517.3003.111.3',
        'nameFormat': 'urn:oasis:names:tc:SAML:2.0:attrname-format:uri',
        'values': ['false']
    },
    {
        'friendlyName': 'SkipEndpointValidationWhenSigned',
        'name': 'urn:oid:1.2.246.517.3003.111.4',
        'nameFormat': 'urn:oasis:names:tc:SAML:2.0:attrname-format:uri',
        'values': ['true']
    },
    {
        'friendlyName': 'EidasSupport',
        'name': 'urn:oid:1.2.246.517.3003.111.14',
        'nameFormat': 'urn:oasis:names:tc:SAML:2.0:attrname-format:uri',
        'values': ['full']
    },
]

# Suomi.fi instance specific values.
# These should be overwritten in local settings.

# Service provider (Tunnistamo) entity ID and certificates.
SOCIAL_AUTH_SUOMIFI_SP_ENTITY_ID = env("SOCIAL_AUTH_SUOMIFI_SP_ENTITY_ID")
SOCIAL_AUTH_SUOMIFI_SP_PUBLIC_CERT = env("SOCIAL_AUTH_SUOMIFI_SP_PUBLIC_CERT")
SOCIAL_AUTH_SUOMIFI_SP_PRIVATE_KEY = env("SOCIAL_AUTH_SUOMIFI_SP_PRIVATE_KEY")

# Organization (hel.fi/tunnistamo) details must be given for languages fi/sv/en.
SOCIAL_AUTH_SUOMIFI_ORG_INFO = env.json("SOCIAL_AUTH_SUOMIFI_ORG_INFO")
if not SOCIAL_AUTH_SUOMIFI_ORG_INFO:
    SOCIAL_AUTH_SUOMIFI_ORG_INFO = {'fi': {'name': '', 'displayname': '', 'url': ''},
                                    'sv': {'name': '', 'displayname': '', 'url': ''},
                                    'en': {'name': '', 'displayname': '', 'url': ''}}

# Both technical and support contact information are required.
# First name and surname must be given separately.
SOCIAL_AUTH_SUOMIFI_TECHNICAL_CONTACT = env.json("SOCIAL_AUTH_SUOMIFI_TECHNICAL_CONTACT")
if not SOCIAL_AUTH_SUOMIFI_TECHNICAL_CONTACT:
    SOCIAL_AUTH_SUOMIFI_TECHNICAL_CONTACT = {'givenName': '', 'surName': '', 'emailAddress': ''}
SOCIAL_AUTH_SUOMIFI_SUPPORT_CONTACT = env.json("SOCIAL_AUTH_SUOMIFI_SUPPORT_CONTACT")
if not SOCIAL_AUTH_SUOMIFI_SUPPORT_CONTACT:
    SOCIAL_AUTH_SUOMIFI_SUPPORT_CONTACT = {'givenName': '', 'surName': '', 'emailAddress': ''}

# Suomi.fi identity provider information.
# These values can be obtained from Suomi.fi IdP metadata.
SOCIAL_AUTH_SUOMIFI_ENABLED_IDPS = env.json("SOCIAL_AUTH_SUOMIFI_ENABLED_IDPS")
if not SOCIAL_AUTH_SUOMIFI_ENABLED_IDPS:
    SOCIAL_AUTH_SUOMIFI_ENABLED_IDPS = {
        'suomifi': {
            'entity_id': '',  # IdP URI
            'url': '',  # SSO URL
            'logout_url': '',  # SLO URL
            'x509cert': '',  # IdP certificate
            # Social Core attribute bindings
            'attr_user_permanent_id': 'urn:oid:1.2.246.21',
            'attr_full_name': 'urn:oid:2.5.4.3',
            'attr_first_name': 'http://eidas.europa.eu/attributes/naturalperson/CurrentGivenName',
            'attr_last_name': 'urn:oid:2.5.4.4',
            'attr_username': 'urn:oid:1.2.246.21',
            'attr_email': 'urn:oid:0.9.2342.19200300.100.1.3',
        }
    }

# UI configuration hints for Suomi.fi. Suomi.fi authentication selection page
# uses this information for UI customization. Required languages are fi/sv/en.
SOCIAL_AUTH_SUOMIFI_UI_INFO = env.json("SOCIAL_AUTH_SUOMIFI_UI_INFO")
if not SOCIAL_AUTH_SUOMIFI_UI_INFO:
    SOCIAL_AUTH_SUOMIFI_UI_INFO = {
        'fi': {'DisplayName': '', 'Description': '', 'PrivacyStatementURL': ''},
        'sv': {'DisplayName': '', 'Description': '', 'PrivacyStatementURL': ''},
        'en': {'DisplayName': '', 'Description': '', 'PrivacyStatementURL': ''},
    }
SOCIAL_AUTH_SUOMIFI_UI_LOGO = env.json("SOCIAL_AUTH_SUOMIFI_UI_LOGO")
if not SOCIAL_AUTH_SUOMIFI_UI_LOGO:
    SOCIAL_AUTH_SUOMIFI_UI_LOGO = {'url': '', 'height': None, 'width': None}

# End of Suomi.fi section
###

IPWARE_META_PRECEDENCE_ORDER = env('IPWARE_META_PRECEDENCE_ORDER')

CONTENT_SECURITY_POLICY = {
    # The full policy including report-uri and/or report-to specification.
    'policy': None,
    # Whether to use the report only header instead of the enforcing header.
    'report_only': False,
    # If the policy contains a report-to specification, the corresponding
    # group must be defined here
    'report_groups': {},
}

# Turku-specific settings
SOCIAL_AUTH_AXIELL_AURORA_API_URL = env("SOCIAL_AUTH_AXIELL_AURORA_API_URL")
SOCIAL_AUTH_AXIELL_AURORA_API_USERNAME = env("SOCIAL_AUTH_AXIELL_AURORA_API_USERNAME")
SOCIAL_AUTH_AXIELL_AURORA_API_PASSWORD = env("SOCIAL_AUTH_AXIELL_AURORA_API_PASSWORD")
SOCIAL_AUTH_TURKU_SUOMIFI_API_URL = env("SOCIAL_AUTH_TURKU_SUOMIFI_API_URL")
SOCIAL_AUTH_TURKU_SUOMIFI_API_KEY = env("SOCIAL_AUTH_TURKU_SUOMIFI_API_KEY")
SOCIAL_AUTH_TURKU_SUOMIFI_SP_NAME = 'Tunnistamo'
SOCIAL_AUTH_TURKU_ADFS_TECHNICAL_CONTACT = {
    'givenName': 'Technical Contact',
    'emailAddress': 'turun.kaupunki@turku.fi',
}
SOCIAL_AUTH_TURKU_ADFS_SUPPORT_CONTACT = {
    'givenName': 'Support Contact',
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
SOCIAL_AUTH_TURKU_ADFS_SP_ENTITY_ID = env("SOCIAL_AUTH_TURKU_ADFS_SP_ENTITY_ID")
if env("SKIP_CERTIFICATES") != "true":
    SOCIAL_AUTH_TURKU_ADFS_SP_PUBLIC_CERT = open(os.path.join(BASE_DIR, 'certs', 'turku_adfs.crt')).read()
    SOCIAL_AUTH_TURKU_ADFS_SP_PRIVATE_KEY = open(os.path.join(BASE_DIR, 'certs', 'turku_adfs.key')).read()
SOCIAL_AUTH_OPAS_ADFS_TECHNICAL_CONTACT = {
    'givenName': 'Technical Contact',
    'emailAddress': 'turun.kaupunki@turku.fi',
}
SOCIAL_AUTH_OPAS_ADFS_SUPPORT_CONTACT = {
    'givenName': 'Support Contact',
    'emailAddress': 'turun.kaupunki@turku.fi',
}
SOCIAL_AUTH_OPAS_ADFS_ORG_INFO = {
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
SOCIAL_AUTH_OPAS_ADFS_SP_ENTITY_ID = env("SOCIAL_AUTH_OPAS_ADFS_SP_ENTITY_ID")
if env("SKIP_CERTIFICATES") != "true":
    SOCIAL_AUTH_OPAS_ADFS_SP_PUBLIC_CERT = open(os.path.join(BASE_DIR, 'certs', 'turku_adfs.crt')).read()
    SOCIAL_AUTH_OPAS_ADFS_SP_PRIVATE_KEY = open(os.path.join(BASE_DIR, 'certs', 'turku_adfs.key')).read()
SOCIAL_AUTH_KOHA_API_URL = 'https://vaski.koha-suomi.fi/api/v1'
SOCIAL_AUTH_FOLI_API_URL = 'https://nettilataus.turku.fi/netloading-svc/api'
KOHA_OAUTH_CLIENT_ID = env("KOHA_OAUTH_CLIENT_ID")
KOHA_OAUTH_CLIENT_API_KEY = env("KOHA_OAUTH_CLIENT_API_KEY")
SOCIAL_AUTH_FOLI_API_ID = env("SOCIAL_AUTH_FOLI_API_ID")
SOCIAL_AUTH_FOLI_API_KEY = env("SOCIAL_AUTH_FOLI_API_KEY")
# End of Turku-specific settings

# local_settings.py can be used to override environment-specific settings
# like database and email that differ between development and production.
local_settings_path = os.path.join(BASE_DIR, "local_settings.py")
if os.path.exists(local_settings_path):
    import sys
    import types
    module_name = "%s.local_settings" % ROOT_URLCONF.split('.')[0]
    module = types.ModuleType(module_name)
    module.__file__ = local_settings_path
    sys.modules[module_name] = module
    with open(local_settings_path, "rb") as f:
        exec(f.read())

if 'SECRET_KEY' not in locals():
    secret_file = os.path.join(BASE_DIR, '.django_secret')
    try:
        with open(secret_file) as f:
            SECRET_KEY = f.read().strip()
    except IOError:
        SECRET_KEY = env("SECRET_KEY")
        if not SECRET_KEY:
            import random
            system_random = random.SystemRandom()
            try:
                SECRET_KEY = ''.join(
                    [system_random.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(64)])
                with open(secret_file, 'w') as f:
                    import os
                    os.fchmod(f.fileno(), 0o0600)
                    f.write(SECRET_KEY)
                    f.close()
            except IOError:
                Exception('Please create a %s file with random characters to generate your secret key!' % secret_file)