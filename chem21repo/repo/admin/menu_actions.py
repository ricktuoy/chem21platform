from django.core.urlresolvers import reverse, NoReverseMatch
import re
from django.conf import settings
from collections import OrderedDict
from ..models import Question
import logging


class BasePageMenuAction(object):
    view_name = None

    def __init__(self, page):
        self.page = page

    @property
    def url(self):
        try:
            return reverse(
                self.view_name,
                args=[self.page.pk, ] + ([0, ] * (len(self.params))))
        except NoReverseMatch:
            return ""

    @property
    def name(self):
        return type(self).__name__

    @property
    def param_string(self):
        return ",".join(self.params)


class ActionClassFactory(object):
    @staticmethod
    def to_snake(s):
        return re.sub(
            '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))',
            '_\\1',
            s).lower().strip('_')

    @staticmethod
    def create(
            action_name, display_name="",
            params=[], instruction="", view_name=""):
        view_name = view_name if view_name else \
            "admin:%s" % ActionClassFactory.to_snake(action_name)

        class NewAction(BasePageMenuAction):
            pass
        NewAction.view_name = view_name
        NewAction.params = params
        NewAction.instruction = instruction
        NewAction.display_name = display_name if display_name else action_name
        NewAction.name = action_name
        NewAction.__name__ = ("%sAction" % action_name)
        return NewAction


class PageActionRegistry(OrderedDict):
    _instance = None

    def __init__(self, *args, **kwargs):
        ret = super(PageActionRegistry, self).__init__(*args, **kwargs)
        for category, verbs in settings.LMS_PAGE_MENU:
            try:
                for verb, kwargs in verbs:
                    kwargs['display_name'] = verb.capitalize()
                    self.register(
                        category,
                        "%s%s" % (verb, category),
                        **kwargs)
            except ValueError:   # no kwargs
                for verb in verbs:
                    self.register(
                        category,
                        "%s%s" % (verb, category),
                        display_name=verb.capitalize())
        return ret

    @classmethod
    def get(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def register(self, category, action_name, **kwargs):
        if category not in self:
            self[category] = []
        logging.debug(category)
        self[category].append(ActionClassFactory.create(action_name, **kwargs))

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, v):
        try:  # looks like a request
            self._page = v.context['object']
            return
        except (AttributeError, KeyError):
            pass
        try:  # looks like a context
            self._page = v['object']
            return
        except(TypeError, KeyError):
            pass
        if hasattr(v, 'pk'):  # looks like an object
            self._page = v
        else:  # looks like an int probably
            return Question.objects.get(v)

    def itercategories(self):
        for category, actions in self.iteritems():
            yield (category, [cls(self.page) for cls in actions])
