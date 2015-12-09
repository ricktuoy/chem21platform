import logging

from .models import Lesson
from .models import LessonsInModule
from .models import Module
from .models import Question
from .models import QuestionsInLesson
from .models import Topic
from .models import UniqueFile
from .models import UniqueFilesofModule
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch
from django.http import Http404
from django.views.generic import View
from django.views.generic import DetailView
from django.views.generic import TemplateView
from querystring_parser import parser
from chem21repo.api_clients import RESTError, RESTAuthError

# Create your views here.

from django.http import JsonResponse


class JSONResponseMixin(object):

    """
    A mixin that can be used to render a JSON response.
    """

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
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
        return self.render_to_json_response(context, **response_kwargs)


class HomePageView(TemplateView):
    template_name = "repo/full_listing.html"

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context['files'] = UniqueFile.objects.filter(type="video")
        topics = Topic.objects.all().prefetch_related(
            "modules",
            Prefetch("modules__uniquefilesofmodule_set",
                     queryset=UniqueFilesofModule.objects.filter(
                         file__active=True,
                         file__type="video", file__cut_of__isnull=True),
                     to_attr="ordered_videos"),
            Prefetch("modules__ordered_videos__file__cuts",
                     queryset=UniqueFile.objects.filter(
                         type="video").order_by('cut_order')),
            Prefetch("modules__lessons",
                     queryset=Lesson.objects.all().order_by('order'),
                     to_attr="ordered_lessons"),
            Prefetch("modules__ordered_lessons__questions",
                     queryset=Question.objects.all().order_by(
                         'order'),
                     to_attr="ordered_questions")
        )

        class Opt(object):

            def __init__(self, label, name):
                self.app_label = label
                self.model_name = name

        context['topics'] = topics
        context['opts'] = dict([(v.model.replace(" ", ""),
                                 Opt(v.app_label, v.model))
                                for k, v in
                                ContentType.objects.get_for_models(
            Module, Topic, UniqueFile, Lesson, Question,
            for_concrete_models=False).iteritems()])
        logging.debug(context['opts'])
        return context


class VideoView(DetailView):
    model = UniqueFile
    template_name = "repo/video_detail.html"
    slug_field = "checksum"
    slug_url_kwarg = "checksum"


class MoveViewBase:
    __metaclass__ = ABCMeta

    @abstractproperty
    def orderable_model(self):
        return None

    @property
    def orderable_manager(self):
        return self.orderable_model.objects

    def get_context_data(self, **kwargs):
        context = {}
        try:
            from_el = self.orderable_manager.get(id=kwargs['from_id'])
        except self.orderable_model.DoesNotExist:
            raise Http404("%s not found." %
                          self.orderable_model._meta.verbose_name.title())
        context['original_order'] = self.orderable_manager.get_order_value(
            from_el)
        if "to_id" not in kwargs or kwargs['to_id'] == "0":
            # no dest id or dest id==0 then move element to top
            context['new_order'] = 1
            context['success'], context[
                'message'] = self.orderable_manager.move_to_top(from_el)
            return context
        try:
            # get dest element
            to_el = self.orderable_manager.get(id=kwargs['to_id'])
        except self.orderable_model.DoesNotExist:
            # bad dest id passed
            context['success'] = False
            context['message'] = "Destination %s not found." % (
                self.orderable_model._meta.verbose_name.title(),)
            return context
        context['new_order'] = self.orderable_manager.get_order_value(to_el)
        context['success'], context[
            'message'] = self.orderable_manager.move(from_el, to_el)
        return context


class SourceFileMoveView(MoveViewBase, JSONView):
    orderable_model = UniqueFilesofModule


class CutFileMoveView(MoveViewBase, JSONView):
    orderable_model = UniqueFile
    orderable_manager = UniqueFile.cut_objects


class ModuleMoveView(MoveViewBase, JSONView):
    orderable_model = Module


class TopicMoveView(MoveViewBase, JSONView):
    orderable_model = Topic


class LessonMoveView(MoveViewBase, JSONView):
    orderable_model = Lesson


class QuestionMoveView(MoveViewBase, JSONView):
    orderable_model = Question


class AJAXError(Exception):

    def __init__(self, *args, **kwargs):
        self.http_response = JsonResponse(*args, **kwargs)
        super(AJAXError, self).__init__()


class BatchProcessView(View):
    __metaclass__ = ABCMeta

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {'error': "Only callable by POST method", }, status=405
        )

    def get_querysets_from_request(self, request):
        try:
            post_dict = parser.parse(request.POST.urlencode())
            refs = post_dict['refs']
            self.refs = refs
        except KeyError:
            raise AJAXError(
                {'error': "No refs found", 'post': request.POST}, status=400
            )
        types = {}

        for i, ref in refs.iteritems():
            try:
                tp = ref['obj']
                pk = ref['pk']
            except KeyError:
                raise AJAXError(
                    {'error': "Badly formed ref: %s" % ref, }, status=400)
            try:
                model_class = ContentType.objects.get(
                    app_label="repo", model=tp).model_class()
            except ContentType.DoesNotExist:
                raise AJAXError(
                    {'error': "Unknown object type: %s" % tp, }, status=400)

            if model_class not in types:
                types[model_class] = []
            types[model_class].append(int(pk))

        for model_class, pks in types.iteritems():
            yield model_class.objects.filter(pk__in=pks)

    def get_refs_from_queryset(self, qs):
        tp = qs.model.__name__.lower()
        for obj in qs:
            yield {'pk': obj.pk, 'obj': tp}

    @abstractmethod
    def process_queryset(self, qs):
        pass

    def post(self, request, *args, **kwargs):
        successes = []
        errors = []
        try:
            for qs in self.get_querysets_from_request(request):
                this_success, this_error = self.process_queryset(qs)
                successes += this_success
                errors += this_error

        except AJAXError, e:
            return e.http_response

        if errors:
            code = 400
        else:
            code = 200
        return JsonResponse(
            {'source': self.refs, 'result': successes,
             'error': errors}, status=code)


class PushView(BatchProcessView):

    def process_queryset(self, qs):
        error = []
        success = []
        for obj in qs:
            try:
                success.append(obj.drupal.push())
            except (RESTError, RESTAuthError), e:
                error.append(str(e))
        return (success, error)


class MarkAsCleanView(BatchProcessView):

    def process_queryset(self, qs):
        refs = self.get_refs_from_queryset(qs)
        try:
            qs.update(dirty="[]")
            return (refs, [])
        except Exception, e:
            return ([], [str(e), ])


class PullView(BatchProcessView):

    def process_queryset(self, qs):
        error = []
        success = []
        for obj in qs:
            try:
                success.append({'pk': obj.pk, 'updated': obj.drupal.pull()})
            except (RESTError, RESTAuthError), e:
                error.append(str(e))
        return (success, error)
