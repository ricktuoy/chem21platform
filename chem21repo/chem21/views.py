from chem21repo.repo.models import Lesson
from chem21repo.repo.models import Module
from chem21repo.repo.models import Question
from chem21repo.repo.models import Topic
from chem21repo.repo.models import UniqueFile
from django.views.generic import DetailView
from django.views.generic import ListView
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType


class LearningView(DetailView):

    def get_context_data(self, *args, **kwargs):
        class Opt(object):
            def __init__(self, label, name):
                self.app_label = label
                self.model_name = name

        context = super(LearningView, self).get_context_data(**kwargs)

        obj = context['object']

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
            "modules",
            Prefetch("modules__lessons",
                     queryset=Lesson.objects.all().order_by('order'),
                     to_attr="ordered_lessons"),
            Prefetch("modules__ordered_lessons__questions",
                     queryset=Question.objects.exclude(dummy=True).order_by(
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
        context['opts'] = dict([(v.model.replace(" ", ""),
                                 Opt(v.app_label, v.model))
                                for k, v in
                                ContentType.objects.get_for_models(
            Module, Topic, Lesson, Question, UniqueFile,
            for_concrete_models=False).iteritems()])
        context['opts']['current'] = context['opts'][ContentType.objects.get_for_model(obj).model.replace(" ","")]

        nxt = obj.get_next_object()
        prev = obj.get_previous_object()
        if nxt:
            context['next'] = nxt
        if prev:
            context['previous'] = prev
        return context


class FrontView(ListView):
    template_name = "chem21/front.html"
    model = Topic

    def get_queryset(self):
        return Topic.objects.prefetch_related(
            Prefetch("modules",
                     queryset=Module.objects.all().order_by('order'),
                     to_attr="ordered_children"),
            Prefetch("ordered_children__lessons",
                     queryset=Lesson.objects.all().order_by('order'),
                     to_attr="ordered_children"))


class TopicView(LearningView):
    template_name = "chem21/topic.html"
    model = Topic


class QuestionView(LearningView):
    template_name = "chem21/question.html"

    def get_queryset(self,):
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

    def get_queryset(self):
        self.module = get_object_or_404(
            Module, slug=self.kwargs['module_slug'])
        self.parent = self.module
        return Lesson.objects.filter(modules=self.module)


class ModuleView(LearningView):
    template_name = "chem21/module.html"
    model = Module
