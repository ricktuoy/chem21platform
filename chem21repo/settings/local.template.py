from django.core.exceptions import ImproperlyConfigured

from common import *
from auth import *
import os

if 'RDS_DB_NAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
else:
    raise ImproperlyConfigured(
        "No RDS_DB_NAME environment configured. Have you added postgres DB variables to your environment?")

STATIC_URL = S3_URL + "/static/"
STATIC_ROOT = BASE_DIR + "/../collected-static/src"
TINYMCE_JS_URL = "/s3/tiny_mce/tiny_mce.js"

# Cache settings.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    # Long cache timeout for staticfiles, since this is used heavily by the
    # optimizing storage.
    "staticfiles": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "TIMEOUT": 60 * 60 * 24 * 365,
        "LOCATION": "staticfiles",
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
        }
    }
}
