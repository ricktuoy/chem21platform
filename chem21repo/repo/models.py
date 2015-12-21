import json
import logging
import os
import base64

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


class BaseModel(models.Model):

    class Meta:
        abstract = True


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


class ActiveManager(models.Manager):

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


class LessonsInModuleManager(models.Manager,
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


class FilesInQuestionManager(models.Manager,
                             OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "question"


class QuestionsInLessonManager(models.Manager,
                               OrderedManyToManyManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "lessons"


class DrupalModel(models.Model):
    dirty = models.TextField(default="[]")

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

    def __init__(self, *args, **kwargs):
        r = super(DrupalModel, self).__init__(*args, **kwargs)
        self.drupal.instantiate(self)
        return r

    class Meta:
        abstract = True


class DrupalConnector(object):

    def __init__(self, tpe, api, obj=None, fle=None, **kwargs):
        self.original = kwargs
        self.tpe = tpe
        self.api = api
        self.file = fle

        if obj:
            connection_cache = {}

            def connection(value):
                def inner(obj):
                    try:
                        return connection_cache[(obj, value)]
                    except KeyError:
                        connection_cache[
                            (obj, value)] = obj.__getattribute__(value)
                    return connection_cache[(obj, value)]
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
    def push(self):

        response, created = self.api.push(self.node)
        if created:
            self.node.set('id', response['id'])
            setattr(
                self.parent, self.original['id'], self.node.get('id'))
            self.parent.save(update_fields=[self.original['id']])
        self.mark_all_clean()
        self.parent.save(update_fields=self.parent_dirty_meta_fields)
        return response

    @needs_node
    def pull(self):

        old_node = self.generate_node_from_parent()
        self.api.pull(self.node)
        diff = self.node_class.get_field_diff(old_node, self.node)
        updates = dict(
            [(self.original[f], self.node.get(f))
             for f in diff if f in self.original])
        old = dict([(self.original[f], old_node.get(f))
                    for f in diff if f in self.original])
        for k, v in updates.iteritems():
            setattr(self.parent, k, v)
        self.parent.save(update_fields=updates.keys())
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
            if self.node.get(k) != newval:
                logging.debug("Field changed from %s to %s" %
                              (self.node.get(k), newval))
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
        setattr(
            self.parent,
            self.parent.__class__.objects.order_dirty_field,
            False)
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
    if isinstance(instance, DrupalModel):
        if update_fields:
            instance.drupal.mark_fields_changed(update_fields)
            return
        if not raw:
            try:
                original = sender.objects.get(pk=instance.pk)
                instance.drupal.mark_fields_changed(
                    original.drupal.get_field_diff(instance.drupal))
                return

            except sender.DoesNotExist:
                pass
        instance.drupal.mark_fields_changed(instance.drupal.fields)


@receiver(models.signals.m2m_changed)
def generate_dirty_m2m_record(sender, instance, action,
                              reverse, model, pk_set, **kwargs):
    if not(issubclass(model, DrupalModel) and
            isinstance(instance, DrupalModel)):
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
        for p in parents:
            #raise Exception("Found a parent")
            p.drupal.mark_fields_changed(parent_fields)
            p.save(update_fields=["dirty", ])


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


class UniqueFile(OrderedModel, DrupalModel):
    objects = ActiveManager()
    cut_objects = CutManager()
    checksum = models.CharField(max_length=100, null=True, unique=True)
    path = models.CharField(max_length=255, null=True)
    ext = models.CharField(max_length=8, null=True)
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
    remote_path = models.CharField(max_length=255, null=True)
    remote_id = models.IntegerField(null=True, db_index=True)

    # def __init__(self, *args, **kwargs):

    #    return super(UniqueFile, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.checksum

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
    def filename(self):
        return self.checksum + self.ext

    @property
    def base64_file(self):
        with UniqueFile.storage.open(self.path, "rb") as v_file:
            return base64.b64encode(v_file.read())

    def get_h5p_path(self):
        return "videos/" + self.filename

    @property
    def h5p_json_content(self):
        return {'copyright': {'license': 'U'},
                'mime': self.get_mime_type(),
                'path': self.get_h5p_path()}

    drupal = DrupalConnector(
        'file', C21RESTRequests(),
        filesize='size', id='remote_id',
        filename='filename', file='base64_file')
try:
    UniqueFile.storage = get_storage_class(settings.SHARED_DRIVE_STORAGE)()
except AttributeError:
    UniqueFile.storage = DefaultStorage()


class Topic(OrderedModel, DrupalModel, NameUnicodeMixin):
    objects = OrderedManager()
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    remote_id = models.IntegerField(null=True, db_index=True)

    drupal = DrupalConnector(
        'class', C21RESTRequests(),
        title='name', id='remote_id')

    def __unicode__(self):
        return "%s" % self.name


class Module(OrderedModel, DrupalModel, NameUnicodeMixin):
    objects = OrderedManager()
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    topic = models.ForeignKey(Topic, related_name='modules')
    working = models.BooleanField(default=False)
    files = models.ManyToManyField(UniqueFile, through='UniqueFilesofModule')
    remote_id = models.IntegerField(null=True, db_index=True)
    _child_orders = {}

    @property
    def topic_remote_id(self):
        try:
            return self.topic.remote_id
        except Topic.DoesNotExist:
            return None

    @property
    def child_orders(self):
        try:
            return dict(
                (q.remote_id, q.order) for q in self.lessons.all())
        except ValueError:
            return None

    drupal = DrupalConnector(
        'course', C21RESTRequests(),
        title='name', id='remote_id', klass='topic_remote_id', lesson_orders='child_orders')

    def __unicode__(self):
        return "%s: %s" % (unicode(self.topic), self.name)


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


class AuthorsOfFile(OrderedModel):
    objects = AuthorInFileManager()
    author = models.ForeignKey(Author, related_name='files')
    file = models.ForeignKey(UniqueFile, related_name='authors')

    class Meta:
        unique_together = ('author', 'file')
        index_together = ('author', 'file')


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
    _child_orders = {}

    @property
    def child_orders(self):
        try:
            return dict(
                (q.remote_id, q.order) for q in self.questions.all())
        except ValueError:
            return None

    #@property
    # def parent_remote_ids(self):
    #    return [m.remote_id for m in self.modules.all()]

    drupal = DrupalConnector(
        'lesson', C21RESTRequests(),
        title='title', id='remote_id',
        question_orders='child_orders',
        # courses='parent_remote_ids'
    )


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

    @property
    def type(self):
        if self.video:
            return "h5p_content"
        else:
            return "slide"

    @property
    def h5p_library(self):
        if self.video:
            return "H5P.InteractiveVideo"
        else:
            return None

    @property
    def h5p_resources(self):
        if self.video:
            out = list(self.video.versions.all())
            out.append(self.video)
            return out
        else:
            raise AttributeError

    @property
    def h5p_resource_dict(self):
        try:
            return dict([(r.remote_id, r.get_h5p_path())
                         for r in self.h5p_resources])
        except AttributeError:
            return None

    @property
    def json_content(self):
        try:
            h5p_res = self.h5p_resources
        except AttributeError:
            return None
        storage = get_storage_class(settings.STATICFILES_STORAGE)()
        with storage.open(settings.STATIC_ROOT +
                          "h5p_video_template.json") as v_file:
            out = json.loads(v_file.read())
        out['interactiveVideo']['video']['title'] = self.title
        out['interactiveVideo']['video']['startScreenOptions'][
            'shortStartDescription'] = self.byline
        out['interactiveVideo']['video']['files'] = [
            f.h5p_json_content for f in h5p_res]
        return out

    drupal = DrupalConnector(
        'question', C21RESTRequests(),
        title='title', intro='text', id='remote_id',
        type='type', h5p_library='h5p_library',
        h5p_resources='h5p_resource_dict',
        json_content='json_content'
    )


class QuestionsInLesson(OrderedModel):
    objects = QuestionsInLessonManager()
    question = models.ForeignKey(Question)
    lesson = models.ForeignKey(Lesson)

    class Meta(OrderedModel.Meta):
        unique_together = ('question', 'lesson')
        index_together = ('question', 'lesson')


class FilesInQuestion(OrderedModel):
    objects = FilesInQuestionManager()
    file = models.ForeignKey(UniqueFile)
    question = models.ForeignKey(Question)
    product = models.BooleanField(default=False)

    @property
    def question_remote_id(self):
        return self.question.remote_id

    drupal = DrupalConnector(
        "question", C21RESTRequests(), file="file", id="question_remote_id")

    class Meta(OrderedModel.Meta):
        unique_together = ('file', 'question')
        index_together = ('file', 'question')


class LessonsInModule(OrderedModel):
    objects = LessonsInModuleManager()
    lesson = models.ForeignKey(Lesson)
    module = models.ForeignKey(Module)

    class Meta(OrderedModel.Meta):
        unique_together = ('lesson', 'module')
        index_together = ('lesson', 'module')


class PresentationsInQuestion(OrderedModel):
    objects = PresentationsInQuestionManager()
    question = models.ForeignKey(Question)
    presentation = models.ForeignKey(Presentation)

    class Meta(OrderedModel.Meta):
        unique_together = ('question', 'presentation')
        index_together = ('question', 'presentation')
