import base64
import json

from abc import ABCMeta
from abc import abstractproperty


class DrupalNodeFiles(list):

    def append(self, ufile, *args, **kwargs):
        with self.storage.open(ufile.path, "rb") as v_file:
            return super(DrupalNodeFiles, self).append(
                {'data': base64.b64encode(v_file.read()),
                 'mimetype': ufile.mimetype, 'type': ufile.type} + kwargs)


class DrupalNodeVideoFiles(DrupalNodeFiles):

    def append(self, ufile, *args, **kwargs):
        results = []
        for rfile in ufile.versions:
            results.append(super(DrupalNodeVideoFiles, self).append(
                rfile, filename="videos/" + rfile.checksum + rfile.ext))
        return results


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
        try:
            return self[self.id_field]
        except KeyError:
            raise AttributeError("No id set.")

    @classmethod
    def get_field_diff(cls, node1, node2):
        return [f for f in cls.fields
                if not cls.compare_fields(f, node1, node2)]

    @classmethod
    def compare_fields(cls, field, node1, node2):
        try:
            f2 = node2.get(field)
        except AttributeError:
            return True
        try:
            f1 = node1.get(field)
        except AttributeError:
            return False
        return f1 == f2

    @id.setter
    def id(self, v):
        self[self.id_field] = int(v)

    def __init__(self, pairs=[], **kwargs):
        self.simple_fields = {}
        self.raw = kwargs
        super(DrupalNode, self).__init__(pairs)
        self.populate(**kwargs)

    def populate(self, **kwargs):
        for k, v in kwargs.iteritems():
            try:
                self.set(k, v)
            except AttributeError:
                pass
        self.deserialise_fields()

    def get(self, name, default=None):
        try:
            return getattr(self, name)
        except AttributeError:
            if name not in self.fields:
                if default is not None:
                    return default
                else:
                    raise AttributeError(
                        "Field %s not defined for drupal wrapper %s " %
                        (name, self.object_name))
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
            if default is not None:
                return default
            raise AttributeError(
                "Field %s not initialised for drupal wrapper %s" %
                (name, self.object_name))

    def set(self, name, val):
        if name not in self.fields:
            setattr(self, name, val)
            return
        if "special" in self.fields[name]:
            self[name] = val
        else:
            self.simple_fields[name] = val

    def _filter_fields(self, arg):
        return dict([(k, self[k]) for k, v in self.fields.iteritems()
                     if arg in v and k in self])

    def filter_changed_fields(self):
        return self._filter_fields('changed')

    def dirty(self):
        if self.get('id', False):
            print self.filter_changed_fields()
            return self.filter_changed_fields()
        else:
            return self

    @classmethod
    def get_child_affected_fields(cls):
        return [k for k, v in cls.fields.iteritems() if "child_affected" in v]

    def mark_all_fields_unchanged(self):
        for k, v in self.fields.iteritems():
            v.discard("changed")

    def mark_fields_changed(self, fields):

        for f in fields:
            if not f == "id" and f in self.fields:
                self.fields[f].add("changed")

    def remove_empty_optional_fields(self):
        for field in self.simple_fields:
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
              'json_content': set(['serialisable', 'child_affected']),
              'h5p_resources': set(['special', 'child_affected']),
              'h5p_library': set(['special', 'child_affected']),
              'intro': set(['special', ]),
              'lesson': set(['special', ]),
              'type': set(['child_affected', ])}

    def __init__(self, *args, **kwargs):
        super(DrupalQuestion, self).__init__(self, *args, **kwargs)

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

    def _add_h5p_video_data(self, ufile):

        self['type'] = "h5p_content"
        self.h5p_video['title'] = self['title']
        for rfile in ufile.version_set:
            dat = {'path': "videos/" + rfile.checksum + rfile.ext,
                   'mimetype': rfile.mimetype, 'copyright': ''}
            self.h5p_video['files'].append(dat)


class DrupalLesson(DrupalNode):
    object_name = "lesson"
    id_field = "nid"
    fields = {'title': set(['special', 'required']),
              'intro': set(['special', ]),
              'question_orders': set(['special', 'child_affected']), }


class DrupalCourse(DrupalNode):
    object_name = "course"
    id_field = "nid"
    fields = {'title': set(['special', 'required']),
              'intro': set(['special', ]),
              'lesson_orders': set(['special', 'child_affected']), }


class DrupalTopic(DrupalNode):
    object_name = "class"
    id_field = "nid"
    fields = {'title': set(['special', 'required']),
              'intro': set(['special', ]), }


class DrupalFile(DrupalNode):
    object_name = "file"
    id_field = "fid"
    fields = {'filename': set(['special', ]),
              'filesize': set(['special', ]),
              'file': set(['special', ])}


def drupal_node_factory(type):
    type_map = {'course': DrupalCourse,
                'lesson': DrupalLesson,
                'question': DrupalQuestion,
                'class': DrupalTopic,
                'file': DrupalFile}
    return type_map[type]


