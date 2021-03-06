import logging

from .sco_base import Author
from .base import BaseModel
from .base import NameUnicodeMixin
from .base import OrderedManager
from .base import OrderedManyToManyManagerBase
from .base import OrderedModel
from .base import OrderedRelationalManagerBase
from .base import TitleUnicodeMixin
from .media import UniqueFile
from .sco_base import SCOBase
from django.core.files.storage import get_storage_class
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Prefetch
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from filebrowser.fields import FileBrowseField


# needed for migration

class AttributionMixin(BaseModel):
    attribution = models.ForeignKey(Author, blank=True, null=True)
    show_attribution = models.BooleanField(default=False)

    class Meta:
        abstract = True


class PageContainerMixin(BaseModel):
    page = models.ForeignKey('Question', blank=True, null=True)

    class Meta:
        abstract = True

    def copy_page_fields_to(self, pg=None):
        pg.title = self.title
        pg.text = self.text


class GlossaryTerm(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(default=[])



class TopicWithStructureManager(OrderedManager):

    def structure_filter(self, **kwargs):
        self._structure_filter = kwargs
        return self

    def structure_exclude(self, **kwargs):
        self._structure_exclude = kwargs
        return self

    def _qs(self, model, model_name=None):
        qs = model.objects.exclude(archived=True)
        if not model_name:
            model_name = model.__name__.lower()
        try:
            qs = qs.exclude(**self._structure_exclude)
        except AttributeError:
            pass

        try:
            qs = qs.filter(**self._structure_filter)
        except AttributeError:
            pass
        return qs

    def get_queryset(self, *args, **kwargs):
        return super(
            TopicWithStructureManager, self).get_queryset(
                *args, **kwargs).prefetch_related(
                    Prefetch(
                        "modules",
                        queryset=self._qs(
                            Module, "module").order_by('order')),
                    Prefetch(
                        "modules__lessons",
                        queryset=self._qs(
                            Lesson, "lesson").order_by('order'),
                        to_attr="ordered_lessons"),
                    Prefetch(
                        "modules__ordered_lessons__questions",
                        queryset=self._qs(
                            Question, "question").order_by('order'),
                        to_attr="ordered_questions"))


class Topic(
        OrderedModel, SCOBase,
        AttributionMixin, PageContainerMixin,
        NameUnicodeMixin):
    objects = OrderedManager()
    objects_with_structure = TopicWithStructureManager()
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, null=True, blank=True)
    code = models.CharField(max_length=10, unique=True)
    remote_id = models.IntegerField(null=True, db_index=True)
    child_attr_name = "modules"
    text = models.TextField(null=True, blank=True, default="")
    icon = FileBrowseField(max_length=500, null=True)

    @property
    def title(self):
        return self.name

    @property
    def is_question(self):
        return False

    @classmethod
    def iter_descendent_models(kls):
        for model in [Module, Lesson, Question]:
            yield model

    @classmethod
    def get_child_classname(kls):
        return "module"

    def get_siblings(self):
        return Topic.objects.filter(code="XXX")

    def get_next_sibling(self):
        return None

    def get_previous_sibling(self):
        return None

    def get_parent(self):
        raise AttributeError

    def get_ancestors(self):
        return []

    def iter_publishable(self):
        self.current_topic = self
        yield self

    def iter_pdf_roots(self):
        return
        yield

    @property
    def touched_structure_querysets(self):
        return [
            Module.objects.filter(topic=self),
            Lesson.objects.filter(modules__topic=self),
            Question.objects.filter(lessons__modules__topic=self)
        ]

    @property
    def title(self):
        return self.name

    @property
    def current_topic(self):
        return self

    @property
    def child_orders(self):
        try:
            return dict(
                (m.remote_id, m.order)
                for m in self.modules.all() if m.remote_id)
        except ValueError:
            return None

    @child_orders.setter
    def child_orders(self, val):
        for rid, order in val:
            m = Module.objects.get_or_pull(remote_id=rid)
            m.topic = self
            m.order = order
            m.save(update_fields=["topic", "order"])

    def __unicode__(self):
        return "%s" % self.name

    def get_absolute_url(self):
        return reverse('topic', kwargs={'slug': self.slug, })

    def get_url_list(self):
        return [self.get_absolute_url(), ]


