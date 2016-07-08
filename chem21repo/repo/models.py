import json
import logging
import os
import base64
import mimetypes
import difflib
import html2text
import logging


from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from chem21repo.api_clients import C21RESTRequests, RESTError
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
from StringIO import StringIO
from io import BytesIO
from django.contrib.auth.models import User
from oauth2client.contrib.django_orm import CredentialsField
from PIL import Image
from djchoices import DjangoChoices, ChoiceItem
from django.db.models import Max


class CredentialsModel(models.Model):
  id = models.ForeignKey(User, primary_key=True)
  credential = CredentialsField()

class Biblio(models.Model):
    citekey = models.CharField(max_length=300, unique=True)
    title = models.CharField(max_length=500, blank=True, default="")
    display_string = models.CharField(max_length=1000, blank=True, default="")
    inline_html = models.TextField(null=True, blank=True)
    footnote_html = models.TextField(null=True, blank=True)

    unknown = models.BooleanField(default=False)

    def bust(self):
        self._get_html_from_drupal()

    def _get_html_from_drupal(self):

        try:
            api = C21RESTRequests()
            ret = api.get_endnode_html(self.citekey)
            self.inline_html = ret[0]['html']
            self.footnote_html = self.inline_html
            self.title = ret[0]['value']
            self.save()
        except IndexError:
            self.unknown = True
            self.inline_html = ""
            self.footnote_html = ""
            self.title = ""
            self.save()
            raise Biblio.DoesNotExist("Unknown reference: '%s'." % self.citekey)

    def get_inline_html(self):
        if self.unknown:
            return False
        if self.inline_html is None:
            try:
                self._get_html_from_drupal()
            except Biblio.DoesNotExist:
                return False
        return self.inline_html

    def get_footnote_html(self):
        if self.unknown:
            return False
        if self.footnote_html is None:
            try:
                self._get_html_from_drupal()
            except Biblio.DoesNotExist:
                return False
        return self.footnote_html

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "title__icontains", )

    def __unicode__(self):
        return self.citekey+": "+self.title




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


def UnicodeMixinFactory(name_field):
    class _NameMixin(object):

        def __unicode__(self):
            try:
                n = getattr(self, name_field)
                if n:
                    return n
                else:
                    return ""
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


class Author(BaseModel, AuthorUnicodeMixin):
    full_name = models.CharField(max_length=200, unique=True)
    role = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        if self.role:
            return "%s, %s" % (self.full_name, self.role)
        else:
            return self.full_name

class AttributionMixin(BaseModel):
    attribution = models.ForeignKey(Author, blank=True, null=True)
    show_attribution = models.BooleanField(default=False)
    class Meta:
        abstract = True
    

class DrupalManager(models.Manager):

    def get_or_pull(self, *args, **kwargs):
        try:
            return self.get(*args, **kwargs)
        except self.model.DoesNotExist:
            instance = self.model(*args, **kwargs)
            instance.drupal.pull()
            instance.save()
            return instance

class LearningTemplate(models.Model):
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name


