import json
import logging
import os
import base64
import mimetypes

import tinymce.models as mceModels

from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from chem21repo.api_clients import C21RESTRequests
from chem21repo.drupal import drupal_node_factory
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import DefaultStorage
from django.core.files.storage import get_storage_class
from django.core.urlresolvers import reverse
from django.db import models
from django.db import transaction
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from filebrowser.fields import FileBrowseField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes import generic


class BaseModel(models.Model):

    class Meta:
        abstract = True


class OrderedModel(BaseModel):
    order = models.IntegerField(default=0)
    order_dirty = models.BooleanField(default=True)

    def move_to(self, el):
        type(self).move(self, el)

    def order_is_dirty(self):
        return self.order_dirty

    class Meta:
        abstract = True
        ordering = ('order',)


class TextVersion(OrderedModel):
    text = models.TextField()
    user = models.ForeignKey(User, editable=False)
    limit = models.Q(app_label='repo', model='Topic') | \
        models.Q(app_label='repo', model='Module') | \
        models.Q(app_label='repo', model='Lesson') | \
        models.Q(app_label='repo', model='Question')
    content_type = models.ForeignKey(
        ContentType,
        verbose_name='content page',
        limit_choices_to=limit,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(
        verbose_name='related object',
        null=True,
    )
    original = generic.GenericForeignKey()


def UnicodeMixinFactory(name_field):
    class _NameMixin(object):

        def __unicode__(self):
            try:
                return getattr(self, name_field)
            except TypeError:
                return " ".join([unicode(getattr(self, field))
                                 for field in name_field])
    return _NameMixin


# needed for migration
NameUnicodeMixin = UnicodeMixinFactory("name")
NameUnicodeMixin.__name__ = "NameUnicodeMixin"
PathUnicodeMixin = UnicodeMixinFactory("path")
PathUnicodeMixin.__name__ = "PathUnicodeMixin"
TitleUnicodeMixin = UnicodeMixinFactory("title")
TitleUnicodeMixin.__name__ = "TitleUnicodeMixin"
AuthorUnicodeMixin = UnicodeMixinFactory("full_name")
AuthorUnicodeMixin.__name__ = "AuthorUnicodeMixin"
EventUnicodeMixin = UnicodeMixinFactory(("name", "date"))
EventUnicodeMixin.__name__ = "EventUnicodeMixin"


class DrupalManager(models.Manager):

    def get_or_pull(self, *args, **kwargs):
        try:
            return self.get(*args, **kwargs)
        except self.model.DoesNotExist:
            instance = self.model(*args, **kwargs)
            instance.drupal.pull()
            instance.save()
            return instance


class DrupalModel(models.Model):
    dirty = models.TextField(default="[]")
    text_versions = GenericRelation(TextVersion)

    @property
    def is_dirty(self):
        dirty = self.dirty != "[]"
        try:
            dirty = dirty or (self.__class__.objects.order_field
                              in self.drupal.original.values(
                              ) and self.order_is_dirty())
        except AttributeError:
            pass
        return dirty

    @property
    def children(self):
        return getattr(self, self.child_attr_name)

    @property
    def child_attr_name(self):
        raise AttributeError

    @property
    def new_children(self):
        return self.children.filter(remote_id__isnull=True)

    def __init__(self, *args, **kwargs):
        r = super(DrupalModel, self).__init__(*args, **kwargs)
        self.drupal.instantiate(self)
        self.fixture_mode = False
        return r

    class Meta:
        abstract = True


class OrderedManagerBase:
    __metaclass__ = ABCMeta

    @abstractproperty
    def order_field(self):
        return None

    @property
    def order_dirty_field(self):
        return self.order_field + "_dirty"

    @property
    def force_reset_order(self):
        return True

    @abstractmethod
    def order_queryset(self):
        return None

    def flag_dirty(self):
        return None

    def order_incr_dict(self):
        return {self.order_field: models.F(self.order_field) + 1,
                self.order_dirty_field: True}

    def order_decr_dict(self):
        return {self.order_field: models.F(self.order_field) - 1,
                self.order_dirty_field: True}

    def order_slice_dict(self, val1, val2):
        return {self.order_field + "__gt": val1,
                self.order_field + "__lte": val2}

    def get_order_value(self, el):
        return getattr(el, self.order_field)

    def set_order_value(self, el, val):
        setattr(el, self.order_dirty_field, True)
        return setattr(el, self.order_field, val)

    def order_sum(self):
        # gets sum of orders from DB. should be equal to self.order_triangle if
        # DB is consistent
        q = self.order_queryset().aggregate(
            order_sum=models.Sum(self.order_field))
        return q['order_sum']

    def order_triangle(self):
        # calculates what sum of orders from DB should be if consistent
        n = self.order_queryset().count()
        return (n * (n + 1)) / 2

    def _reset_order(self):
        i = 1
        for o in self.order_queryset().order_by(self.order_field):
            self.set_order_value(o, i)
            i += 1
            o.save()

    def _ensure_order_consistent(self):
        """ Check orders are consistent in DB, else recalculates """
        if self.order_sum() != self.order_triangle() or \
                self.force_reset_order is True:
            self._reset_order()
            self._have_reset_order = True
        else:
            self._have_reset_order = False
        return self._have_reset_order

    def _load_obj_from_arg(self, arg):
        # make sure we have up-to-date objects loaded from DB after reset
        # if args are integers (PKs) load the object now
        if self._have_reset_order or isinstance(arg, (int, long)):
            try:
                elId = arg.id
            except AttributeError:
                elId = arg
            return self.model.objects.get(pk=elId)
        return arg

    @transaction.atomic
    def move_to_top(self, source, parent=None):
        if parent:
            try:
                self.set_m2m_key_value(parent)
            except AttributeError:
                pass
        self._current_element = source
        self._ensure_order_consistent()
        source = self._load_obj_from_arg(source)
        self._current_element = source

        sval = self.get_order_value(source)
        self.order_queryset().filter(
            **self.order_slice_dict(0, sval)).update(**self.order_incr_dict())
        self.set_order_value(source, 1)
        source.save()
        self.flag_dirty()
        return (True, "Success")

    @transaction.atomic
    def move(self, source, dest, parent=None):
        if parent:
            try:
                self.set_m2m_key_value(parent)
            except AttributeError:
                pass

        self._current_element = source
        self._current_target_element = dest
        self._ensure_order_consistent()
        source = self._load_obj_from_arg(source)
        dest = self._load_obj_from_arg(dest)
        self._current_element = source
        self._current_target_element = dest

        # get current orders
        sval = self.get_order_value(source)
        dval = self.get_order_value(dest)

        if sval == dval:
            return (False, "Destination file same as file being moved")
        elif sval < dval:
            self.order_queryset().filter(
                **self.order_slice_dict(
                    sval, dval)
            ).update(
                **self.order_decr_dict())
        elif sval > dval:
            self.order_queryset().filter(
                **self.order_slice_dict(
                    dval, sval)
            ).update(
                **self.order_incr_dict())

        self.set_order_value(source, dval + 1)
        source.save()
        self.flag_dirty()

        return (True, "Success")


class OrderedRelationalManagerBase(OrderedManagerBase):

    @abstractproperty
    def order_key(self):
        return None

    def flag_dirty(self):
        parent = self._get_order_key_value()

        parent.drupal.mark_fields_changed([parent.drupal.child_order_field, ])
        parent.save(update_fields=["dirty", ])

    def _get_order_key_value(self):
        return getattr(self._current_element, self.order_key)

    def order_queryset(self):
        return self.get_queryset().filter(
            **{self.order_key: self._get_order_key_value(self)})


class OrderedManyToManyManagerBase(OrderedRelationalManagerBase):

    def set_m2m_key_value(self, val):
        self._current_m2m_key_value = val

    def get_m2m_key_value(self):
        return self._current_m2m_key_value

    def order_queryset(self):
        return self.get_queryset().filter(
            **{self.order_key + "__pk": self.get_m2m_key_value()})

    def flag_dirty(self):
        parent = self._get_order_key_value().get(pk=self.get_m2m_key_value())
        parent.drupal.mark_fields_changed([parent.drupal.child_order_field, ])
        parent.save(update_fields=["dirty", ])


class OrderedManager(models.Manager, OrderedManagerBase):

    @property
    def order_field(self):
        return "order"

    def order_queryset(self, el=None, new_parent=None):
        return self.get_queryset()

    def get_queryset(self):
        return super(OrderedManager, self).get_queryset()


class OrderedDrupalManager(OrderedManager, DrupalManager):
    pass


class ActiveManager(DrupalManager):

    def get_queryset(self):
        return super(ActiveManager, self).get_queryset().filter(active=True)


class CutManager(ActiveManager, OrderedRelationalManagerBase):

    def get_queryset(self):
        return super(CutManager, self).get_queryset().filter(
            cut_of__isnull=False)

    @property
    def order_field(self):
        return "cut_order"

    @property
    def order_key(self):
        return "cut_of"


class AuthorInFileManager(models.Manager, OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "file"


class FileInModuleManager(models.Manager, OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "module"


class PresentationsInQuestionManager(models.Manager,
                                     OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "question"


class LessonsInModuleManager(DrupalManager,
                             OrderedManyToManyManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "modules"


class SourceFilesInPresentationManager(models.Manager,
                                       OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "presentation"


class SlidesInPresentationVersionManager(models.Manager,
                                         OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "presentation"


class FilesInQuestionManager(DrupalManager,
                             OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "question"


class QuestionsInLessonManager(DrupalManager,
                               OrderedManyToManyManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "lessons"


class DrupalConnector(object):

    def __init__(self, tpe, api, obj=None, fle=None, **kwargs):
        self.original = kwargs
        self.tpe = tpe
        self.api = api
        self.file = fle

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

        # if isinstance(self.parent, UniqueFile):
        #    print "***FILE***"
        #    return {}

        self.parent.remote_id = None
        self.parent.save(update_fields=["remote_id", ])

    def push(self):
        try:
            name = self.parent.title
        except AttributeError:
            name = self.parent.name
        print name

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
                    logging.debug("Field changed from %s to %s" %
                                  (self.node.get(k), newval))
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


@receiver(models.signals.pre_save)
def generate_dirty_record(sender,
                          instance, raw,
                          using, update_fields,
                          **kwargs):
    if isinstance(instance, DrupalModel) \
            and not isinstance(instance, UniqueFile):
        if update_fields:
            instance.drupal.mark_fields_changed(update_fields)
            return
        if not raw:
            try:
                original = sender.objects.get(pk=instance.pk)
                instance.drupal.mark_fields_changed(
                    original.drupal.get_field_diff(instance.drupal))
                return

            except:
                pass
        # instance.drupal.mark_fields_changed(instance.drupal.fields)


@receiver(models.signals.post_save)
def save_text_version(sender, instance, raw, **kwargs):
    if isinstance(instance, DrupalModel) \
            and not isinstance(instance, UniqueFile):
        if not raw and hasattr(instance, "user"):
            try:
                text = instance.text
            except AttributeError:
                text = instance.intro
            v_args = {
                'text': text,
                'original': instance,
                'user': instance.user,
                #'changed': datetime.now()
            }
            TextVersion.objects.create(**v_args)


@receiver(models.signals.m2m_changed)
def generate_dirty_m2m_record(sender, instance, action,
                              reverse, model, pk_set, **kwargs):

    if not(issubclass(model, DrupalModel) and
            isinstance(instance, DrupalModel)) or instance.fixture_mode:
        return
    if action != "post_add" and action != "post_remove":
        return
    if reverse:
        #children = [instance, ]
        parents = list(model.objects.filter(pk__in=pk_set))
        parent_model = model
    else:
        #children = list(model.objects.filter(pk__in=pk_set))
        parents = [instance, ]
        parent_model = instance.__class__
    parent_fields = parent_model.drupal.child_fields()

    if parent_fields:
        try:
            for p in parents:
                #raise Exception("Found a parent")
                p.drupal.mark_fields_changed(parent_fields)
                p.save(update_fields=["dirty", ])
        except:
            pass


class Event(BaseModel, EventUnicodeMixin):
    name = models.CharField(max_length=100)
    date = models.DateField(null=True)

    @property
    def description(self):
        return self.name + ": " + datetime.strftime(
            self.date, "%b %Y")

    class Meta:
        unique_together = (('name', 'date'),)
        index_together = (('name', 'date'),)


class Status(BaseModel, NameUnicodeMixin):
    name = models.CharField(max_length=200)


class Author(BaseModel, AuthorUnicodeMixin):
    full_name = models.CharField(max_length=200, unique=True)
    role = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        if self.role:
            return "%s, %s" % (self.full_name, self.role)
        else:
            return self.full_name


class UniqueFile(OrderedModel, DrupalModel):
    objects = DrupalManager()
    cut_objects = CutManager()
    checksum = models.CharField(max_length=100, null=True, unique=True)
    path = models.CharField(max_length=255, null=True)
    ext = models.CharField(max_length=25, null=True)
    type = models.CharField(max_length=15, default="text", null=True)
    title = models.CharField(max_length=200, null=True)
    size = models.BigIntegerField(default=0)
    event = models.ForeignKey(Event, null=True)
    status = models.ForeignKey(Status, null=True)
    file = FileBrowseField(max_length=500, null=True)
    cut_of = models.ForeignKey('self', related_name='cuts', null=True)
    version_of = models.ForeignKey('self', related_name='versions', null=True)
    cut_order = models.IntegerField(default=0)
    ready = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    s3d = models.BooleanField(default=False)
    remote_path = models.CharField(max_length=255, null=True, blank=True)
    remote_id = models.IntegerField(null=True, db_index=True)
    authors = models.ManyToManyField(Author, blank=True)

    # def __init__(self, *args, **kwargs):

    #    return super(UniqueFile, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.path

    @property
    def _stripped_ext(self):
        return self.ext.replace(".", "")

    def get_absolute_url(self):
        return reverse('video_detail', kwargs={'checksum': self.checksum})

    def get_file_relative_url(self):
        return "sources/" + self.checksum + self.ext

    def get_mime_type(self):
        return self.type + "/" + self._stripped_ext

    @property
    def author_string(self):
        if self.cut_of and self.cut_of.pk != self.pk:
            return self.cut_of.author_string
        authors = list(self.authors.all())
        if len(authors) == 1:
            return unicode(authors[0])
        out = "; ".join(map(unicode, authors[:-1]))
        try:
            return "%s; and %s" % (out, unicode(authors[-1]))
        except IndexError:
            return out

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
        if not self.path:
            # TODO: generate a proper local path
            # (give a Module to the Path
            # model ... write a .module attribute for Question and a .question
            # attribute for this)
            pass
        mime = mimetypes.guess_type(val)
        self.type = mime[0].split("/")[0]

    @property
    def base64_file(self):
        if self.path is None:
            return None
        with UniqueFile.storage.open(self.path, "rb") as v_file:
            f = base64.b64encode(v_file.read())
        if not f:
            return None
        else:
            return f

    @base64_file.setter
    def base64_file(self, val):
        if not val or self.path is None:
            return
        with UniqueFile.storage.open(self.path, "wb") as v_file:
            v_file.write(base64.b64decode(val))

    def get_h5p_path(self):
        return "videos/" + self.filename

    @property
    def h5p_json_content(self):
        return {'copyright': {'license': 'U'},
                'mime': self.get_mime_type(),
                'path': self.get_h5p_path()}

    def get_title(self):
        if not self.title:
            if self.path:
                return os.path.basename(os.path.basename(self.path))
            else:
                return self.filename
        return self.title

    drupal = DrupalConnector(
        'file', C21RESTRequests(),
        filesize='size', id='remote_id',
        filename='filename', file='base64_file')
try:
    UniqueFile.storage = get_storage_class(settings.SHARED_DRIVE_STORAGE)()
except AttributeError:
    UniqueFile.storage = DefaultStorage()


class Topic(OrderedModel, DrupalModel, NameUnicodeMixin):
    objects = OrderedDrupalManager()
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    remote_id = models.IntegerField(null=True, db_index=True)
    child_attr_name = "modules"

    @property
    def child_orders(self):
        try:
            return dict(
                (m.remote_id, m.order) for m in self.modules.all() if m.remote_id)
        except ValueError:
            return None

    @child_orders.setter
    def child_orders(self, val):
        for rid, order in val:
            m = Module.objects.get_or_pull(remote_id=rid)
            m.topic = self
            m.order = order
            m.save(update_fields=["topic", "order"])

    drupal = DrupalConnector(
        'class', C21RESTRequests(),
        title='name', id='remote_id',
        course_orders='child_orders')

    def __unicode__(self):
        return "%s" % self.name


class Module(OrderedModel, DrupalModel, NameUnicodeMixin):
    objects = OrderedDrupalManager()
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    topic = models.ForeignKey(Topic, related_name='modules')
    working = models.BooleanField(default=False)
    files = models.ManyToManyField(UniqueFile, through='UniqueFilesofModule')
    remote_id = models.IntegerField(null=True, db_index=True)
    text = mceModels.HTMLField(null=True, blank=True, default="")
    _child_orders = {}
    child_attr_name = "lessons"

    @property
    def topic_remote_id(self):
        try:
            return self.topic.remote_id
        except Topic.DoesNotExist:
            return None

    @topic_remote_id.setter
    def topic_remote_id(self, val):
        self.topic = Topic.objects.get_or_pull(remote_id=val)

    @property
    def child_orders(self):
        try:
            return dict(
                (q.remote_id, q.order) for q in self.lessons.all() if q.remote_id)
        except ValueError:
            return None

    @child_orders.setter
    def child_orders(self, val):
        for rid, order in val:
            lesson = Lesson.objects.get_or_pull(remote_id=rid)
            lesson.modules.add(self)
            lesson.order = order
            lesson.save(update_fields=["order", "modules"])

    drupal = DrupalConnector(
        'course', C21RESTRequests(),
        title='name', id='remote_id',
        intro='text',
        klass='topic_remote_id', lesson_orders='child_orders')

    def __unicode__(self):
        return "%s: %s" % (unicode(self.topic), self.name)

    class Meta:
        permissions = (
            ("can_publish", "Can publish modules"),
            ("change structure", "Can change module structures"),
        )


class Path(BaseModel, NameUnicodeMixin):
    name = models.CharField(max_length=800, unique=True)
    topic = models.ForeignKey(Topic, related_name='paths', null=True)
    module = models.ForeignKey(Module, related_name='paths', null=True)
    active = models.BooleanField(default=True)


class UniqueFilesofModule(OrderedModel):
    objects = FileInModuleManager()
    file = models.ForeignKey(UniqueFile)
    module = models.ForeignKey(Module)

    class Meta(OrderedModel.Meta):
        unique_together = ('file', 'module')
        index_together = ('file', 'module')


class File(OrderedModel, PathUnicodeMixin):
    path = models.CharField(max_length=800, unique=True)
    title = models.CharField(max_length=200, null=True)
    containing_path = models.ForeignKey(Path, related_name="files", null=True)
    dir_level = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    ready = models.BooleanField(default=False)

    def suggested_filename(self):
        _, ext = os.path.splitext(self.path)
        if self.event is not None:
            return slugify(self.event.name + " " +
                           datetime.strftime(
                               self.event.date, "%m %Y") +
                           " " + self.title) + ext
        else:
            return slugify(" ".join(
                [a.author.full_name for a in self.authors]) +
                " " + self.title) + ext

    class Meta:
        ordering = ['containing_path__topic', 'containing_path__module']


class FileLink(BaseModel):
    origin = models.ForeignKey(File, related_name="filelink_destinations")
    destination = models.ForeignKey(File, related_name="filelink_origins")

    class Meta:
        unique_together = ('origin', 'destination')
        index_together = ('origin', 'destination')


class FileStatus(BaseModel):
    file = models.ForeignKey(UniqueFile)
    status = models.ForeignKey(Status)
    user = models.ForeignKey(User)


class Presentation(BaseModel):
    source_files = models.ManyToManyField(
        UniqueFile, through="SourceFilesInPresentation")


class SourceFilesInPresentation(OrderedModel):
    objects = SourceFilesInPresentationManager()
    file = models.ForeignKey(UniqueFile)
    presentation = models.ForeignKey(Presentation)

    class Meta(OrderedModel.Meta):
        unique_together = ('presentation', 'file')
        index_together = ('presentation', 'file')


class PresentationSlide(OrderedModel):
    file = FileBrowseField(max_length=500, null=True)
    duration = models.IntegerField(
        help_text='Duration of this slide in milliseconds')
    html = models.TextField()


class PresentationVersion(BaseModel):
    presentation = models.ForeignKey(Presentation)
    version = models.IntegerField()
    slides = models.ManyToManyField(
        PresentationSlide, through='SlidesInPresentationVersion')
    audio = models.ForeignKey(UniqueFile)


class SlidesInPresentationVersion(OrderedModel):
    objects = SlidesInPresentationVersionManager()
    presentation = models.ForeignKey(PresentationVersion)
    slide = models.ForeignKey(PresentationSlide)

    class Meta(OrderedModel.Meta):
        unique_together = ('presentation', 'slide')
        index_together = ('presentation', 'slide')


class Lesson(OrderedModel, DrupalModel, TitleUnicodeMixin):
    objects = LessonsInModuleManager()
    modules = models.ManyToManyField(Module, related_name="lessons")
    title = models.CharField(max_length=100, blank=True, default="")
    remote_id = models.IntegerField(null=True, db_index=True)
    text = mceModels.HTMLField(null=True, blank=True, default="")
    _child_orders = {}
    child_attr_name = "questions"

    # define the interface with Drupal
    drupal = DrupalConnector(
        'lesson', C21RESTRequests(),
        title='title', id='remote_id',
        question_orders='child_orders',
    )

    @property
    def child_orders(self):
        try:
            return dict(
                (q.remote_id, q.order) for q in self.questions.all() if q.remote_id)
        except ValueError:
            return None

    @child_orders.setter
    def child_orders(self, val):
        for rid, order in val:
            q = Question.get(remote_id=rid)
            q.lessons.add(self)
            q.order = order
            q.save(update_fields=["order", "lessons"])


class Question(OrderedModel, DrupalModel, TitleUnicodeMixin):
    objects = QuestionsInLessonManager()
    title = models.CharField(max_length=100, blank=True, default="")
    presentations = models.ManyToManyField(
        Presentation, through='PresentationsInQuestion')
    files = models.ManyToManyField(UniqueFile, related_name="questions")
    text = mceModels.HTMLField(null=True, blank=True, default="")
    byline = mceModels.HTMLField(null=True, blank=True, default="")
    pdf = models.ForeignKey(UniqueFile, null=True, related_name="pdf_question")
    remote_id = models.IntegerField(null=True, db_index=True)
    lessons = models.ManyToManyField(Lesson, related_name="questions")
    child_attr_name = "files"

    # define the interface with Drupal
    drupal = DrupalConnector(
        'question', C21RESTRequests(),
        title='title', intro='text', id='remote_id',
        type='type', h5p_library='h5p_library',
        h5p_resources='h5p_resource_dict',
        json_content='json_content'
    )

    # ##################### Drupal interface attributes ##################

    @property
    def type(self):
        if self.is_h5p():
            return "h5p_content"
        else:
            return "quiz_directions"

    @type.setter
    def type(self, val):
        pass

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

    def get_byline(self):
        if not self.byline and self.video:
            return "Author: %s" % self.video.author_string

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

    # ################ Helper attributes ########################

    @property
    def video(self, reset=False):
        if not reset:
            try:
                return self._cached_video
            except AttributeError:
                pass
        try:
            self._cached_video = list(self.files.filter(type="video")[:1])[0]
        except (IndexError, ValueError):
            self._cached_video = None
        return self._cached_video

    def is_h5p(self):
        return not not self.video

    @property
    def h5p_resources(self):
        if self.is_h5p():
            if self.video:
                out = list(self.video.versions.all())
                out.append(self.video)
                return out
            else:
                return []
        else:
            raise AttributeError


class PresentationsInQuestion(OrderedModel):
    objects = PresentationsInQuestionManager()
    question = models.ForeignKey(Question)
    presentation = models.ForeignKey(Presentation)

    class Meta(OrderedModel.Meta):
        unique_together = ('question', 'presentation')
        index_together = ('question', 'presentation')