class Module(
        OrderedModel,
        SCOBase,
        AttributionMixin,
        PageContainerMixin,
        NameUnicodeMixin):
    objects = OrderedManager()
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=100, blank=True, default="")
    code = models.CharField(max_length=10, unique=True)
    topic = models.ForeignKey(Topic, related_name='modules')
    working = models.BooleanField(default=False)
    files = models.ManyToManyField(UniqueFile,
                                   through='UniqueFilesofModule',
                                   related_name="modules")
    remote_id = models.IntegerField(null=True, db_index=True)
    text = models.TextField(null=True, blank=True, default="")
    is_question = models.BooleanField(default=False)
    _child_orders = {}
    child_attr_name = "lessons"

    @property
    def title(self):
        return self.name

    @property
    def current_topic(self):
        return self.topic

    @classmethod
    def iter_descendent_models(kls):
        for model in [Lesson, Question]:
            yield model

    def iter_publishable(self):
        yield self

    def iter_pdf_roots(self):
        return self.iter_publishable()

    def get_pdf_version_url(self, fmt="a4"):
        storage = get_storage_class()()
        return storage.url(self.get_pdf_version_path(fmt))

    def get_pdf_base_path(self):
        return "pdf/%d" % self.pk

    def get_pdf_version_path(self, fmt):
        return "pdf/%d/%s-%s.pdf" % (
            self.pk, self.slug, fmt)

    @property
    def touched_structure_querysets(self):
        return self.topic.touched_structure_querysets

    @classmethod
    def get_child_classname(kls):
        return "lesson"

    @classmethod
    def get_parent_fieldname(kls):
        return "topic"

    def get_ancestors(self):
        return [self.topic, ]

    @property
    def modules(self):
        return [self, ]

    @property
    def first_question(self):
        try:
            return self._first_question
        except AttributeError:
            self._first_question = self.lessons.first().questions.first()
            return self._first_question

    def set_parent(self, parent):
        super(Module, self).set_parent(parent)

    def get_parent(self):
        return self.topic

    @property
    def title(self):
        return self.name

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
                (q.remote_id, q.order)
                for q in self.lessons.all() if q.remote_id)
        except ValueError:
            return None

    @child_orders.setter
    def child_orders(self, val):
        for rid, order in val:
            lesson = Lesson.objects.get_or_pull(remote_id=rid)
            lesson.modules.add(self)
            lesson.order = order
            lesson.save(update_fields=["order", "modules"])

    def __unicode__(self):
        return "%s: %s" % (unicode(self.topic), self.name)

    class Meta:
        permissions = (
            ("can_publish", "Can publish modules"),
            ("change structure", "Can change module structures"),
        )

    def get_absolute_url(self):
        return reverse(
            'module_detail',
            kwargs={'topic_slug': self.topic.slug,
                    'slug': self.slug, })

    def get_url_list(self):
        return [self.get_absolute_url(), ]


