import logging
import traceback
import os
import json
import hashlib
import mimetypes

from .models import Lesson
from .models import Module
from .models import Question
from .models import Topic
from .models import UniqueFile
from .models import UniqueFilesofModule
from .models import TextVersion
from .models import Molecule
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from django.core.files.storage import default_storage
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Prefetch
from django.http import Http404, HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.views.generic import ListView
from django.conf import settings
from querystring_parser import parser
from chem21repo.api_clients import RESTError, RESTAuthError, C21RESTRequests
from django.contrib.auth.decorators import login_required
from revproxy.views import ProxyView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import magic
# Create your views here.


class S3ProxyView(ProxyView):
    upstream = settings.S3_URL


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        if os.environ.get("DJANGO_DEVELOPMENT", False):
            return view
        return login_required(view)


class CSRFExemptMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(CSRFExemptMixin, cls).as_view(**initkwargs)
        return csrf_exempt(view)


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


class HomePageView(LoginRequiredMixin, TemplateView):
    template_name = "repo/full_listing.html"

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        context['files'] = UniqueFile.objects.filter(type="video")
        topics = Topic.objects.all().prefetch_related(
            "modules",
            Prefetch("modules__text_versions",
                     queryset=TextVersion.objects.all().order_by(
                         "-modified_time"),
                     to_attr="text_versions"),
            Prefetch("modules__text_versions",
                     queryset=TextVersion.objects.filter(
                         user__is_superuser=False).order_by("-modified_time"),
                     to_attr="editor_text_versions"),
            Prefetch("modules__uniquefilesofmodule_set",
                     queryset=UniqueFilesofModule.objects.filter(
                         file__active=True,
                         file__type__in=["video", "image", "application"],
                         file__cut_of__isnull=True).order_by('file__type'),
                     to_attr="ordered_videos"),
            Prefetch("modules__ordered_videos__file__cuts",
                     queryset=UniqueFile.objects.filter(
                         type="video").order_by('cut_order')),
            Prefetch("modules__lessons",
                     queryset=Lesson.objects.all().order_by('order'),
                     to_attr="ordered_lessons"),
            Prefetch("modules__ordered_lessons__text_versions",
                     queryset=TextVersion.objects.all().order_by(
                         "-modified_time")),
            Prefetch("modules__ordered_lessons__text_versions",
                     queryset=TextVersion.objects.filter(
                         user__is_superuser=False).order_by(
                         "-modified_time"),
                     to_attr="editor_text_versions"),
            Prefetch("modules__ordered_lessons__questions",
                     queryset=Question.objects.all().order_by(
                         'order'),
                     to_attr="ordered_questions"),
            Prefetch("modules__ordered_lessons__ordered_questions__files",
                     queryset=UniqueFile.objects.all().order_by('type'),
                     to_attr="ordered_files"),
            Prefetch("modules__ordered_lessons__ordered_questions__text_versions",
                     queryset=TextVersion.objects.all().order_by(
                         "-modified_time")),
            Prefetch("modules__ordered_lessons__ordered_questions__text_versions",
                     queryset=TextVersion.objects.filter(
                         user__is_superuser=False).order_by(
                         "-modified_time"),
                     to_attr="editor_text_versions"),
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
        return context


class VideoView(LoginRequiredMixin, DetailView):
    model = UniqueFile
    template_name = "repo/video_detail.html"
    slug_field = "checksum"
    slug_url_kwarg = "checksum"


class TextVersionView(LoginRequiredMixin, DetailView):
    model = TextVersion
    template_name = "repo/textversion_detail.html"

    def get_context_data(self, *args, **kwargs):
        context = super(TextVersionView, self).get_context_data(
            *args, **kwargs)
        instance = context['object']
        return context


class DirtyView(LoginRequiredMixin, JSONView):

    def get_context_data(self, **kwargs):
        if(kwargs['object_name'] == "file"):
            model = UniqueFile
        else:
            model = ContentType.objects.get(
                app_label="repo",
                model=kwargs['object_name']).model_class()
        obj = model.objects.get(pk=kwargs['id'])
        return obj.drupal.generate_node_from_parent(debug=True)


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

        parent_id = kwargs.get('parent_id', None)
        if "to_id" not in kwargs or kwargs['to_id'] == "0":
            # no dest id or dest id==0 then move element to top
            context['new_order'] = 1
            context['success'], context[
                'message'] = self.orderable_manager.move_to_top(
                    from_el, parent_id)
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
            'message'] = self.orderable_manager.move(from_el, to_el, parent_id)
        return context


