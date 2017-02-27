import base64
import json
import mimetypes
import os

from .media import UniqueFile
from django.conf import settings
from django.core.files import get_storage_class


class H5PMediaMixin(object):
    @property
    def filename(self):
        if self.checksum is None or self.ext is None:
            return None
        return self.checksum + self.ext

    @filename.setter
    def filename(self, val):
        self.checksum, self.ext = os.path.splitext(val)
        if not self.title:
            self.title = self.checksum
        try:
            self.path = self.local_paths[0]
        except IndexError:
            pass
        mime = mimetypes.guess_type(val)
        self.type = mime[0].split("/")[0]

    @property
    def base64_file(self):
        try:
            path = self.local_paths[0]
        except IndexError:
            return None
        try:
            with UniqueFile.storage.open(path, "rb") as v_file:
                f = base64.b64encode(v_file.read())
        except IOError:
            return None
        if not f:
            return None
        else:
            return f

    @base64_file.setter
    def base64_file(self, val):
        if not val:
            return
        for path in self.local_paths:

            if UniqueFile.storage.exists(path):
                continue
            with UniqueFile.storage.open(path, "wb") as v_file:
                print "Writing %s" % path
                v_file.write(base64.b64decode(val))

    def get_h5p_path(self):
        fn = self.filename
        if not fn:
            return None
        else:
            return "videos/" + self.filename

    @property
    def h5p_json_content(self):
        return {'copyright': {'license': 'U'},
                'mime': self.get_mime_type(),
                'path': self.get_h5p_path()}


class H5PSCOMixin(object):
    @property
    def h5p_library(self):
        if self.video:
            return "H5P.InteractiveVideo 1.6"
        if self.is_h5p():
            raise Exception("Unknown H5P type")
        else:
            return None

    @property
    def h5p_resource_dict(self):
        if self.is_h5p():
            return dict([(r.remote_id, r.get_h5p_path())
                         for r in self.h5p_resources])
        else:
            return None

    @h5p_resource_dict.setter
    def h5p_resource_dict(self, val):
        if not val:
            return
        for rid, path in val.iteritems():
            f = UniqueFile.objects.get_or_pull(remote_id=rid)
            self.files.add(f)

    @property
    def json_content(self):
        if not self.is_h5p():
            return None
        if self.video:
            storage = get_storage_class(settings.STATICFILES_STORAGE)()
            with storage.open(settings.STATIC_ROOT +
                              "h5p_video_template.json") as v_file:
                out = json.loads(v_file.read())
            out['interactiveVideo']['video']['title'] = self.title
            out['interactiveVideo']['video']['startScreenOptions'][
                'shortStartDescription'] = self.get_byline()
            out['interactiveVideo']['video']['files'] = [
                f.h5p_json_content for f in self.h5p_resources]
        else:
            raise Exception("Unknown H5P type")
        return out

    @json_content.setter
    def json_content(self, val):
        if 'interactiveVideo' in val:
            try:
                self.byline = val['interactiveVideo']['video'][
                    'startScreenOptions']['shortStartDescription']
            except KeyError:
                pass
        else:
            raise Exception("Unknown H5P json content")
