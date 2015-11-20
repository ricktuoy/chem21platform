import base64
import json

from abc import ABCMeta
from abc import abstractproperty
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.files.storage import get_storage_class


class DrupalNodeFile(list):

    def append(self, ufile, *args, **kwargs):
        with self.storage.open(ufile.path, "rb") as v_file:
            return super(DrupalNodeFile, self).append(
                {'data': base64.b64encode(v_file.read()),
                 'mimetype': ufile.mimetype, 'type': ufile.type},
                *args, **kwargs)


class DrupalNodeVideoFile(DrupalNodeFile):

    def append(self, ufile, *args, **kwargs):
        if ufile.type == "video":
            self._add_video_data(ufile)
            added_files = []
            self.files = []
            for rfile in ufile.versions:
                added_file = super(DrupalNodeVideoFile, self).append(rfile)
                added_file['filename'] = "videos/" + rfile.checksum + rfile.ext
                added_files.append(added_file)
            return added_files
        else:
            return super(DrupalQuestion, self).add_file_data(ufile)


class DrupalNode(dict):

    """ Abstract wrapper for Drupal REST CRUD JSON responses / requests

        Inherit from this for specific Drupal objects.

        n.b. Internal simple_fields property is populated with data that
        requires no additional processing at the Drupal end. All others
        should be passed as individual arguments to Drupal Services callbacks
        and at this end marked as 'special' in the fields property.

        Example usage:
        class DrupalCourse(DrupalNode):
            object_name = "course"
            id_field = "nid"
            fields = {'title': set(['required', ]),
                      'intro': set(['special', ])}

        my_drupal_requests = DrupalRESTRequests(URL,USER,PWD)
        course = DrupalCourse()
        course.id = 23
        my_drupal_requests.pull(course)
        course.set("title", "UPDATED: " + course.get("title"))
        response = my_drupal_requests.push(course)

        This results in JSON
        {'title': 'UPDATED: My original title'}

    """

    __metaclass__ = ABCMeta

    @abstractproperty
    def object_name(self):
        return None

    @abstractproperty
    def id_field(self):
        return None

    @abstractproperty
    def fields(self):
        return None

    @property
    def id(self):
        return self[self.id_field]

    def __init__(self, pairs=[], **kwargs):
        self.storage = DefaultStorage()
        self.static_storage = get_storage_class(settings.STATICFILES_STORAGE)()
        self.simple_fields = {}
        self.set(files, self.get("files", DrupalNodeVideoFile()))
        self.raw = kwargs
        super(DrupalNode, self).__init__(pairs)
        try:
            self.id = kwargs[self.id_field]
        except KeyError:
            pass
        for k, v in kwargs.iteritems():
            try:
                self.set(k, v)
            except AttributeError:
                pass
        self.deserialise_fields()

    def get(self, name, default=None):
        if name not in self.fields:
            raise AttributeError("Field not defined")
        try:
            return getattr(self, name)
        except AttributeError:
            if "special" in self.fields[name]:
                try:
                    return self[name]
                except KeyError:
                    pass
            else:
                try:
                    return self.simple_fields[name]
                except KeyError:
                    pass
            if default:
                return default
            raise AttributeError("Field not initialised")

    def set(self, name, val):
        if hasattr(self, name):
            setattr(self, name, val)
        else:
            if name not in self.fields:
                raise AttributeError("Field not defined")
            if "special" in self.fields[name]:
                self[name] = val
            else:
                self.simple_fields[name] = val
        self.fields[name].add("changed")

    def filter_changed_fields(self):
        return dict([(k, v) for k, v in self.iteritems()
                     if 'changed' in self.fields[k]])

    def mark_all_fields_unchanged(self):
        for v in self.fields.iteritems():
            v.discard("changed")

    def mark_fields_changed(self, fields):
        for f in fields:
            self.fields[f].add("changed")

    def remove_empty_optional_fields(self):
        for field in self.basic_fields:
            try:
                if hasattr(self, field):
                    if not getattr(self, field):
                        delattr(self, field)
                elif not self[field]:
                    del self[field]
            except KeyError:
                pass

    def serialise_fields(self, fieldnames=[]):
        fieldnames = self.serialisable_fields + fieldnames
        for fieldname in fieldnames:
            try:
                self.set(fieldname, json.dumps(self.get(fieldname)))
            except (AttributeError, TypeError):
                pass

    def deserialise_fields(self, fieldnames=[]):
        fieldnames = self.serialisable_fields + fieldnames
        for fieldname in fieldnames:
            try:
                self.set(fieldname, json.loads(self.get(fieldname)))
            except (AttributeError, TypeError):
                pass

    @property
    def simple_fields(self):
        return self['simple_fields']

    @simple_fields.setter
    def simple_fields(self, data):
        self['simple_fields'] = data

    @property
    def serialisable_fields(self):
        return [k for k, v in self.fields.iteritems()
                if 'serialisable' in v]

    def add_nonempty_fields(self, fields):
        for field, value in fields.iteritems():
            if value:
                self[field] = value


class DrupalQuestion(DrupalNode):
    object_name = "question"
    id_field = "nid"
    fields = {'title': set(['special', 'required']),
              'json_content': set(['serialisable', ]),
              'intro': set(['special', ]),
              'lesson': set(['special', ]),
              'type': set()}

    @property
    def byline(self):
        try:
            return self.h5p_video['start_screen_options'][
                'short_start_description']
        except KeyError:
            raise AttributeError("No byline")

    @byline.setter
    def byline(self, val):
        self.h5p_video['start_screen_options'][
            'short_start_description'] = val

    @byline.deleter
    def byline(self):
        del self.h5p_video['start_screen_options'][
            'short_start_description']

    @property
    def h5p_video(self):
        try:
            return self['json_content']['interactiveVideo']['video']
        except KeyError:
            raise AttributeError("No video data")

    def _add_video_data(self, ufile):
        if not hasattr(self, 'h5p_video'):
            with self.static_storage.open(settings.STATIC_ROOT +
                                          "video_fields.json") as v_file:
                self += json.loads(v_file.read())
        self['type'] = "h5p_content"
        self.h5p_video['title'] = self['title']
        for rfile in ufile.version_set:
            dat = {'path': "videos/" + rfile.checksum + rfile.ext,
                   'mimetype': rfile.mimetype, 'copyright': ''}
            self.h5p_video['files'].append(dat)

    def add_file_data(self, ufile):
        if ufile.type == "video":
            self._add_video_data(ufile)
            added_files = []
            self.files = []
            for rfile in ufile.unpushed_versions(self.id):
                added_file = super(DrupalQuestion, self).add_file_data(rfile)
                added_file['filename'] = "videos/" + rfile.checksum + rfile.ext
                added_files.append(added_file)
            return added_files
        else:
            return super(DrupalQuestion, self).add_file_data(ufile)


class DrupalLesson(DrupalNode):
    object_name = "lesson"
    id_field = "nid"
    fields = {'title': set(['special', 'required']),
              'intro': set(['special', ]),
              'course': set(['special', ])}


class DrupalCourse(DrupalNode):
    object_name = "course"
    id_field = "nid"
    fields = {'title': set(['special', 'required']),
              'intro': set(['special', ])}


def drupal_node_factory(type):
    type_map = {'course': DrupalCourse,
                'lesson': DrupalLesson,
                'question': DrupalQuestion}
    return type_map[type]