class SourceFileMoveView(LoginRequiredMixin, MoveViewBase, JSONView):
    orderable_model = UniqueFilesofModule


class CutFileMoveView(LoginRequiredMixin, MoveViewBase, JSONView):
    orderable_model = UniqueFile
    orderable_manager = UniqueFile.cut_objects


class ModuleMoveView(LoginRequiredMixin, MoveViewBase, JSONView):
    orderable_model = Module


class TopicMoveView(LoginRequiredMixin, MoveViewBase, JSONView):
    orderable_model = Topic


class LessonMoveView(LoginRequiredMixin, MoveViewBase, JSONView):
    orderable_model = Lesson


class QuestionMoveView(LoginRequiredMixin, MoveViewBase, JSONView):
    orderable_model = Question


class RemoveViewBase:
    __metaclass__ = ABCMeta

    @abstractproperty
    def m2m_field(self):
        return None

    @abstractproperty
    def model(self):
        return None

    @abstractproperty
    def parent_model(self):
        return None

    @property
    def manager(self):
        return self.model.objects

    @property
    def parent_manager(self):
        return self.parent_model.objects

    @property
    def model_name(self):
        return self.model._meta.verbose_name.title().lower()

    def get_context_data(self, *args, **kwargs):
        try:
            child = self.manager.get(pk=kwargs['id'])
        except self.model.DoesNotExist, e:
            self.error = (e, 404)
            return {}
        try:
            parent = self.parent_manager.get(pk=kwargs['parent_id'])
        except self.parent_model.DoesNotExist, e:
            self.error = (e, 404)
            return {}
        try:
            m2m_manager = getattr(parent, self.m2m_field)
        except AttributeError, e:
            self.error = e
            return {}
        try:
            m2m_manager.remove(child)
        except Exception, e:
            self.error = e
        self._child = child
        return {'success':
                {'obj': self.model_name,
                 'pk': child.pk}}


class DeleteViewBase(LoginRequiredMixin, RemoveViewBase):
    __metaclass__ = ABCMeta

    def get_context_data(self, *args, **kwargs):
        ret = super(DeleteViewBase, self).get_context_data(*args, **kwargs)
        try:
            self._child.delete()
        except Exception, e:
            self.error = e
            return {}
        return ret


class QuestionRemoveView(RemoveViewBase, JSONView):
    m2m_field = "questions"
    model = Question
    parent_model = Lesson


class FileRemoveView(RemoveViewBase, JSONView):
    m2m_field = "files"
    model = UniqueFile
    model_name = "file"
    parent_model = Question


class FileDeleteView(DeleteViewBase, JSONView):
    m2m_field = "files"
    model = UniqueFile
    model_name = "file"
    parent_model = Question


class LessonRemoveView(RemoveViewBase, JSONView):
    m2m_field = "lessons"
    model = Lesson
    parent_model = Module


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

    def get_querysets_from_refs(self, refs):
        types = {}

        for ref in refs:
            try:
                tp = ref['obj']
                pk = ref['pk']
            except KeyError:
                raise AJAXError(
                    {'error': "Badly formed ref: %s" % ref, }, status=400)
            if tp == "file":
                tp = "uniquefile"
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

    def get_querysets_from_request(self, request):
        try:
            post_dict = parser.parse(request.POST.urlencode())
            refs = post_dict['refs']
            self.refs = [ref for i, ref in refs.iteritems()]
        except KeyError:
            raise AJAXError(
                {'error': "No refs found", 'post': request.POST}, status=400
            )

        return self.get_querysets_from_refs(self.refs)

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
                this_success, this_error = self.process_queryset(
                    qs)
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


