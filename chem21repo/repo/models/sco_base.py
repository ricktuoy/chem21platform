from .base import BaseModel
from .base import UnicodeMixinFactory
from django.db import models
import logging


class LearningTemplate(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class SCOBase(models.Model):
    dirty = models.TextField(default="[]")
    #text_versions = GenericRelation(TextVersion)
    changed = models.BooleanField(default=False)
    dummy = models.BooleanField(default=False)
    quiz_name = models.CharField(max_length=100, blank=True, null=True)
    template = models.ForeignKey(LearningTemplate, null=True, blank=True)
    archived = models.BooleanField(default=False)
    _type_hierarchy = {'topic': 1, 'module': 2, 'lesson': 3, 'question': 4}

    def __init__(self, *args, **kwargs):
        r = super(SCOBase, self).__init__(*args, **kwargs)
        """
        self.drupal.instantiate(self)
        """
        self.fixture_mode = False
        self._parent = None
        return r

    class Meta:
        abstract = True

    def get_next_object(self, check_children=True):
        if check_children:
            # first see if this node has any children; if so get the first
            try:
                ch = self.get_first_display_child()
                if ch is not None:
                    ch.set_parent(self)
                    return ch
            except AttributeError:
                pass

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
    def touched_structure_querysets(self):
        return None

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

    """
    def has_text_changes(self, since=None):
        return self.text_versions.exclude(
            user__pk=1).exclude(user__pk=2).count() or False
    """

    """
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
    """

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
            order__lte=self.order).exclude(
            archived=True).exclude(
            pk=self.pk).order_by('-order')

    def get_later_siblings(self):
        return self.get_siblings().filter(
            order__gte=self.order).exclude(
            archived=True).exclude(
            pk=self.pk).order_by('order')

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

    @property
    def new_children(self):
        return self.children.filter(remote_id__isnull=True)

    @property
    def learning_object_type(self):
        return type(self).__name__.lower()

    @property
    def level(self):
        return self._type_hierarchy[self.learning_object_type]

    @property
    def distfromtopic(self):
        return self.level - 1

    @classmethod
    def get_model_name(kls):
        return kls.__name__.lower()

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
    def get_byline(self):
        if self.is_question:
            try:
                return self.first_question.byline
            except:
                pass
        return None

    def get_text(self):
        try:
            text = self.page.text
            logging.debug("Using page attribute for text")
            return text
        except AttributeError:
            pass
        if self.is_question:
            try:
                return self.first_question.text
            except:
                pass
        return self.text

    def get_title(self):
        try:
            title = self.page.title
            logging.debug("Using page attribute for title")
            return title
        except AttributeError:
            pass
        if self.is_question:
            try:
                return self.first_question.title
            except:
                pass
        return self.title


AuthorUnicodeMixin = UnicodeMixinFactory("full_name")
AuthorUnicodeMixin.__name__ = "AuthorUnicodeMixin"


class Author(BaseModel, AuthorUnicodeMixin):
    full_name = models.CharField(max_length=200, unique=True)
    role = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        if self.role:
            return "%s, %s" % (self.full_name, self.role)
        else:
            return self.full_name