class DrupalModel(models.Model):
    dirty = models.TextField(default="[]")
    text_versions = GenericRelation(TextVersion)
    changed = models.BooleanField(default=False)
    dummy = models.BooleanField(default=False)
    quiz_name = models.CharField(max_length=100, blank=True, null=True)
    template = models.ForeignKey(LearningTemplate, null=True, blank=True)
    archived = models.BooleanField(default=False)


    @property
    def quiz(self):
        try:
            if self.is_question:
                return self.first_question.quiz
        except:
            pass
        if self.quiz_name:
            return self.quiz_name


    @property
    def has_quiz(self):
        if self.quiz:
            return True
        return False

    def has_text_changes(self, since=None):
        return self.text_versions.exclude(
            user__pk=1).exclude(user__pk=2).count() or False

    def get_title(self):
        return self.title

    def get_text(self):
        if not self.text:
            try:
                q = self.questions.first()
                q.dummy = True
                q.save()
                return q.text
            except:
                pass
        return self.text

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

    def get_first_child(self):
        child = self.children.all().order_by('order').first()
        child.set_parent(self)
        return child

    def get_first_child_url(self):
        try:
            return self.get_first_child().get_absolute_url()
        except:
            return None

    @property
    def child_attr_name(self):
        raise AttributeError

    def set_parent(self, parent):
        self._parent = parent
        return None

    def get_parent(self):
        return self._parent

    def get_ancestors(self):
        try:
            par = self.get_parent()
        except AttributeError:
            return []
        if not par:
            return ["??", ]
        if par.slug == "-" or par.dummy:
            return par.get_ancestors()
        return par.get_ancestors() + [self.get_parent(), ]

    def get_siblings(self):
        return self.get_parent().children

    def get_earlier_siblings(self):
        return self.get_siblings().filter(
            order__lte=self.order).exclude(archived=True).exclude(pk=self.pk).order_by('-order')

    def get_later_siblings(self):
        return self.get_siblings().filter(
            order__gte=self.order).exclude(archived=True).exclude(pk=self.pk).order_by('order')

    def _get_display_child_help(self, reverse=False):
        # raise <child_class>.DoesNotExist if no children
        order = "order"
        if reverse:
            order = "-" + order
        qs = self.children.all().exclude(archived=True).order_by(order)

        # get the first child except if we know it's a dummy
        i = 0
        try:
            if self.is_question and not reverse:
                # avoid the first child: it's a dummy
                i = 1
        except AttributeError:
            pass

        try:
            ch = qs[i]
        except IndexError:
            return None

        # now check we haven't got a dummy child for reverse case
        # this will only happen when it's an only child of a pseudo-question
        # in which case we try to get a second child from the queryset 
        # this will raise IndexError if it is in fact a dummy

        try:
            if self.is_question and reverse:
                _ = qs[1].get()
        except AttributeError:
            pass
        except IndexError:
            return None
        return ch


    def get_first_display_child(self):
        return self._get_display_child_help(reverse=False)

    def get_last_display_child(self):
        ch = self._get_display_child_help(reverse=True)
        if ch:
            ch.set_parent(self)
        return ch

    def get_recurse_last_display_child(self):
        ch = self.get_last_display_child()
        if ch is None or ch == self:
            return self
        else:
            return ch.get_recurse_last_display_child()

    def get_next_sibling(self):
        sibs = self.get_later_siblings()
        p = self.get_parent()
        try:
            p.current_module = self.current_module
        except AttributeError:
            pass
        try:
            sib = sibs[0]
        except IndexError:
            return None
        sib.set_parent(p)
        return sib

    def get_next_object(self, check_children=True):
        if check_children:#
            # first see if this node has any children; if so get the first
            try:
                ch = self.get_first_display_child()
                if ch is not None and not isinstance(ch, UniqueFile):
                    ch.set_parent(self)
                    return ch
            except AttributeError:
                pass
            """
            ch = self.children.all().exclude(archived=True).order_by('order').first()
            if ch is not None and ch.dummy and not isinstance(ch, UniqueFile):
                o = ch
                o.set_parent(self)
                sib = o.get_next_sibling()
                if sib:
                    return sib
            """
        sib = self.get_next_sibling()
        if sib:
            return sib
        try:
            return self.get_parent().get_next_object(check_children=False)
        except AttributeError:
            return None

    def get_previous_object(self, check_children=True):
        try:
            sibs = self.get_earlier_siblings()
        except AttributeError:
            return None
        try:
            p = self.get_parent()
        except AttributeError:
            p = None

        #TODO: need to check for situation where parent is_question
        # in this situation, we need to check self is not the first child of parent
        # e.g. check sibs[1]
        try:
            p.current_module = self.current_module
        except AttributeError:
            pass
        try:
            o = sibs[0]
        except IndexError:
            if p is not None:
                return p
            else:
                return None
        try:
            if p.is_question:
                _ = sibs[1]
        except AttributeError: 
            pass
        except IndexError:
            return p
        if p is not None:
            o.set_parent(p)
        if check_children:
            ch = o.get_recurse_last_display_child()
            if ch:
                return ch
        return o

    @property
    def new_children(self):
        return self.children.filter(remote_id__isnull=True)

    @property
    def learning_object_type(self):
        return type(self).__name__.lower()
    

    def __init__(self, *args, **kwargs):
        r = super(DrupalModel, self).__init__(*args, **kwargs)
        self.drupal.instantiate(self)
        self.fixture_mode = False
        self._parent = None
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

    @property
    def new_order_val(self):
        return self.order_queryset().aggregate(Max('order'))['order__max'] + 1

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
            print i
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
            **{self.order_key: self._get_order_key_value()})


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
        instance.changed = True
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

