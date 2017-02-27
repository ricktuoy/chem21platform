import os
from boto.s3.connection import OrdinaryCallingFormat

from django.utils.crypto import get_random_string

# Application definition

YOUTUBE_BASE = "https://www.youtube.com/"
YOUTUBE_URL_TEMPLATE = YOUTUBE_BASE + "watch?v=%s&controls=1&preload=none"

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
    'require',
    'cachedS3',
    'querystring_parser',
    'revproxy',
    'bibliotag',
    'figuretag',
    'linktag',
    'social.apps.django_app.default',
    'widget_tweaks'
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
    'django.middleware.security.SecurityMiddleware',
    #'social_auth.middleware.SocialAuthExceptionMiddleware'
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
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

TEMPLATE_CONTEXT_PROCESSORS = (
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
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

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION = os.environ.get("AWS_STORAGE_REGION", None)

# Amazon S3 settings.

AWS_AUTO_CREATE_BUCKET = False
AWS_HEADERS = {
    "Cache-Control": "public, max-age=86400",
}
AWS_S3_FILE_OVERWRITE = True
AWS_S3_CALLING_FORMAT = OrdinaryCallingFormat()
AWS_S3_CUSTOM_DOMAIN = "learning.chem21.eu"

AWS_QUERYSTRING_AUTH = False
AWS_S3_SECURE_URLS = False
AWS_REDUCED_REDUNDANCY = False
AWS_IS_GZIPPED = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

REQUIRE_BASE_URL = 'js/lib'

S3_URL = 'http://%s' % AWS_STORAGE_BUCKET_NAME

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
    'social.backends.google.GoogleOAuth2',
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

SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_EMAILS = [
    'rick.taylor@york.ac.uk',
    'louise.summerton@york.ac.uk',
    'james.sherwood@york.ac.uk',
    'jobie.kirkwood@york.ac.uk']

WEB_ROOT = ''
