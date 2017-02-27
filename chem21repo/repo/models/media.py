import os

from .base import ActiveManager
from .base import OrderedModel
from .base import OrderedRelationalManagerBase
from .biblio import Biblio
from .sco_base import Author
from .sco_base import SCOBase
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.files.storage import get_storage_class
from django.core.urlresolvers import reverse
from django.db import models
from djchoices import ChoiceItem
from djchoices import DjangoChoices
"""
from PIL import Image
from io import BytesIO
"""


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


class Molecule(models.Model):
    name = models.CharField(max_length=100, null=True, unique=True)
    mol_def = models.TextField(null=True, blank=True, default="")
    smiles_def = models.CharField(max_length=200, null=True, unique=True)

    def __unicode__(self):
        return self.name


class UniqueFile(OrderedModel, SCOBase):
    objects = models.Manager()
    cut_objects = CutManager()
    checksum = models.CharField(max_length=100, null=True, unique=True)
    path = models.CharField(max_length=255, null=True)
    ext = models.CharField(max_length=25, null=True)
    type = models.CharField(max_length=15, default="text", null=True)
    title = models.CharField(max_length=200, null=True)
    size = models.BigIntegerField(default=0)
    # event = models.ForeignKey(Event, null=True)
    # status = models.ForeignKey(Status, null=True)
    # file = FileBrowseField(max_length=500, null=True)
    cut_of = models.ForeignKey('self', related_name='cuts', null=True)
    version_of = models.ForeignKey('self', related_name='versions', null=True)
    thumbnail = models.ForeignKey(
        'self', related_name='thumbnail_of', null=True)
    # cut_order = models.IntegerField(default=0)
    ready = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    s3d = models.BooleanField(default=False)
    remote_path = models.CharField(max_length=255, null=True, blank=True)
    remote_id = models.IntegerField(null=True, db_index=True)
    authors = models.ManyToManyField(Author, blank=True)
    description = models.TextField(null=True, blank=True, default="")
    molecule = models.ForeignKey(
        Molecule, null=True, related_name='related_files')
    youtube_id = models.CharField(max_length=50, null=True, blank=True)

    def __unicode__(self):
        if self.path:
            return self.path
        elif self.title:
            return self.title
        else:
            return self.checksum

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

    def get_title(self):
        if not self.title:
            if self.path:
                return os.path.basename(os.path.basename(self.path))
            else:
                return self.filename
        return self.title

    @property
    def render_type(self):
        if self.type == "video":
            if self.youtube_id:
                return "youtube"
            else:
                return "html5"
        return None

    @property
    def render_args(self):
        if self.type == "video":
            ctx = {
                'url': self.url,
                'remote_url': self.get_remote_url(),
                'byline': self.author_string,
                'description':
                    self.description.replace("<p>", "").replace("</p>", "")}
            if self.render_type == "youtube":
                ctx['remote_id'] = self.youtube_id
            return ctx
        return None

    def get_remote_url(self):
        if self.type == "video" and self.render_type == "youtube":
            return settings.YOUTUBE_URL_TEMPLATE % self.youtube_id
        return self.url

    def get_video_slide_url(self, container_obj, lobj):
        if not self.type == "video":
            return None
        sstorage = get_storage_class(settings.STATICFILES_STORAGE)()
        return sstorage.url("slide_template.jpg")

    @property
    def _stripped_ext(self):
        try:
            return self.ext.replace(".", "")
        except AttributeError:
            return None

    @property
    def url(self):
        return settings.S3_URL + "/media/" + self.get_file_relative_url()
    """
    def _gen_video_slide_path(self, container_obj, lobj):
        return "front_slides/%s/%s/%s.jpg" % (
            container_obj.slug, lobj.slug, self.checksum)

    def _gen_video_slide_path_eps(self, container_obj, lobj):
        return "front_slides/%s/%s/%s.eps" % (
            container_obj.slug, lobj.slug, self.checksum)
    """

    def get_absolute_url(self):
        if self.type == "video":
            return reverse('video_detail', kwargs={'checksum': self.checksum})
        else:
            return self.url

    def get_file_relative_url(self):
        return "sources/" + self.filename

    def get_mime_type(self):
        ext = self._stripped_ext
        if ext is None:
            return None
        else:
            return self.type + "/" + self._stripped_ext

    @property
    def author_string(self):

        authors = list(self.authors.all())
        if len(authors) == 1:
            return unicode(authors[0])
        out = "; ".join(map(unicode, authors[:-1]))
        try:
            return "%s; and %s" % (out, unicode(authors[-1]))
        except IndexError:
            if self.cut_of and self.cut_of.pk != self.pk:
                return self.cut_of.author_string
            return out

    def get_module_pks(self):
        pks = []
        for q in self.questions.all():
            for l in q.lessons.all():
                for m in l.modules.all():
                    pks.append(m.pk)
        return pks

    """
    @property
    def local_paths(self):
        if not self.pk:
            return []
        pks = self.get_module_pks()
        return [p.name + "/DL_" + self.filename
                for p in Path.objects.filter(
                    module__pk__in=pks)]
    """


UniqueFile.storage = DefaultStorage()


class PresentationAction(models.Model):

    class ActionType(DjangoChoices):
        Footnote = ChoiceItem("F")
        Image = ChoiceItem("I")
        Biblio = ChoiceItem("B")

    def _base_json(self):
        return {'start': self.start, 'end': self.end}

    class JSONEncoder():
        def __init__(self, action_type):
            self.as_json = getattr(
                self,
                action_type + "_json",
                PresentationAction._base_json)

        @staticmethod
        def F_json(obj):
            out = PresentationAction._base_json(obj)
            out.update({
                'text': obj.text,
                'target': 'popcorn_footnote'
            })
            return {'footnote': out, }

        @staticmethod
        def I_json(obj):
            out = PresentationAction._base_json(obj)
            out.update({
                'src': obj.image.get_absolute_url(),
                'target': 'popcorn-image'
            })
            if obj.link:
                out['href'] = obj.link
            if obj.text:
                out['text'] = obj.text
            return {'image': out, }

        @staticmethod
        def B_json(obj):
            out = PresentationAction._base_json(obj)
            out.update({
                'text': "<p>" + obj.biblio.get_inline_html() + "</p>",
                'target': 'popcorn_footnote'
            })
            return {'footnote': out, }

    start = models.IntegerField()
    end = models.IntegerField()
    text = models.TextField(null=True, blank=True, default="")
    presentation = models.ForeignKey(UniqueFile, related_name="actions")
    biblio = models.ForeignKey(Biblio, null=True, blank=True)
    image = models.ForeignKey(UniqueFile,
                              null=True,
                              blank=True,
                              related_name="actions_of_image")

    action_type = models.CharField(max_length=1,
                                   choices=ActionType.choices,
                                   validators=[ActionType.validator, ], default="F")

    def as_json(self):
        return PresentationAction.JSONEncoder(
            self.action_type).as_json(self)
