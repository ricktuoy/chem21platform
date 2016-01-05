import os

from django.utils.crypto import get_random_string
# Application definition

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
    'require',
    'cachedS3',
    'querystring_parser',
    'tinymce',
    'bibliotag'
)


MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'chem21repo.middleware.C21AdminMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
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

WSGI_APPLICATION = 'chem21repo.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'GMT'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# AWS setup

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")

# Amazon S3 settings.

AWS_AUTO_CREATE_BUCKET = True
AWS_HEADERS = {
    "Cache-Control": "public, max-age=86400",
}
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = False
AWS_S3_SECURE_URLS = True
AWS_REDUCED_REDUNDANCY = False
AWS_IS_GZIPPED = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)


REQUIRE_BASE_URL = 'js/lib'

S3_URL = 'http://%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

MEDIA_ROOT = '/media/'
MEDIA_URL = S3_URL + MEDIA_ROOT

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.environ.get("SECRET_KEY", get_random_string(
    50, "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"))

# Use Amazon S3 for storage for uploaded media files.
DEFAULT_FILE_STORAGE = "chem21repo.storage.MediaRootS3BotoStorage"

CHEM21_PLATFORM_BASE_URL = 'http://test-chem21-elearning.pantheon.io'
CHEM21_PLATFORM_REST_API_URL = '/rest'
CHEM21_PLATFORM_API_USER = 'admin'
CHEM21_PLATFORM_API_PWD = '9chard87'

TINYMCE_DEFAULT_CONFIG = {
    'plugins': "table,spellchecker,paste,searchreplace,bibliotag",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 10,
    'theme' : "advanced",
    'theme_advanced_buttons1' : "bold,italic,underline,link,unlink,bullist,blockquote,undo,bibliotag", 
    'theme_advanced_buttons2' : "", 
    'theme_advanced_buttons3' : "" 
}
TINYMCE_SPELLCHECKER = True
