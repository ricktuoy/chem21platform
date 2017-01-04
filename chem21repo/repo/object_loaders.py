from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from .models import Topic, Module, Lesson, Question
from django.db.models import Prefetch
from django.db.models import Q
import logging


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
        self.pk_sets = {}

    @staticmethod
    def get_model_name(model):
        return model.__name__.lower()

    def get_pk_set(self, model_name):
        if model_name not in self.pk_sets:
            self.pk_sets[model_name] = [int(pk) for pk in self.querydict.getlist(model_name+"s[]")]
        return self.pk_sets[model_name]

    def descendents_query_modifier(self, model, query_vars_fn):

        descendent_models = list(model.iter_descendent_models())
        clauses = Q(**query_vars_fn(model)) 
        for descendent_model in descendent_models:
            field_name = reduce(
                    lambda acc, m: acc + m.get_model_name() +"s__",
                    descendent_models[:descendent_models.index(descendent_model)],
                    ""
                )
            this_query_vars = {}
            orig_query_vars = query_vars_fn(descendent_model)
            for k, v in orig_query_vars.iteritems():

                this_query_vars[field_name+"%s" % k] = v
            clauses |= Q(**this_query_vars)
        return clauses

    def pks_queryset(self, model, model_name=None, ancestors=False):

        qs = model.objects.exclude(archived=True)

        if not model_name:
            model_name = self.get_model_name(model)

        try:
            qs = qs.exclude(**self.options['exclude'])
        except KeyError:
            pass

        try:
            if not ancestors:
                qs = qs.filter(**self.options['filter'])
            else:
                qs = qs.filter(self.descendents_query_modifier(model, lambda model: self.options['filter']))
        except KeyError:
            logging.debug("Got a key error")
            pass

    
        if not self.get_all:
            get_pk_query_vars = lambda model: {'pk__in':self.get_pk_set(model.get_model_name())}
            if not ancestors:
                qs = qs.filter(**get_pk_query_vars(model))
            else:
                qs = qs.filter(self.descendents_query_modifier(model, get_pk_query_vars))
        
        
        return qs



    def learning_object_reducer(self, a, t):
        model = ContentType.objects.get(
            app_label="repo",
            model=t).model_class()
        return a + list(self.pks_queryset(model))

    def get_list(self):
        # returns a flat unsorted list of the objects
        return reduce(self.learning_object_reducer, self.model_names, [])

    def get_structure_queryset(self):
        # returns a hierarchical ordered queryset of the objects
        # note this
        return self.pks_queryset(Topic, "topic", ancestors=True).prefetch_related(
            Prefetch("modules",
                     queryset=self.pks_queryset(Module, "module", ancestors=True).order_by('order').distinct()),
            Prefetch("modules__lessons",
                     queryset=self.pks_queryset(Lesson, "lesson", ancestors=True).order_by('order').distinct(),
                     to_attr="ordered_lessons"),
            Prefetch("modules__ordered_lessons__questions",
                     queryset=self.pks_queryset(Question,"question", ancestors=True).order_by('order').distinct(),
                     to_attr="ordered_questions")).distinct()


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