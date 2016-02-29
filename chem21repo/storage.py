from cachedS3.storage import CachedS3BotoStorage
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import grp
import tempfile
from django.core.files.storage import DefaultStorage
from django.core.urlresolvers import reverse
from require_s3.storage import OptimizedCachedStaticFilesStorage


class TinyMCEProxyCachedS3BotoStorage(OptimizedCachedStaticFilesStorage):
    def url(self, *args, **kwargs):
        url = super(TinyMCEProxyCachedS3BotoStorage, self).url(*args, **kwargs)
        if "tiny_mce" in url or "tinymce" in url:
            url = reverse(
                "s3_proxy", kwargs={'path': url.replace(settings.S3_URL + "/", "")})
        return url


class MediaRootS3BotoStorage(CachedS3BotoStorage):
    def __init__(self, *args, **kwargs):
        kwargs['location'] = 'media/'
        return super(MediaRootS3BotoStorage, self).__init__(*args, **kwargs)

    def isdir(self, path):
        path = self._clean_name(path)
        path = path.rstrip("/")
        return super(MediaRootS3BotoStorage, self).isdir(path)

    def listdir(self, path):
        path = self._clean_name(path)
        path = path.rstrip("/")
        return super(MediaRootS3BotoStorage, self).listdir(path)


try:
    SharedMediaStorage = lambda: FileSystemStorage(
        location=settings.SHARED_DRIVE_ROOT, base_url=settings.SHARED_DRIVE_URL)
except AttributeError:
    pass

SiteRootS3BotoStorage = lambda: CachedS3BotoStorage(location='site/')


class S3StaticFileSystem(object):

    def __init__(self, storage=SiteRootS3BotoStorage()):
        self.storage = storage

    def exists(self, path):
        return self.storage.exists(path)

    def makedirs(self, path):
        self.storage.makedirs(path)

    def chown_group(self, path, groupname):
        return None

    def tempfile(self, directory):
        filename = "TEMP.html"
        path = os.path.join(directory, filename)
        print "Path %s" % path
        f = self.storage.open(path, 'w')
        return (f, path)

    def write(self, f, content):
        try:
            return f.write(content)
        except TypeError:
            print "No content to write"
            return f

    def close(self, f):
        try:
            f.close()
        except:
            print "File not closed"

    def chmod(self, filename, flags):
        return None
        # os.chmod(filename, flags)

    def rename(self, from_file, to_file):
        print str(from_file) + ":" + str(to_file)
        try:
            self.storage.move(from_file, to_file, True)
        except OSError:
            print "Failed to move %s to %s" % (from_file, to_file)

    def remove(self, path):
        self.storage.remove(path)

    def rmdir(self, directory):
        self.storage.rmdir(directory)

    def join(self, *paths):
        if not paths:
            return ""
        return os.path.join(paths[0], *[path.lstrip("/") for path in paths[1:]])

    def dirname(self, path):
        return os.path.dirname(path)