@receiver(models.signals.pre_save)
def save_slug_and_order(sender, instance, **kwargs):
    if isinstance(instance, Question) or isinstance(instance, Lesson) \
            or isinstance(instance, Topic) or isinstance(instance, Module):
        if not instance.slug:
            instance.slug = slugify(instance.title)
        
            

@receiver(models.signals.post_save, dispatch_uid="save_order")
def save_order(sender, instance, raw, **kwargs):
    if isinstance(instance, OrderedModel):
        if not instance.order:
            try:
                instance.order = sender.objects.new_order_val # insert at end
            except:
                pass


@receiver(models.signals.post_save, dispatch_uid="save_text_version")
def save_text_version(sender, instance, raw, **kwargs):
    if isinstance(instance, DrupalModel) \
            and not isinstance(instance, UniqueFile):

        if kwargs.get("update_fields", False):
            if 'text' not in 'update_fields' \
                    and 'intro' not in 'update_fields':
                return
        if kwargs.get("created", False):
            return
        if not raw and hasattr(instance, "user"):
            TextVersion.objects.create_for_object(instance)



@receiver(models.signals.m2m_changed)
def generate_dirty_m2m_record(sender, instance, action,
                              reverse, model, pk_set, **kwargs):

    if not(issubclass(model, DrupalModel) and
            isinstance(instance, DrupalModel)) or instance.fixture_mode:
        return
    if action != "post_add" and action != "post_remove":
        return
    if reverse:
        # children = [instance, ]
        parents = list(model.objects.filter(pk__in=pk_set))
        parent_model = model
    else:
        # children = list(model.objects.filter(pk__in=pk_set))
        parents = [instance, ]
        parent_model = instance.__class__
    parent_fields = parent_model.drupal.child_fields()

    if parent_fields:
        try:
            for p in parents:
                # raise Exception("Found a parent")
                p.drupal.mark_fields_changed(parent_fields)
                p.save(update_fields=["dirty", ])
        except:
            pass

@receiver(models.signals.m2m_changed)
def save_m2m_order(sender, instance, action,
               reverse, model, pk_set, **kwargs):
    if not (isinstance(instance, Question) or isinstance(instance, Lesson) \
            or isinstance(instance, Topic) or isinstance(instance, Module)):
        #logging.debug("Not saving the order, wrong type so fuck you.")
        return
    if action != "post_add":
        #logging.debug("This is not post add")
        return
    logging.debug("Trying to save m2m order")
    if not reverse:
        children = [instance, ]
        parents = list(model.objects.filter(pk__in=pk_set))
        parent_model = model
        child_model = instance.__class__
    else:
        children = list(model.objects.filter(pk__in=pk_set))
        parents = [instance, ]
        parent_model = instance.__class__
        child_model = model
    logging.debug("Children: %s" % repr(children))
    logging.debug("Parents: %s" % repr(parents))
    for c in children:
        logging.debug("Child order %s" % repr(c.order))
        if not c.order:
            c.order = 0
            for p in parents:
                child_model.objects.set_m2m_key_value(p.pk)
                new_order = child_model.objects.new_order_val
                logging.debug(new_order)
                if new_order > c.order:
                    c.order = new_order
            c.save()



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




