import logging
import os

from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from datetime import datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db import transaction
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

    def move_to(self, el):
        type(self).move(self, el)

    class Meta:
        abstract = True
        ordering = ('order',)


class OrderedManagerBase:
    __metaclass__ = ABCMeta

    @abstractproperty
    def order_field(self):
        return None

    @property
    def force_reset_order(self):
        return True

    @abstractmethod
    def order_queryset(self):
        return None

    def order_incr_dict(self):
        return {self.order_field: models.F(self.order_field) + 1}

    def order_decr_dict(self):
        return {self.order_field: models.F(self.order_field) - 1}

    def order_slice_dict(self, val1, val2):
        return {self.order_field + "__gt": val1,
                self.order_field + "__lte": val2}

    def get_order_value(self, el):
        return getattr(el, self.order_field)

    def set_order_value(self, el, val):
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
        logging.debug("Resetting orders")
        i = 1
        logging.debug(self.order_queryset())
        for o in self.order_queryset().order_by(self.order_field):
            logging.debug("Changing order %s " % self.get_order_value(o))
            self.set_order_value(o, i)
            logging.debug("Order is now %s" % self.get_order_value(o))
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
        logging.debug("Order checksum: %s" % self.order_sum())
        logging.debug("Order calculated checksum: %s" % self.order_triangle())
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
    def move_to_top(self, source):
        self._current_element = source
        self._ensure_order_consistent()
        source = self._load_obj_from_arg(source)
        self._current_element = source
        sval = self.get_order_value(source)
        self.order_queryset().filter(
            **self.order_slice_dict(0, sval)).update(**self.order_incr_dict())
        self.set_order_value(source, 1)
        source.save()
        return (True, "Success")

    @transaction.atomic
    def move(self, source, dest):
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

        return (True, "Success")


class OrderedRelationalManagerBase(OrderedManagerBase):

    @abstractproperty
    def order_key(self):
        return None

    def get_order_key_value(self, el):
        return getattr(el, self.order_key)

    def order_queryset(self):
        return self.get_queryset().filter(
            **{self.order_key: self.get_order_key_value(
                self._current_element)})


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


class UniqueFile(OrderedModel):
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
    cut_order = models.IntegerField(default=0)
    ready = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    s3d = models.BooleanField(default=False)

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


class Topic(OrderedModel, NameUnicodeMixin):
    objects = OrderedManager()
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)


class Module(OrderedModel, NameUnicodeMixin):
    objects = OrderedManager()
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    topic = models.ForeignKey(Topic, related_name='modules')
    working = models.BooleanField(default=False)
    files = models.ManyToManyField(UniqueFile, through='UniqueFilesofModule')

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
                               self.event.date, "%m %Y")
                           + " " + self.title) + ext
        else:
            return slugify(" ".join(
                [a.author.full_name for a in self.authors])
                + " " + self.title) + ext

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
    source_files = models.ManyToManyField(UniqueFile)


class PresentationSlide(OrderedModel):
    file = FileBrowseField(max_length=500, null=True)
    duration = models.IntegerField(
        help_text='Duration of this slide in milliseconds')
    html = models.TextField()


class PresentationVersion(BaseModel):
    presentation = models.ForeignKey(Presentation)
    version = models.IntegerField()
    slides = models.ManyToManyField(PresentationSlide)
    audio = models.ForeignKey(UniqueFile)