class AttachUniqueFileView(CSRFExemptMixin, View):

    def get_post_dict_from_request(self, request):
        try:
            return self._post_dict
        except AttributeError:
            self._post_dict = parser.parse(request.POST.urlencode())
            return self._post_dict

    def get_module_from_request(self, request):
        kwargs = self.get_post_dict_from_request(request)
        return Module.objects.get(code=kwargs['module'])

    def get_uniquefiles_from_request(self, request):
        kwargs = self.get_post_dict_from_request(request)
        for fd in json.loads(kwargs['files']):
            defaults = {'ext': fd['ext'],
                        'type': fd['type'],
                        'title': fd['title']}
            fo, created = UniqueFile.objects.get_or_create(
                checksum=fd['checksum'], defaults=defaults)
            if not created:
                fo.ext = fd['ext']
                fo.type = fd['type']
                fo.title = fd['title']
                fo.save()
            yield fo

    def post(self, request, *args, **kwargs):
        mod = self.get_module_from_request(request)
        for f in self.get_uniquefiles_from_request(request):
            ufm, created = UniqueFilesofModule.objects.get_or_create(
                module=mod, file=f)
        return JsonResponse(
            {'module': mod.title, }, status=200)


class JQueryFileHandleView(LoginRequiredMixin, View):
    __metaclass__ = ABCMeta

    errors = []

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {'error': "Only callable by POST method", }, status=405
        )

    @property
    def filename(self):
        return self._f.name

    @property
    def filesize(self):
        return self._f.size

    @abstractproperty
    def fileurl(self):
        return None

    @abstractproperty
    def deleteurl(self):
        return None

    @property
    def deletetype(self):
        return "DELETE"

    def get_return_values(self):
        return {'name': self.filename,
                'size': self.filesize,
                'url': self.fileurl,
                'delete_url': self.deleteurl,
                'delete_type': self.deletetype}

    @abstractmethod
    def process_file(self, f, **kwargs):
        return None

    def post(self, request, *args, **kwargs):
        if request.FILES is None:
            return JsonResponse(
                {'error': "No files uploaded.", }, status=405
            )
        ret = []
        # getting file data for farther manipulations
        for k, f in request.FILES.iteritems():
            self.process_file(f, k, *args, **kwargs)
            ret.append(self.get_return_values())
        if self.errors:
            return JsonResponse({'error': self.errors}, status=400)
        else:
            return JsonResponse(
                ret, status=200, safe=False)


class MediaUploadHandle(object):

     
    def process(self, f, lobj=None, **kwargs):
        m = hashlib.md5()
        
        for ch in f.chunks():
            m.update(ch)
        
        checksum = m.hexdigest()
        name = f.name
        title, ext = os.path.splitext(name)
        tpe, encoding = mimetypes.guess_type(name)
        tpe, enc = tpe.split("/")

        dest_path = "sources/" + checksum + ext
        default_storage.save(dest_path, f)

        defaults = {'ext': ext,
            'type': tpe,
            'title': title}
        
        fo, created = UniqueFile.objects.get_or_create(
            checksum=checksum, defaults=defaults)
        
        if not created:
            fo.ext = ext
            fo.type = tpe
            fo.title = title
            fo.save()

        if lobj:
            try:
                lobj.files.add(fo)
            except AttributeError:
                pass

        return fo

class MolUploadHandle(object):
    def process(self, f, lobj=None, **kwargs):
        datalines = list(f)
        name = datalines[0]
        root, ext = os.path.splitext(name)
        if root != name:
            name = root
        mol, created = Molecule.objects.get_or_create(
            name=name, 
            defaults={'mol_def':"\n".join(datalines)})
        if not created:
            mol.mol_data = "\n".join(datalines)
            mol.save
        if lobj:
            try:
                lobj.molecule = mol
                lobj.save()
            except AttributeError:
                pass
        return JSONFileObjectWrapper(name = name, url=None)

