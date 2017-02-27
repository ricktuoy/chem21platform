import StringIO
import difflib
import html2text

from .base import OrderedModel
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models


class TextVersionManager(models.Manager):
    def create_for_object(self, instance, time=None):
        if time is None:
            time = datetime.now()
        try:
            text = instance.text
        except AttributeError:
            text = instance.intro
        if text is None:
            text = ""
        v_args = {
            'text': text,
            'original': instance,
            'user': instance.user,
            'modified_time': time
        }
        TextVersion.objects.create(**v_args)


class TextVersion(OrderedModel):
    objects = TextVersionManager()
    text = models.TextField()
    user = models.ForeignKey(User, editable=False)
    limit = models.Q(app_label='repo', model='Topic') | \
        models.Q(app_label='repo', model='Module') | \
        models.Q(app_label='repo', model='Lesson') | \
        models.Q(app_label='repo', model='Question')
    modified_time = models.DateTimeField(null=True, blank=True)
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
    published = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        self._older_qs = None
        self._newer_qs = None
        return super(TextVersion, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.user.username + " " + \
            self.original.title + " " + self.strtime()

    def strtime(self):
        try:
            return self.modified_time.strftime("%c")
        except AttributeError:
            return "----"

    def get_html_link_user(self):
        return "%s: <a href=\"%s\">%s</a>" % (
            self.user.username,
            self.get_absolute_url(), self.strtime())

    def get_markdown(self):
        return html2text.html2text(self.text)

    def get_older_version(self):
        if not self._older_qs:
            self._older_qs = self.original.text_versions.filter(
                modified_time__lt=self.modified_time).order_by(
                "-modified_time")
        try:
            return self._older_qs[0]
        except IndexError:
            return None

    def get_newer_version(self):
        if not self._newer_qs:
            self._newer_qs = self.original.text_versions.filter(
                modified_time__gt=self.modified_time).order_by(
                "modified_time")
        try:
            return self._newer_qs[0]
        except IndexError:
            return None

    def get_diff_table(self, diffcls=None):
        if not diffcls:
            diffcls = difflib.HtmlDiff()
        tolines = StringIO(self.get_markdown()).readlines()
        try:
            from_version = self.get_older_version()
            fromlines = StringIO(from_version.get_markdown()).readlines()
        except (AttributeError, ValueError):
            fromlines = []
        return diffcls.make_table(fromlines, tolines)

    def get_absolute_url(self):
        return reverse('version', args=[str(self.id), ])