class Molecule(models.Model):
    name = models.CharField(max_length=100, null=True, unique=True)
    mol_def = models.TextField(null=True, blank=True, default="")
    smiles_def = models.CharField(max_length=200, null=True, unique=True)
    def __unicode__(self):
        return self.name

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
    thumbnail = models.ForeignKey('self', related_name='thumbnail_of', null=True)
    cut_order = models.IntegerField(default=0)
    ready = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    s3d = models.BooleanField(default=False)
    remote_path = models.CharField(max_length=255, null=True, blank=True)
    remote_id = models.IntegerField(null=True, db_index=True)
    authors = models.ManyToManyField(Author, blank=True)
    description = models.TextField(null=True, blank=True, default="")
    molecule = models.ForeignKey(Molecule, null=True, related_name='related_files')
    youtube_id = models.CharField(max_length=50, null=True, blank=True)


    def __unicode__(self):
        if self.path:
            return self.path
        elif self.title:
            return self.title
        else:
            return self.checksum

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
            ctx = {'url':self.url,
                    'remote_url':self.get_remote_url(),
                    'byline': self.author_string ,
                    'description': self.description.replace("<p>","").replace("</p>","")}
            if self.render_type=="youtube":
                ctx['remote_id'] = self.youtube_id
            return ctx
        return None

    def get_remote_url(self):
        if self.type == "video":
            if self.render_type == "youtube":
                return "https://www.youtube.com/watch?v=%s&controls=1&preload=none" % self.youtube_id
        return self.url

    
    def get_video_slide_url(self, container_obj, lobj):
        if not self.type == "video":
            return None

        path = self._gen_video_slide_path(container_obj, lobj)
        #if not UniqueFile.storage.exists(path):
        sstorage = get_storage_class(settings.STATICFILES_STORAGE)()
        return sstorage.url("slide_template.jpg")
        with sstorage.open(settings.STATIC_ROOT +
                          "front-slide-template.eps", 'rt') as ps_file:
            data = ps_file.read()
        """
        data = data.replace("(1)", "(%s)" % container_obj.title)
        data = data.replace("(2)", "(%s)" % lobj.title)
        data = data.replace("(3)", "(%s)" % self.author_string)
        """
        data = data.replace("(1)", "(%s)" % "T")
        data = data.replace("(2)", "(%s)" % "U")
        data = data.replace("(3)", "(%s)" % "VS")

        #fh = StringIO()
        with UniqueFile.storage.open(self._gen_video_slide_path_eps(container_obj, lobj), "wb") as fh:
            fh.write(data.encode("utf-8"))
        output = BytesIO()
        fh = BytesIO(data.encode("utf-8"))
        #fh.write(data)
        fh.seek(0)

        with Image.open(fh) as image:
            #logging.debug((image.format, image.size, image.mode))
            #with UniqueFile.storage.open(path, "rw") as output:
            image.save(output, format="JPEG")

        fh.close()
        output.seek(0)
        with UniqueFile.storage.open(path, "wb") as remote:
            remote.write(output.read())


        return UniqueFile.storage.url(path)






    @property
    def _stripped_ext(self):
        try:
            return self.ext.replace(".", "")
        except AttributeError:
            return None

    @property
    def url(self):
        return settings.S3_URL+"/media/"+self.get_file_relative_url()

    def _gen_video_slide_path(self, container_obj, lobj):
        return "front_slides/%s/%s/%s.jpg" % (container_obj.slug, lobj.slug, self.checksum)

    def _gen_video_slide_path_eps(self, container_obj, lobj):
        return "front_slides/%s/%s/%s.eps" % (container_obj.slug, lobj.slug, self.checksum)


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

    @property
    def local_paths(self):
        if not self.pk:
            return []
        pks = self.get_module_pks()
        return [p.name+"/DL_"+self.filename
                for p in Path.objects.filter(
                    module__pk__in=pks)]

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
"""
try:
    UniqueFile.storage = get_storage_class(settings.SHARED_DRIVE_STORAGE)()
except AttributeError:
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
            self.as_json = getattr(self, 
                action_type+"_json", 
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
                    'text': "<p>"+obj.biblio.get_inline_html()+"</p>",
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
                

class Topic(OrderedModel, DrupalModel, AttributionMixin, NameUnicodeMixin):
    objects = OrderedDrupalManager()
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, null=True, blank=True)
    code = models.CharField(max_length=10, unique=True)
    remote_id = models.IntegerField(null=True, db_index=True)
    child_attr_name = "modules"
    text = models.TextField(null=True, blank=True, default="")
    icon = FileBrowseField(max_length=500, null=True)

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

    @property
    def title(self):
        return self.name

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

    drupal = DrupalConnector(
        'class', C21RESTRequests(),
        title='name', id='remote_id',
        course_orders='child_orders')

    def __unicode__(self):
        return "%s" % self.name

    def get_absolute_url(self):
        return reverse('topic', kwargs={'slug': self.slug, })

    def get_url_list(self):
        return [self.get_absolute_url(), ]

class Module(OrderedModel, DrupalModel, AttributionMixin, NameUnicodeMixin):
    objects = OrderedDrupalManager()
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

    @classmethod
    def get_child_classname(kls):
        return "lesson"

    @classmethod
    def get_parent_fieldname(kls):
        return "topic"

    @property
    def modules(self):
        return [ self, ]
    

    @property
    def first_question(self):
        try:
            return self._first_question
        except AttributeError:
            self._first_question = self.lessons.first().questions.first()
            return self._first_question

    @property
    def video(self):
        if self.is_question:
            try:
                return self.first_question.video
            except:
                pass
        return None

    @property
    def videos(self):
        if self.is_question:
            try:
                return self.first_question.videos
            except:
                pass
        return None

    @property
    def byline(self):
        if self.is_question:
            try:
                return self.first_question.byline
            except:
                pass
        return self.byline

    def get_text(self):
        if self.is_question:
            try:
                return self.first_question.text
            except:
                pass
        return self.text

    def get_title(self):
        if self.is_question:
            try:
                return self.first_question.title
            except:
                pass
        return self.title

    def set_parent(self, parent):
        super(Module, self).set_parent(parent)
        self.current_topic = parent

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

    def get_absolute_url(self):
        return reverse(
            'module_detail',
            kwargs={'topic_slug': self.topic.slug,
                    'slug': self.slug, })

    def get_url_list(self):
        return [self.get_absolute_url(), ]


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


class Lesson(OrderedModel, DrupalModel, AttributionMixin, TitleUnicodeMixin):
    objects = LessonsInModuleManager()
    modules = models.ManyToManyField(Module, related_name="lessons")
    title = models.CharField(max_length=100, blank=True, default="")
    slug = models.CharField(max_length=100, blank=True, default="")
    remote_id = models.IntegerField(null=True, db_index=True)
    text = models.TextField(null=True, blank=True, default="")
    _child_orders = {}
    child_attr_name = "questions"
    is_question = models.BooleanField(default=False)

    # define the interface with Drupal
    drupal = DrupalConnector(
        'lesson', C21RESTRequests(),
        title='title', id='remote_id',
        question_orders='child_orders',
    )

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

    """
    @property
    def is_question(self):
        if self.text:
            return False
        try:
            if self.first_question.dummy:
                return self.first_question
        except AttributeError:
            pass
        return False
    """


    @property
    def pdf(self):
        if self.is_question:
            try:
                return self.first_question.pdf
            except:
                pass
        return None

    @property
    def video(self):
        if self.is_question:
            try:
                return self.first_question.video
            except:
                pass
        return None

    @property
    def videos(self):
        if self.is_question:
            try:
                return self.first_question.videos
            except:
                pass
        return None

    @property
    def byline(self):
        if self.is_question:
            try:
                return self.first_question.byline
            except:
                pass
        return self.byline

    def get_text(self):
        if self.is_question:
            try:
                return self.first_question.text
            except:
                pass
        return self.text

    def get_title(self):
        if self.is_question:
            try:
                return self.first_question.title
            except:
                pass
        return self.title

    def set_parent(self, parent):
        super(Lesson, self).set_parent(parent)
        self.current_topic = parent.topic
        self.current_module = parent

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
        return reverse('lesson_detail', kwargs={
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


class Question(OrderedModel, DrupalModel, AttributionMixin, TitleUnicodeMixin):
    objects = QuestionsInLessonManager()
    title = models.CharField(max_length=100, blank=True, default="")
    slug = models.CharField(max_length=100, blank=True, default="")
    presentations = models.ManyToManyField(
        Presentation, through='PresentationsInQuestion')
    files = models.ManyToManyField(UniqueFile, related_name="questions")
    text = models.TextField(null=True, blank=True, default="")
    byline = models.TextField(null=True, blank=True, default="")
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
        self.current_topic = parent.current_module.topic
        self.current_module = parent.current_module
        self.current_lesson = parent
        self.current_lesson.set_parent(self.current_module)

    def get_parent(self):
        return self.current_lesson

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

    def get_url_list(self):
        urls = []
        for lesson in self.lessons.all():
            for module in lesson.modules.all():
                self.current_lesson = lesson
                self.current_module = module
                self.current_topic = module.topic
                urls.append(self.get_absolute_url())
        return urls

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
            return self.video.author_string
        elif self.byline:
            return self.byline
        else:
            return ""


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
    def pdf(self, reset=False):
        if not reset:
            try:
                return self._cached_pdf
            except AttributeError:
                pass
        try:
            self._cached_pdf = list(self.files.filter(ext=".pdf").exclude(remote_id__isnull=True)[:1])[0]
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
            self._cached_video = list(self.files.filter(type="video").exclude(remote_id__isnull=True)[:1])[0]
        except (IndexError, ValueError):
            try:
                self._cached_video = list(self.files.filter(type="video")[:1])[0]
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
