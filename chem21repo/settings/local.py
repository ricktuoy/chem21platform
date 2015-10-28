from common import *
import os
DEBUG = True
TEMPLATE_DEBUG = True

STATIC_ROOT = BASE_DIR+'/../static/'
STATIC_URL = "/static/"
STATICFILES_STORAGE = 'require.storage.OptimizedStaticFilesStorage'

ALLOWED_HOSTS = ['localhost','localhost:8080','127.0.0.1','127.0.0.1:8080']
INSTALLED_APPS += ('debug_toolbar',)
DEBUG_TOOLBAR_PATCH_SETTINGS = False

REQUIRE_BUILD_PROFILE = 'chem21repo.dev.build.js'

MIDDLEWARE_CLASSES = (
    # ...
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # ...
) + MIDDLEWARE_CLASSES

INTERNAL_IPS = ("localhost", "127.0.0.1", "localhost:8080", "127.0.0.1:8080")

DATABASES = {
    "default":  {
    	'ENGINE': 'django.db.backends.sqlite3',
    	'NAME': os.path.join(BASE_DIR, 'repo.db')
    }
}
