from chem21repo.repo.models import Lesson
from chem21repo.repo.models import Module
from chem21repo.repo.models import Question
from chem21repo.repo.models import Topic
from chem21repo.repo.models import UniqueFile
from chem21repo.repo.models import PresentationAction
from django.views.generic import DetailView
from django.views.generic import ListView
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from abc import abstractmethod
from abc import abstractproperty
from abc import ABCMeta
import hashlib


class JSONResponseMixin:

    """
    A mixin that can be used to render a JSON response.
    """

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, ev):
        tr = traceback.format_exc()
        try:
            e, status = ev
        except ValueError:
            e = ev
            status = 400
        self._error = {'message': str(e), 'stacktrace': tr}
        self._error_status = status

    @property
    def status_code(self):
        return self._error_status

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        if hasattr(self, "error") and self.error:
            context['error'] = self.error
            response_kwargs['status'] = self.status_code
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
        )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        return context


class JSONView(JSONResponseMixin, TemplateView):

    def render_to_response(self, context, **response_kwargs):
        try:
            response_kwargs['safe'] = self.__class__.safe
        except AttributeError:
            pass
        return self.render_to_json_response(context, **response_kwargs)



class VideoTimelineView(JSONView):
    def get_context_data(self, *args, **kwargs):
        pk = kwargs['pk']
        vid = get_object_or_404(UniqueFile, pk=pk)
        timeline = vid.actions
        return {
            'title': vid.title,
            'remote': vid.get_remote_url(),
            'data': [ a.as_json() for a in timeline.all() ]
        } 
# TODO: turn this into a URL then add it to 
# the vars passed to video token




class LearningView(DetailView):
    def get_template_names(self):
        if self.object.template:
            return ["chem21/%s.html" % self.object.template.name,]
        return super(LearningView, self).get_template_names()

    def get_context_data(self, *args, **kwargs):
        class Opt(object):
            def __init__(self, label, name, parent_fieldname):
                self.app_label = label
                self.model_name = name
                self.parent_fieldname = parent_fieldname

        context = super(LearningView, self).get_context_data(**kwargs)

        obj = context['object']
        self.object = obj

        try:
            obj.set_parent(self.parent)
        except AttributeError:
            pass
        try:
            slug = self.kwargs['topic_slug']
        except KeyError:
            slug = self.kwargs['slug']

        context['class_tree'] = Topic.objects.filter(
            slug=slug).prefetch_related(
            Prefetch("modules",
                     queryset=Module.objects.all().exclude(archived=True).order_by('order')),
            Prefetch("modules__lessons",
                     queryset=Lesson.objects.all().exclude(archived=True).order_by('order'),
                     to_attr="ordered_lessons"),
            Prefetch("modules__ordered_lessons__questions",
                     queryset=Question.objects.all().exclude(archived=True).order_by(
                         'order'),
                     to_attr="ordered_questions")).first()

        context['current_topic'] = context[
            'object'].current_topic = context['class_tree']

        try:
            context['current_module'] = context[
                'object'].current_module = self.module
        except AttributeError:
            pass

        try:
            context['current_lesson'] = context[
                'object'].current_lesson = self.lesson
        except AttributeError:
            pass

        context['breadcrumbs'] = obj.get_ancestors()
        models =  [Module, Topic, Lesson, Question, UniqueFile, PresentationAction]
        cts = ContentType.objects.get_for_models(*models, for_concrete_models=False)

        context['opts'] = dict([(ct.model.replace(" ", ""),
                                Opt(ct.app_label, ct.model, getattr(m,'get_parent_fieldname', None)))
                                for m, ct in
                                cts.iteritems()])
        context['opts']['current'] = context['opts'][ContentType.objects.get_for_model(obj).model.replace(" ","")]
        
        try:
            context['opts']['child'] = context['opts'][obj.get_child_classname()]
        except AttributeError:
            pass

        nxt = obj.get_next_object()
        prev = obj.get_previous_object()
        
        if nxt:
            context['next'] = nxt
        if prev:
            context['previous'] = prev

        try:
            if obj.is_question:
                context['learning_reference_type'] = "question"
                context['learning_reference_pk'] = obj.first_question.pk
        except AttributeError:
            pass
        
        if 'learning_reference_type' not in context:
            context['learning_reference_type'] = self.name
            context['learning_reference_pk'] = obj.pk
        return context






class MediaUpload(object):
    def __init__(self, f):
        self.handle = handle
        self.file = f
        pass

    def process(self):
        self.handle.process(f)


class FrontView(ListView):
    template_name = "chem21/front.html"
    model = Topic

    def get_queryset(self):
        return Topic.objects.prefetch_related(
            Prefetch("modules",
                     queryset=Module.objects.all().exclude(archived=True).order_by('order'),
                     to_attr="ordered_children"),
            Prefetch("ordered_children__lessons",
                     queryset=Lesson.objects.all().exclude(archived=True).order_by('order'),
                     to_attr="ordered_children"))


class TopicView(LearningView):
    template_name = "chem21/topic.html"
    model = Topic
    name = "topic"


class QuestionView(LearningView):
    template_name = "chem21/question.html"
    name = "question"


    def get_queryset(self):
        self.module = get_object_or_404(
            Module, slug=self.kwargs['module_slug'])
        self.lesson = get_object_or_404(
            Lesson, slug=self.kwargs['lesson_slug'],
            modules=self.module)
        self.parent = self.lesson

        return Question.objects.filter(lessons=self.lesson)

    def get_context_data(self, *args, **kwargs):
        context = super(QuestionView, self).get_context_data(
            self, *args, **kwargs)
        questions = list(context['object'].get_siblings().all())
        question_pks = [q.pk for q in questions]
        question_orders = dict(
            zip(question_pks, range(1, len(questions) + 1)))
        context['num_questions'] = len(questions)
        qnum = question_orders[context['object'].pk]
        context['question_num'] = qnum
        return context




class LessonView(LearningView):
    template_name = "chem21/lesson.html"
    name = "lesson"

    def get_queryset(self):
        self.module = get_object_or_404(
            Module, slug=self.kwargs['module_slug'])
        self.parent = self.module
        return Lesson.objects.filter(modules=self.module)


class ModuleView(LearningView):
    template_name = "chem21/module.html"
    model = Module
    name = "module"




