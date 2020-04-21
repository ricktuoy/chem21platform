import os
from boto.s3.connection import OrdinaryCallingFormat

from django.utils.crypto import get_random_string
from chem21repo.repo.settings import *

# Application definition

YOUTUBE_BASE = "https://www.youtube.com/"
YOUTUBE_URL_TEMPLATE = YOUTUBE_BASE + "watch?v=%s&controls=1&preload=none"

# Amazon Elastic Beanstalk settings

# whether should be viewable at .elasticbeanstalk.com domain
AWS_EB_TEST = os.environ.get("DJANGO_AWS_EB_TEST", False)
DEBUG = True if os.environ.get("DJANGO_DEBUG", False) else False

INSTALLED_APPS = (
    'grappelli',
    'filebrowser',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chem21repo.repo',
    'chem21repo.chem21',
    'chem21repo.quiz',
    'querystring_parser',
    'revproxy',
    'bibliotag',
    'figuretag',
    'linktag',
    'widget_tweaks',
    'social_django',
)


MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'chem21repo.middleware.C21AdminMiddleware',
    'chem21repo.middleware.C21StaticGenMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'chem21repo.middleware.C21ReturnURIMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware'
)

ROOT_URLCONF = 'chem21repo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'chem21repo.context_processors.page_admin_menu',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

TEMPLATE_CONTEXT_PROCESSORS = (
    'social_django.context_processors.backends',
    'social_django.context_processors.login_redirect',
    'chem21repo.context_processors.page_admin_menu',
    'django.core.context_processors.request'
)

WSGI_APPLICATION = 'chem21repo.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'GMT'
USE_I18N = True
USE_L10N = True
USE_TZ = False

# AWS setup

AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION_NAME = os.environ.get("AWS_STORAGE_REGION", None)

# Amazon S3 settings.

AWS_AUTO_CREATE_BUCKET = False
AWS_HEADERS = {
    "Cache-Control": "public, max-age=86400",
}
#AWS_S3_SIGNATURE_VERSION = os.environ.get("AWS_S3_SIGNATURE_VERSION",'s3v4') 
AWS_S3_FILE_OVERWRITE = True

if "AWS_S3_CUSTOM_DOMAIN" in os.environ:
    AWS_S3_CUSTOM_DOMAIN = "learning.chem21.eu"
    AWS_S3_CALLING_FORMAT = OrdinaryCallingFormat()

AWS_QUERYSTRING_AUTH = False
AWS_REDUCED_REDUNDANCY = False
AWS_IS_GZIPPED = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

REQUIRE_BASE_URL = 'js/lib'

S3_URL = 'https://%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

MEDIA_ROOT = '/media/'
MEDIA_URL = S3_URL + MEDIA_ROOT

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.environ.get("SECRET_KEY", get_random_string(
    50, "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"))

# Use Amazon S3 for storage for uploaded media files.
DEFAULT_FILE_STORAGE = "chem21repo.storage.MediaRootS3BotoStorage"
PUBLIC_SITE_STORAGE = 'chem21repo.storage.SiteRootStorage'

CHEM21_PLATFORM_BASE_URL = 'http://test-chem21-elearning.pantheonsite.io'
CHEM21_PLATFORM_REST_API_URL = '/rest'
CHEM21_PLATFORM_API_USER = 'admin'
CHEM21_PLATFORM_API_PWD = '#'

CITEPROC_DEFAULT_STYLE = "royal-society-of-chemistry"

CITEPROC_CSL_PATH = os.path.join(BASE_DIR, 'csl')
CITEPROC_DEFAULT_STYLE_PATH = os.path.join(
    CITEPROC_CSL_PATH,
    CITEPROC_DEFAULT_STYLE + ".csl")

AUTHENTICATION_BACKENDS = (
    'chem21repo.auth.backends.LocalGoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend'
)
GOOGLE_OAUTH2_KEY = SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get(
    "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
GOOGLE_OAUTH2_SECRET = SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get(
    "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", "")

LOGIN_URL = '/login/google-oauth2/'
LOGIN_REDIRECT_URL = '/'
LOGIN_ERROR_URL = '/login-error/'


SERIALIZATION_MODULES = {
    'json': 'chem21repo.serializers.json',
    'json-files': 'chem21repo.serializers.json-files'
}

SOCIAL_AUTH_COMPLETE_URL_NAME = 'socialauth_complete'
SOCIAL_AUTH_ASSOCIATE_URL_NAME = 'socialauth_associate_complete'
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True

WEB_ROOT = ''

ALLOWED_HOSTS = [".chem21.eu", "localhost"]

if AWS_EB_TEST:
    ALLOWED_HOSTS += [".elasticbeanstalk.com","172.31.2.191"]

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

    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    'social_core.pipeline.user.get_username',

    # No validation email
    # 'social_core.pipeline.mail.mail_validation',

    # Associates the current social details with another user account with
    # a similar email address. Disabled by default.
    'social_core.pipeline.social_auth.associate_by_email',

    # Never create a new user account
    #'social_core.pipeline.user.create_user',

    # Create the record that associates the social account with the user.
    'social_core.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social_core.pipeline.social_auth.load_extra_data',

    # Update the user record with any changed info from the auth service.
    'social_core.pipeline.user.user_details',
)