class FileInModuleManager(models.Manager, OrderedRelationalManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "module"


class UniqueFilesofModule(OrderedModel):
    objects = FileInModuleManager()
    file = models.ForeignKey(UniqueFile)
    module = models.ForeignKey(Module)

    class Meta(OrderedModel.Meta):
        unique_together = ('file', 'module')
        index_together = ('file', 'module')


class LessonsInModuleManager(models.Manager,
                             OrderedManyToManyManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "modules"


class Lesson(
        OrderedModel,
        SCOBase,
        AttributionMixin,
        PageContainerMixin,
        TitleUnicodeMixin):
    objects = LessonsInModuleManager()
    modules = models.ManyToManyField(Module, related_name="lessons")
    title = models.CharField(max_length=100, blank=True, default="")
    slug = models.CharField(max_length=100, blank=True, default="")
    remote_id = models.IntegerField(null=True, db_index=True)
    text = models.TextField(null=True, blank=True, default="")
    _child_orders = {}
    child_attr_name = "questions"
    is_question = models.BooleanField(default=False)

    @property
    def current_module(self):
        return self.modules.first()

    @property
    def current_topic(self):
        return self.current_module.topic if self.current_module else None

    @classmethod
    def iter_descendent_models(kls):
        yield Question

    def iter_publishable(self):
        yield self

    def iter_pdf_roots(self):
        if self.current_module:
            yield self.current_module

    @property
    def touched_structure_querysets(self):
        return [
            Module.objects.filter(lessons=self),
            Lesson.objects.filter(modules__lessons=self),
            Question.objects.filter(lessons__modules__lessons=self)
        ]

    @classmethod
    def get_child_classname(kls):
        return "question"

    @classmethod
    def get_parent_fieldname(kls):
        return "modules"

    @property
    def first_question(self):
        try:
            return self._first_question
        except AttributeError:
            self._first_question = self.questions.first()
            return self._first_question

    def set_parent(self, parent):
        super(Lesson, self).set_parent(parent)

    def get_parent(self):
        return self.current_module

    @property
    def child_orders(self):
        try:
            return dict(
                (q.remote_id, q.order)
                for q in self.questions.all() if q.remote_id)
        except ValueError:
            return None

    @child_orders.setter
    def child_orders(self, val):
        for rid, order in val:
            q = Question.get(remote_id=rid)
            q.lessons.add(self)
            q.order = order
            q.save(update_fields=["order", "lessons"])

    def get_absolute_url(self):
        return reverse(
            'lesson_detail', kwargs={
                'topic_slug': self.current_module.topic.slug,
                'module_slug': self.current_module.slug,
                'slug': self.slug})

    def get_url_list(self):
        urls = []
        for module in self.modules.all():
            self.current_module = module
            self.current_topic = module.topic
            urls.append(self.get_absolute_url())
        return urls

    def get_touched_url_list(self, fields_changed=None):
        urls = []
        for module in self.modules.all():
            pass
        return urls


class QuestionsInLessonManager(models.Manager,
                               OrderedManyToManyManagerBase):

    @property
    def order_field(self):
        return "order"

    @property
    def order_key(self):
        return "lessons"


class Question(OrderedModel, SCOBase, AttributionMixin, TitleUnicodeMixin):
    objects = QuestionsInLessonManager()
    title = models.CharField(max_length=100, blank=True, default="")
    slug = models.CharField(max_length=100, blank=True, default="")
    """
    presentations = models.ManyToManyField(
        Presentation, through='PresentationsInQuestion')
    """
    files = models.ManyToManyField(UniqueFile, related_name="questions", blank=True)
    text = models.TextField(null=True, blank=True, default="")
    byline = models.TextField(null=True, blank=True, default="")
    remote_id = models.IntegerField(null=True, db_index=True)
    lessons = models.ManyToManyField(Lesson, related_name="questions", blank=True)
    child_attr_name = "files"

    @property
    def is_question(self):
        return False

    @property
    def current_lesson(self):
        return self.lessons.first()

    @property
    def current_module(self):
        return self.current_lesson.modules.first() if self.current_lesson else None

    @property
    def current_topic(self):
        return self.current_module.topic if self.current_module else None

    @classmethod
    def iter_descendent_models(kls):
        return []

    def iter_publishable(self):
        yield self

    def iter_pdf_roots(self):
        if self.current_module:
            yield self.current_module

    @property
    def touched_structure_querysets(self):
        lessons = Lesson.objects.filter(questions=self)
        modules = Module.objects.filter(
            lessons__is_question=True,
            lessons__questions=self)
        return [
            modules,
            lessons,
            Question.objects.filter(lessons__questions=self)
        ]

    @property
    def first_question(self):
        return self

    @property
    def modules(self):
        modules = []
        for lesson in self.lessons.all():
            modules += list(lesson.modules.all())
        return list(set(modules))

    @classmethod
    def get_parent_fieldname(kls):
        return "lessons"

    def get_last_display_child(self):
        return None

    def get_first_display_child(self):
        return None

    def set_parent(self, parent):
        super(Question, self).set_parent(parent)
        self.current_lesson.set_parent(self.current_module)

    def get_parent(self):
        return self.current_lesson

    def get_canonical_page(self):
        pg = self._get_canonical_parent_via_page_relation()
        return pg if pg else self

    def _get_canonical_parent_via_page_relation(self):
        return self.page_of_lesson if self.page_of_lesson else \
            self.page_of_module if self.page_of_module else \
            self.page_of_topic if self.page_of_topic else None

    @property
    def page_of_lesson(self):
        try:
            return Lesson.objects.get(page=self)
        except Lesson.DoesNotExist:
            return None

    @property
    def page_of_module(self):
        try:
            return Module.objects.get(page=self)
        except Module.DoesNotExist:
            return None

    @property
    def page_of_topic(self):
        try:
            return Topic.objects.get(page=self)
        except Topic.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        if getattr(self, 'fixture_files_only', False):
            kwargs['update_fields'] = ['files', ]
        super(Question, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            'question_detail',
            kwargs={'topic_slug': self.current_module.topic.slug,
                    'module_slug': self.current_module.slug,
                    'lesson_slug': self.current_lesson.slug,
                    'slug': self.slug, })

    def get_touched_url_list(self, fields_changed=None):
        urls = []
        if fields_changed is None or 'title' in fields_changed \
                or 'slug' in fields_changed:
            lessons = self.lessons.all()
            for lesson in lessons:
                for module in lesson.modules.all():
                    lesson.current_module = module
                    lesson.current_topic = module.topic
                    if lesson.dummy == "-" or lesson.dummy:
                        urls.append(module.get_absolute_url())
                    urls.append(lesson.get_absolute_url())
                    for question in lesson.questions.all():
                        question.current_lesson = lesson
                        question.current_module = module
                        question.current_topic = module.topic
                        urls.append(question.get_absolute_url())
        return urls

    def get_byline(self):
        if not self.byline and self.video:
            return self.video.author_string
        elif self.byline:
            return self.byline
        else:
            return ""

    # ################ Helper attributes ########################

    @property
    def pdf(self, reset=False):
        if not reset:
            try:
                return self._cached_pdf
            except AttributeError:
                pass
        try:
            self._cached_pdf = list(
                self.files.filter(ext=".pdf").exclude(
                    remote_id__isnull=True)[:1])[0]
        except (IndexError, ValueError):
            try:
                self._cached_pdf = list(self.files.filter(ext=".pdf")[:1])[0]
            except (IndexError, ValueError):
                self._cached_pdf = None
        return self._cached_pdf

    @property
    def video(self, reset=False):
        if not reset:
            try:
                return self._cached_video
            except AttributeError:
                pass
        try:
            self._cached_video = list(
                self.files.filter(
                    type="video").exclude(remote_id__isnull=True)[:1])[0]
        except (IndexError, ValueError):
            try:
                self._cached_video = list(
                    self.files.filter(type="video")[:1])[0]
            except (IndexError, ValueError):
                self._cached_video = None
        return self._cached_video

    @property
    def videos(self, reset=False):
        if not reset:
            try:
                return self._cached_videos
            except AttributeError:
                pass
        try:
            self._cached_videos = list(self.files.filter(type="video"))
        except ValueError:
            self._cached_videos = None
        return self._cached_videos


