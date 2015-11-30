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


class PushView(View):

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {'error': "Only callable by POST method", }, status=405
        )

    def post(self, request, *args, **kwargs):
        try:
            post_dict = parser.parse(request.POST.urlencode())
            refs = post_dict['refs']
        except KeyError:
            return JsonResponse(
                {'error': "No refs found", 'post': request.POST}, status=400
            )
        types = {}
        success = []
        error = []
        for i, ref in refs.iteritems():
            try:
                tp = ref['obj']
                pk = ref['pk']
            except KeyError:
                return JsonResponse(
                    {'error': "Badly formed ref: %s" % ref, }, status=400)
            try:
                model_class = ContentType.objects.get(
                    app_label="repo", model=tp).model_class()
            except ContentType.DoesNotExist:
                return JsonResponse(
                    {'error': "Unknown object type: %s" % tp, }, status=400)

            if model_class not in types:
                types[model_class] = []
            types[model_class].append(int(pk))

        
        for model_class, pks in types.iteritems():
            objs = model_class.objects.filter(pk__in=pks)
            success.append(str(model_class))
            """
            try:
                success.append(model_class.objects.push(objs))
                continue
            except AttributeError:
                pass
            except (RESTError, RESTAuthError), e:
                error.append(str(e))
                continue
            """
            success.append([obj.drupal.node for obj in objs])

            for obj in objs:
                try:
                    success.append(obj.drupal.node)
                    success.append(obj.drupal.push())
                except (RESTError, RESTAuthError), e:
                    error.append(str(e))
        if error:
            code = 400
        else:
            code = 200
        return JsonResponse(
            {'source': refs, 'result': success, 'error': error}, status=code)
