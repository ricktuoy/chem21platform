from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from .models import Topic, Module, Lesson, Question
from django.db.models import Prefetch

class BaseLearningObjectLoader(object):
    # efficiently load a bunch of learning objects from Primary Key sets in a querydict 
    # if passing in a querydict on init:
    #   the PKs should be in "questions[]", "lessons[]", "modules[]", "topics[]" by default
    #   these field names correspond to the default model names ["question", "lesson", "module", "topic"]
    #   these can be changed by passing a different list to the "model_names" kwarg on init
    #   if a "publish_all" field is detected in the querydict any PK sets will be ignored and all possible objects will be loaded
    # if no querydict on init:
    #   the loader will try to load all possible objects
    def __init__(self, querydict=None, **kwargs):
        if querydict is not None:
            if "publish_all" in querydict:
                get_all = True
            else:
                get_all=False
        else:
            get_all = True
        self.options = kwargs
        self.get_all = get_all
        self.querydict = querydict
        self.model_names = kwargs.get("model_names", 
            ["question", "lesson", "module", "topic"])

    def _qs(self, model, model_name=None):
        qs = model.objects.exclude(archived=True)
        if not model_name:
            model_name = model.__name__.lower()

        try:
            qs = qs.exclude(**self.options['exclude'])
        except KeyError:
            pass

        try:
            qs = qs.filter(**self.options['filter'])
        except KeyError:
            pass

        if not self.get_all:
            #raise Exception(model_name+"||"+repr(self.querydict.getlist(model_name+"s[]")))
            pkset = [int(pk) for pk in self.querydict.getlist(model_name+"s[]")]
            qs = qs.filter(pk__in=pkset)

        return qs


    def learning_object_reducer(self, a, t):
        model = ContentType.objects.get(
            app_label="repo",
            model=t).model_class()
        return a + list(self._qs(model))

    def get_list(self):
        # returns a flat unsorted list of the objects
        return reduce(self.learning_object_reducer, self.model_names, [])

    def get_structure_queryset(self):
        # returns a hierarchical ordered queryset of the objects
        # note this
        return self._qs(Topic, "topic").prefetch_related(
            Prefetch("modules",
                     queryset=self._qs(Module, "module").order_by('order')),
            Prefetch("modules__lessons",
                     queryset=self._qs(Lesson, "lesson").order_by('order'),
                     to_attr="ordered_lessons"),
            Prefetch("modules__ordered_lessons__questions",
                     queryset=self._qs(Question,"question").order_by('order'),
                     to_attr="ordered_questions"))

    @staticmethod
    def get_reference_from_object(obj):
        name = obj._meta.object_name.lower()+"s"
        return {'name':name, 'value': obj.pk}

    def get_reference_list(self):
        return map(self.get_reference_from_object, self.get_list())

class PageLoader(BaseLearningObjectLoader):
    # load all pages associated with learning objects from PKs passed in a querydict
    # loads all pages if no querydict passed
    @staticmethod
    def page_reducer(a, obj):
        return a.union(obj.iter_publishable()) # learning objects are compared (eq) by URL first
    
    def get_list(self):
        # this adds 
        objs = super(PageLoader, self).get_list()
        return reduce(self.page_reducer, objs, set([]))


class PDFLoader(BaseLearningObjectLoader):
    # load all pdf roots associated with learning objects from PKs passed in a querydict
    # loads all pdf roots if not querydict passed
    @staticmethod
    def pdf_reducer(a, b):
        return a.union(b.iter_pdf_roots())

    def get_list(self):
        objs = super(PDFLoader, self).get_list()
        return reduce(self.pdf_reducer, objs, set([]))