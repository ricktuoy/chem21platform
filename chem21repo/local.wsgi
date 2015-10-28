"""
WSGI config for chem21 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chem21repo.settings")
os.environ.setdefault("AWS_ACCESS_KEY_ID","AKIAIKJHTIHD6APQCPJA")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY","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")
os.environ.setdefault("AWS_STORAGE_BUCKET_NAME","chem21repo")
os.environ.setdefault("DJANGO_DEVELOPMENT","1")
	
application = get_wsgi_application()
