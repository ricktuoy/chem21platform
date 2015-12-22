from cachedS3.storage import CachedS3BotoStorage
from django.core.files.storage import FileSystemStorage
from django.conf import settings

MediaRootS3BotoStorage = lambda: CachedS3BotoStorage(location='media/')
try:
    SharedMediaStorage = lambda: FileSystemStorage(
        location=settings.SHARED_DRIVE_ROOT, base_url=settings.SHARED_DRIVE_URL)
except AttributeError:
    pass