class JSONFileObjectWrapper(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.title = name

class JSONUploadHandle(MediaUploadHandle):
    def process(self, f, lobj=None, **kwargs):
        try:
            qparse = QuizParser(f)
        except QuizValidationError, e:    
            return super(JSONUploadHandle, self).process(f, lobj=lobj, **kwargs)
        dest_questions, dest_answers = qparse.save()
        if lobj:
            lobj.quiz_name = qparse.name
            lobj.save()
        return JSONFileObjectWrapper(name = "Quiz questions: %s" % qparse.name, url = default_storage.url(dest_questions))


class MediaUploadView(JQueryFileHandleView):

    content_type_handle_map = {
        'text/mol': MolUploadHandle,
        'application/mol': MolUploadHandle,
        'text/json': JSONUploadHandle
    }

    default_handle = MediaUploadHandle

    def get_return_values(self):
        ret = super(MediaUploadView, self).get_return_values()
        ret['urlkwargs'] = self.urlkwargs
        return ret

    @property
    def filename(self):
        return self.file_obj.title

    @property
    def filesize(self):
        return self.file.size

    def get_return_values(self):
        o = super(MediaUploadView,self).get_return_values()
        o['content_type'] = self.content_type
        o['handler'] = unicode(self.handle_cls)
        return o

    def get_post_dict_from_request(self, request):
        try:
            return self._post_dict
        except AttributeError:
            self._post_dict = parser.parse(request.POST.urlencode())
            return self._post_dict
    
    def post(self, request, *args, **kwargs):
        self.urlkwargs = kwargs
        kwargs.update(self.get_post_dict_from_request(request))

        return super(MediaUploadView, self).post(request, *args, **kwargs)
            
    @property
    def learning_object(self,**kwargs):
        try:
            return self._learning_object
        except AttributeError:
            pass

        self._learning_object = None
        try:
            model = ContentType.objects.get(
                app_label="repo",
                model=self.urlkwargs['type']).model_class()
            try:
                self._learning_object = model.objects.get(pk=self.urlkwargs['pk'])
            except model.DoesNotExist:
                pass
        except (KeyError, ContentType.DoesNotExist):
            pass
        return self._learning_object

    @property
    def fileurl(self):
        return self.file_obj.url

    @property
    def deleteurl(self):
        return None

    def process_file(self, f, k, *args, **kwargs):
        self.errors = []
        self.file = f
        ct = f.content_type
        # Extra file type sniffing
        if ct == "application/octet-stream":
            ct = magic.from_buffer(f.read(1024), mime=True)
            f.seek(0)
            if ct =="text/plain":
                try:
                    js = json.loads(f.read())
                    f.seek(0)
                    ct = "text/json"
                except ValueError, e:
                    try:
                        lf = list(f)
                        f.seek(0)
                        counts_line = lf[3].split()
                        version = counts_line.pop()
                        if version in ("V2000", "V3000"):
                            ct = "text/mol"
                        else:
                            ct = "text/plain"
                    except IndexError, AttributeError:
                        ct = "text/plain"
        self.content_type = ct
        self.handle_cls = self.content_type_handle_map.get(ct, self.default_handle)
        self.handle = self.handle_cls()
        try:
            fo = self.handle.process(f, lobj=self.learning_object, **kwargs)
        except Exception as e:
            self.errors.append(str(e))
            self.file_obj = JSONFileObjectWrapper(name = "", url ="" )
            return
        self.file_obj = fo

class EndnoteUploadView(JQueryFileHandleView):

    def process_file(self):
        self.errors = []
        reqs = C21RESTRequests()
        self._result = reqs.import_endnote(self._file.read())

    @property
    def fileurl(self):
        return self._result

    @property
    def deleteurl(self):
        return ""


class EndnoteSearchView(LoginRequiredMixin, JSONView):
    def get_context_data(self, **kwargs):
        return C21RESTRequests().search_endnote(kwargs['term'])

    def render_to_response(self, *args, **kwargs):
        kwargs['safe'] = False
        return super(EndnoteSearchView, self).render_to_response(
            *args, **kwargs)


class FiguresGetView(LoginRequiredMixin, JSONView):
    def get_context_data(self, **kwargs):
        model = ContentType.objects.get(
            app_label="repo",
            model=kwargs['type']).model_class()
        try:
            obj = model.objects.get(pk=kwargs['pk'])
            return dict([(f.pk, f.title) for f in obj.files.all()])
        except model.DoesNotExist:
            return {}

    def render_to_response(self, *args, **kwargs):
        kwargs['safe'] = False
        return super(FiguresGetView, self).render_to_response(
            *args, **kwargs)

class MoleculeListView(LoginRequiredMixin, JSONView):
    safe = False
    def get_context_data(self, **kwargs):
        return [{'pk':m.pk, 'name':unicode(m), 'mol':m.mol_def} for m in Molecule.objects.all()]

class MoleculeAttachView(LoginRequiredMixin, View):
    @staticmethod
    def error_response(e=""):
        return JsonResponse({'error': e}, status=500)
    def post(self, *args, **kwargs):
        t = kwargs['type']
        tpk = kwargs['tpk']
        mpk = kwargs['mpk']
        try:
            model = ContentType.objects.get(
                app_label="repo",
                model=t).model_class()
        except ContentType.DoesNotExist:
            return self.error_response("Learning object of type %s not found" % t)
        try:
            inst = model.objects.get(pk=tpk)
        except model.DoesNotExist:
            return self.error_response("Object %s with id %d not found" % (t, tpk))
        try:
            molinst = Molecule.objects.get(pk=mpk)
        except Molecule.DoesNotExist:
            return self.error_response("Object %s with id %d not found" % (t, mpk))
        try:
            inst.molecule = molinst
            inst.save()
        except AttributeError:
            return self.error_response("Molecule cannot be attached to %s %s" % (t, unicode(inst)))
        return JsonResponse({'success': True}, status=200)



class FileLinkGetView(LoginRequiredMixin, JSONView):
    def get_context_data(self, **kwargs):
        model = ContentType.objects.get(
            app_label="repo",
            model=kwargs['type']).model_class()
        try:
            obj = model.objects.get(pk=kwargs['pk'])
            return dict([(f.url, f.title) for f in obj.files.all()])
        except model.DoesNotExist:
            return {}

    def render_to_response(self, *args, **kwargs):
        kwargs['safe'] = False
        return super(FileLinkGetView, self).render_to_response(
            *args, **kwargs)


class StructureGetView(LoginRequiredMixin, JSONView):

    def obj_to_dict(self, obj):
        d = {'pk': obj.pk, 'name': obj.title}
        if isinstance(obj, Question):
            return d
        d['children'] = [self.obj_to_dict(ch) for ch in obj.ordered_children]
        return d

    def get_context_data(self, **kwargs):
        struct = Topic.objects.prefetch_related(
            Prefetch("modules",
                     queryset=Module.objects.all().order_by('order'),
                     to_attr="ordered_children"),
            Prefetch("ordered_children__lessons",
                     queryset=Lesson.objects.all().order_by('order'),
                     to_attr="ordered_children"),
            Prefetch("ordered_children__ordered_children__questions",
                     queryset=Question.objects.exclude(dummy=True).order_by(
                         'order'),
                     to_attr="ordered_children"))
        return [self.obj_to_dict(ch) for ch in struct]

    def render_to_response(self, *args, **kwargs):
        kwargs['safe'] = False
        return super(StructureGetView, self).render_to_response(
            *args, **kwargs)


class PushView(BatchProcessView):
    def process_queryset(self, qs):
        error = []
        success = []
        for obj in qs:
            try:
                success.append(obj.drupal.push())
                obj.text_versions.all().update()
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


class StripRemoteIdView(BatchProcessView):
    def process_queryset(self, qs):
        error = []
        success = []
        for obj in qs:
            try:
                success.append(
                    {'pk': obj.pk, 'updated': obj.title + str(
                        obj.drupal.strip_remote_id())})
            except (RESTError, RESTAuthError), e:
                error.append(str(e))
        return (success, error)

class QuizValidationError(Exception):
    pass

class QuizParser(object):

    def __init__(self, bstring):
        try:
            self.data = json.load(bstring)
        except Exception as e:
            return self.error_response("%s" % (str(e)))
            self.data = json.loads(bstring)
        self.validate()

    def error_response(self, text):
        raise QuizValidationError(text)

    def validate(self):
        data = self.data

        try:
            t = data['quiz_object']
        except KeyError:
            return self.error_response("Not a quiz_object")

        if t != "questions_answers":
            return self.error_response(
                "Not questions and answers; cannot import")

        try:
            self.name = data['id']
        except KeyError:
            return self.error_response("Quiz object has no id")



        return True

    def save(self):

        data = self.data

        dest_questions = "quiz/%s_questions.json" % self.name
        dest_answers = "quiz/%s_answers.json" % self.name

        question_data = [
            {'id': el['id'],
             'type': el['type'],
             'text': el['text'],
             'responses': el['responses']}
            for el in data['data']]
        answer_data = [
            {'id': el['id'],
             'correct': el['correct'],
             'discussion': el.get('discussion', "")}
            for el in data['data']]

        questions = data.copy()
        questions['data'] = question_data
        questions['quiz_object'] = "questions"

        answers = data.copy()
        answers['data'] = answer_data
        answers['quiz_object'] = "answers"

        f = ContentFile(json.dumps(questions))
        default_storage.save(dest_questions, f)

        f = ContentFile(json.dumps(answers))
        default_storage.save(dest_answers, f)

        return (dest_questions, dest_answers)


class ImportQuizView(CSRFExemptMixin, JSONView):

    def populate_post_dict(self):
        try:
            return self._post_dict
        except AttributeError:
            self._post_dict = parser.parse(self.request.POST.urlencode())
            return self._post_dict

    def error_response(self, error=""):
        return JsonResponse({'error': error}, status=500)

    def post(self, request, *args, **kwargs):
        self.request = request
        self.errors = []

        data = self.get_json_data()
        self.populate_post_dict()

        try:
            qparse = QuizParser(self.request.body)
        except QuizValidationError, e:
            return self.error_response(e.message)

        try:
            self.model = ContentType.objects.get(
                app_label="repo",
                model=kwargs['object_name']).model_class()
        except ContentType.DoesNotExist:
            return self.error_response("Unknown learning object type")

        try:
            self.attach_to = model.objects.get(pk=kwargs['id'])
        except model.DoesNotExist:
            return self.error_response("Cannot find learning object")

        dest_questions, dest_answers = qparse.save()

        attach_to.quiz_name = qparse.name
        attach_to.save()

        return JsonResponse(
            {'success': 'Saved to %s, %s' % (
                default_storage.url(dest_questions),
                default_storage.url(dest_answers))},
            status=200)




class AddFileView(BatchProcessView):

    def post(self, request, *args, **kwargs):
        if kwargs['target_type'] != "question":
            return JsonResponse(
                {'error': "Target should be a question.", }, status=405
            )
        refs = [{'pk': kwargs['target_id'], 'obj': kwargs['target_type']}, ]
        target_qs = list(self.get_querysets_from_refs(refs))
        target_qs = target_qs[0]
        target = list(target_qs[:1])
        if not target[0]:
            return JsonResponse(
                {'error': "Target not found.", }, status=405
            )
        self.add_file_target = target[0]
        return super(AddFileView, self).post(request, *args, **kwargs)

    def process_queryset(self, qs):

        success = []
        error = []
        for obj in qs:
            try:
                self.add_file_target.files.add(obj)
                success.append({'pk': obj.pk})
            except Exception, e:
                error.append(str(e))
                error.append(traceback.format_exc())
        return (success, error)

    def get_querysets_from_refs(self, refs):
        def convert_ref(ref):
            if ref['obj'] == 'cut_file' or ref['obj'] == 'source_file':
                obj = 'uniquefile'
            else:
                obj = ref['obj']
            return {'obj': obj, 'pk': ref['pk']}

        return super(AddFileView, self).get_querysets_from_refs(
            map(convert_ref, refs))
