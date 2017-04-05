from .base import BaseModel
from .base import NameUnicodeMixin
from .base import OrderedRelationalManagerBase
from .base import UnicodeMixinFactory
from .scos import Module
from .scos import Topic
from datetime import datetime
from django.db import models


class AuthorInFileManager(models.Manager, OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "file"


class PresentationsInQuestionManager(models.Manager,
                                     OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "question"


class SourceFilesInPresentationManager(models.Manager,
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


class SlidesInPresentationVersionManager(models.Manager,
                                         OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "presentation"


EventUnicodeMixin = UnicodeMixinFactory(("name", "date"))
EventUnicodeMixin.__name__ = "EventUnicodeMixin"


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
    """
    drupal = DrupalConnector(
        'file', C21RESTRequests(),
        filesize='size', id='remote_id',
        filename='filename', file='base64_file')
    """


class Path(BaseModel, NameUnicodeMixin):
    name = models.CharField(max_length=800, unique=True)
    topic = models.ForeignKey(Topic, related_name='paths', null=True)
    module = models.ForeignKey(Module, related_name='paths', null=True)
    active = models.BooleanField(default=True)
