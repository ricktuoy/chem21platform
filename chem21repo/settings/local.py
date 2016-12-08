from common import *
import os
DEBUG = True
TEMPLATE_DEBUG = True
DEBUG_TOOLBAR = True

STATIC_ROOT = BASE_DIR + '/../static/'
PUBLIC_SITE_ROOT = BASE_DIR + '/../site/'
STATIC_URL = "/static/"
PUBLIC_SITE_URL = "http://127.0.0.1:8999"
STATICFILES_STORAGE = 'require.storage.OptimizedStaticFilesStorage'
SHARED_DRIVE_STORAGE = 'chem21repo.storage.SharedMediaStorage'
SHARED_DRIVE_ROOT = "/home/rick/shared_drive"
SHARED_DRIVE_URL = "/shared"

ALLOWED_HOSTS = ['localhost', "10.0.2.2", "10.0.2.2:8080",
                 'localhost:8080', '127.0.0.1', '127.0.0.1:8080']


REQUIRE_BUILD_PROFILE = '../chem21repo.dev.build.js'


INTERNAL_IPS = ("localhost", "10.0.2.2", "10.0.2.2:8080",
                "127.0.0.1", "localhost:8080", "127.0.0.1:8080")

DATABASES = {
    "default":  {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'chem21',
        'USER': 'rick',
        'HOST': 'localhost',
        'PASSWORD': '9chard87'
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.file"

if DEBUG_TOOLBAR:
    INSTALLED_APPS += ('debug_toolbar',)
    DEBUG_TOOLBAR_PATCH_SETTINGS = False
    MIDDLEWARE_CLASSES = ('debug_toolbar.middleware.DebugToolbarMiddleware',
    ) + MIDDLEWARE_CLASSES
    #DEBUG_TOOLBAR_CONFIG = {
    #    'SHOW_TOOLBAR_CALLBACK': 'chem21repo.middleware.show_toolbar',
    #}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'incremental': True,
    'root': {
        'level': 'DEBUG',
    },
}
