from cachedS3.storage import CachedS3BotoStorage

MediaRootS3BotoStorage = lambda: CachedS3BotoStorage(location='media/')
