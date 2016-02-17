from common import *
import dj_database_url
DATABASES = {
    "default": dj_database_url.config(default='postgres://localhost'),
}

REQUIRE_BUILD_PROFILE = 'chem21repo.build.js'
# Use Amazon S3 for static files storage.
STATIC_URL = S3_URL +"/"
STATICFILES_STORAGE = "chem21repo.storage.TinyMCEProxyCachedS3BotoStorage"


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

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