class DrupalConnector(object):

    def __init__(self, tpe, api, obj=None, fle=None, **kwargs):
        self.original = kwargs
        self.tpe = tpe
        self.api = api
        self.file = fle
        self.node = None

        if obj:

            def connection(value):
                def inner(obj):
                    return obj.__getattribute__(value)
                return inner
            self.connector = dict([(k, connection(v))
                                   for k, v in self.original.iteritems()])
            self.parent = obj

    def needs_node(fn):
        def inner(self, *args, **kwargs):
            try:
                _ = self.node
            except AttributeError:
                self.node = self.generate_node_from_parent()
            return fn(self, *args, **kwargs)
        return inner

    @needs_node
    def strip_remote_id(self):
        try:
            new_children = self.parent.children.all()
        except AttributeError:
            new_children = []
        for child in new_children:
            child.drupal.strip_remote_id()

        self.parent.remote_id = None
        self.parent.save(update_fields=["remote_id", ])

    def push(self):
        try:
            name = self.parent.title
        except AttributeError:
            name = self.parent.name

        try:
            new_children = self.parent.new_children
        except AttributeError:
            new_children = []

        for child in new_children:
            print "descending to child"
            child.drupal.push()

        self.node = self.generate_node_from_parent()

        # print "Doing push for ID %s %s" % (self.node.id, name)
        response, created = self.api.push(self.node)
        if created:
            print "Was created"
            try:
                self.node.set('id', int(response['id']))
                setattr(self.parent, self.original['id'], self.node.get('id'))
                self.parent.save(update_fields=[self.original['id'], ])
            except KeyError:
                try:
                    self.node.set('id', int(response['fid']))
                    setattr(
                        self.parent, self.original['id'], self.node.get('id'))
                    self.parent.save(update_fields=[self.original['id'], ])
                except KeyError:
                    raise Exception("No id returned")
        self.mark_all_clean()
        self.parent.save(update_fields=self.parent_dirty_meta_fields)
        print "Done push for %s" % name
        return response

    @needs_node
    def pull(self):
        old_node = self.generate_node_from_parent()
        self.api.pull(self.node)
        # if isinstance(self.parent, UniqueFile):
        #    raise Exception(str(self.node))
        diff = self.node_class.get_field_diff(old_node, self.node)
        updates = dict(
            [(self.original[f], self.node.get(f))
             for f in diff if f in self.original])
        old = dict([(self.original[f], old_node.get(f, default=""))
                    for f in diff if f in self.original])
        for k, v in updates.iteritems():
            try:
                setattr(self.parent, k, v)
            except AttributeError:
                raise Exception("Failed to set attribute %s, %s" % (k, str(v)))
        self.parent.save()
        self.mark_all_clean()
        self.parent.save(update_fields=self.parent_dirty_meta_fields)
        return (old, updates)

    @property
    def parent_dirty_meta_fields(self):
        # try:
        #    return ['dirty', self.parent.__class__.objects.order_dirty_field]
        # except AttributeError:
        #   pass
        return ['dirty', ]

    def parent_dirty_fields(self):
        fields = json.loads(self.parent.dirty)
        # if self.parent.order_is_dirty():
        #    fields.append(self.parent.__class__.objects.order_field)

        return fields

    @property
    def node_class(self):
        return drupal_node_factory(self.tpe)

    @property
    def fields(self):
        return set(self.original.keys())

    def generate_node_from_parent(self, debug=False):
        node = self.node_class(**dict([(k, v(self.parent))
                                       for k, v in
                                       self.connector.iteritems()
                                       if v(self.parent) is not None and
                                       (not debug or k != "file")]))
        node.mark_fields_changed(self.parent_dirty_fields())

        return node

    def instantiate(self, obj):
        obj.drupal = DrupalConnector(
            self.tpe, api=self.api, obj=obj, **self.original)

    @needs_node
    def get_field_diff(self, changed):
        diff = set([])
        for k, f1 in self.connector.iteritems():
            f2 = changed.connector[k]
            newval = f2(changed.parent)
            try:
                if self.node.get(k) != newval:
                    diff.add(k)
            except AttributeError:
                diff.add(k)
        return diff

    @needs_node
    def mark_fields_changed(self, fields):
        fields = self.fields.intersection(fields)
        if fields:
            self.parent.dirty = json.dumps(
                list(set(json.loads(self.parent.dirty)).union(fields)))
            self.node.mark_fields_changed(fields)

    @needs_node
    def mark_all_clean(self):
        self.parent.dirty = "[]"
        try:
            setattr(
                self.parent,
                self.parent.__class__.objects.order_dirty_field,
                False)
        except AttributeError:
            pass
        self.node.mark_all_fields_unchanged()

    def child_fields(self):
        return self.node_class.get_child_affected_fields()

    @property
    def child_order_field(self):
        for k, v in self.original.iteritems():
            if v == "child_orders":
                return k
        raise AttributeError
        