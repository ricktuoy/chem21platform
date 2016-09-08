from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging
import traceback
import os
import re
import json
import hashlib
import mimetypes
import httplib2
import httplib


from apiclient.discovery import build
from apiclient.errors import HttpError as GoogleHttpError
from apiclient.http import MediaIoBaseUpload as GoogleMediaIoBaseUpload


from .models import Lesson
from .models import Module
from .models import Question
from .models import Topic
from .models import UniqueFile
from .models import UniqueFilesofModule
from .models import TextVersion
from .models import Molecule
from .models import CredentialsModel
from .models import Biblio
from .models import LearningTemplate
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from bs4 import BeautifulSoup
from django.core.files.storage import DefaultStorage
from django.core.files.storage import default_storage
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Prefetch
from django.http import Http404, HttpResponseBadRequest, HttpResponseServerError, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.views.generic import ListView
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import IntegrityError
from querystring_parser import parser
from chem21repo.api_clients import RESTError, RESTAuthError, C21RESTRequests
from django.contrib.auth.decorators import login_required
from revproxy.views import ProxyView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from oauth2client.contrib.django_orm import Storage
from oauth2client.client import OAuth2WebServerFlow as Flow
from oauth2client.contrib import xsrfutil
import magic
# Create your views here.


class S3ProxyView(ProxyView):
    upstream = settings.S3_URL

class LearningObjectRelationMixin(object):
    def get_learning_object(self, *args, **kwargs):
        t = kwargs['type']
        tpk = kwargs['tpk']
        self.learning_object_type = t
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
        return inst

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
            defaults={'mol_def':"".join(datalines)})
        if not created:
            mol.mol_def = "".join(datalines)
            mol.save
        if lobj:
            try:
                lobj.molecule = mol
                lobj.save()
            except AttributeError:
                pass
        return JSONFileObjectWrapper(name = name, url=mol.mol_def)



class JSONFileObjectWrapper(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.title = name

class JSONUploadHandle(MediaUploadHandle):
    def process(self, f, lobj=None, **kwargs):
        try:
            parser = QuizParser(f)
        except QuizValidationError, e:
            try:
                parser = GuideToolParser(f)
            except GuideToolValidationError, e:
                raise e
                return super(JSONUploadHandle, self).process(f, lobj=lobj, **kwargs)
        outcome = parser.save()
        if lobj:
            lobj.quiz_name = parser.name
            if isinstance(parser, GuideToolParser):
                try:
                    tpl = LearningTemplate.objects.get(name="guide_detail")
                    lobj.template = tpl
                except LearningTemplate.DoesNotExist:
                    raise AJAXError("No 'guide_detail' template registered")
            lobj.save()
        return JSONFileObjectWrapper(name = "%s: %s" % (parser.human_type_name, parser.name), 
            url = default_storage.url(outcome))


class BibTeXUploadView(JQueryFileHandleView):
    class Fail(Exception):
        pass
    def deleteurl(self):
        return None
    def fileurl(self):
        return None

    def fail(self, message):
        try:
            self.errors.append(message)
        except AttributeError:
            self.errors = [message,]
    def fail_except(self, e):
        self.fail((str(e), traceback.format_exc()))
    def fail_unless(self, test, message="Error."):
        if not test:
            self.fail(message)
            raise self.Fail

    def get_return_values(self):
        return {'name': self.filename,
                #'bibliography': self.bibliography,
                #'raw': self.raw,
                'skipped': self.skipped,
                'created': self.created_bibs, 
                'modified': self.modified_bibs
                }

   
    def process_file(self, f, k, *args, **kwargs):
        from .bibtex import BibTeXParsing

        self._f = f
        self.errors=[]
        self.created_bibs=[]
        self.modified_bibs=[]
        self.skipped=[]
        self.bibliography = []

        raw = BibTeXParsing.get_bib_raw(f)
        self.raw = raw
        bib_source = BibTeXParsing.get_bib_source(raw)
        self.bib_source = bib_source
        bibliography, ref_order = BibTeXParsing.get_bibliography_ordered(bib_source)
        bib_rendered = bibliography.bibliography()

        for k in ref_order:
            entry = bib_source[k]
            bibitem = bib_rendered.pop(0)

            doi, url = BibTeXParsing.get_doi_url(entry)
            html = BibTeXParsing.get_html_from_bibref(unicode(bibitem), url)
            defaults = {'bibkey': k,
                        'inline_html': html,
                        'footnote_html': html}
            if 'title' in entry:
                defaults['title'] = unicode(entry['title'])

            if doi:
                defaults['citekey'] = doi
                crargs = {'DOI': doi, 'defaults': defaults}
            else:
                del defaults['bibkey']
                defaults['citekey'] = k
                crargs = {'bibkey': k, 'defaults': defaults}
            try:
                bib, created = Biblio.objects.get_or_create(**crargs)
            except IntegrityError:
                if doi:
                    try:
                        bib = Biblio.objects.get(bibkey=k)
                        defaults['DOI'] = doi
                        defaults['citekey'] = doi
                        created = False
                    except Biblio.DoesNotExist:
                        bib = Biblio.objects.get(citekey=doi)
                        defaults['DOI'] = doi
                        defaults['bibkey'] = k
                        created = False
                else:
                    try:
                        bib = Biblio.objects.get(citekey=k)
                        defaults['bibkey'] = k
                        created = False
                    except Biblio.DoesNotExist:
                        raise Exception("Unknown integrity error when trying to create biblio")
                #self.skipped.append((repr(bib), created, crargs))
                
            if created:
                self.created_bibs.append(repr(bib)) 
            else:
                #del defaults['citekey']
                for k,v in defaults.iteritems():
                    setattr(bib, k, v)
                bib.unknown = False
                try:
                    bib.save()
                except IntegrityError:
                    self.skipped.append((repr(bib), created, crargs))
                self.modified_bibs.append(repr(bib))







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
        #o['pk'] = self.file_obj.pk
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
            self.errors.append((str(e), str(self.handle), traceback.format_exc()))
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




class MoleculeAttachView(LoginRequiredMixin, LearningObjectRelationMixin, View):
    @staticmethod
    def error_response(e=""):
        return JsonResponse({'error': e}, status=500)
    def post(self, *args, **kwargs):
        mpk = kwargs['mpk']
        inst = self.get_learning_object(*args, **kwargs)
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

class GoogleOAuth2RedirectRequired(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return self.url

class GoogleUploadError(Exception):
    pass

class GoogleServiceMixin(object):
    # Always retry when these exceptions are raised.
    RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
      httplib.IncompleteRead, httplib.ImproperConnectionState,
      httplib.CannotSendRequest, httplib.CannotSendHeader,
      httplib.ResponseNotReady, httplib.BadStatusLine)

    # Always retry when an apiclient.errors.HttpError with one of these status
    # codes is raised.
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
    MAX_RETRIES = 10
    @property
    def flow(self):
        try:
            return self._flow
        except AttributeError:
            pass
        self._flow = Flow(settings.GOOGLE_OAUTH2_KEY, settings.GOOGLE_OAUTH2_SECRET, 
            scope=self.get_google_scope(),
            prompt="consent",
            access_type="offline",
            redirect_uri=self.request.build_absolute_uri(reverse("google-service-oauth2-return")))
        return self._flow

    def get_google_scope(self):
        try:
            return self.request.session["google_service_scope"]
        except KeyError:
            self.request.session["google_service_scope"] = self.google_scope
            return self.google_scope


    @property
    def storage(self):
        try:
            return self._storage
        except AttributeError:
            pass
        self._storage = Storage(CredentialsModel, 'id', self.request.user, 'credential')
        return self._storage

    @property
    def credential(self):
        try:
            return self._credential
        except AttributeError:
            pass
        self._credential = self.storage.get()
        return self._credential

    @property
    def return_path_session_key(self):
        return "google_oauth_return_path"
    

    def get_service(self, request):
        self.request = request
        try:
            return self._service
        except AttributeError:
            pass
        if self.credential is None or self.credential.invalid == True:    
            self.flow.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                       self.request.user)
            self.request.session[self.return_path_session_key] = self.request.path
            authorize_url = self.flow.step1_get_authorize_url()
            raise GoogleOAuth2RedirectRequired(authorize_url)
        else:
            http = httplib2.Http()
            http = self.credential.authorize(http)
            return build(self.google_service_name, self.google_api_version, http=http)

    # This method implements an exponential backoff strategy to resume a
    # failed upload.
    # from https://developers.google.com/youtube/v3/guides/uploading_a_video#Sample_Code
    def resumable_upload(self, insert_request):

      httplib2.RETRIES = 1
      response = None
      error = None
      retry = 0
      while response is None:
        try:
          status, response = insert_request.next_chunk()
          if 'id' in response:
            return response
          else:
            raise GoogleUploadError("The upload failed with an unexpected response: %s" % response)
        except GoogleHttpError, e:
          if e.resp.status in self.RETRIABLE_STATUS_CODES:
            error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                 e.content)
          else:
            raise
        except self.RETRIABLE_EXCEPTIONS, e:
          error = "A retriable error occurred: %s" % e

        if error is not None:
          retry += 1
          if retry > self.MAX_RETRIES:
            raise GoogleUploadError("The upload failed after %d attempts: %s" % (self.MAX_RETRIES, response))

          max_sleep = 2 ** retry
          sleep_seconds = random.random() * max_sleep
          time.sleep(sleep_seconds)

class YouTubeServiceMixin(GoogleServiceMixin):
    google_scope = "https://www.googleapis.com/auth/youtube.upload"
    google_service_name = "youtube"
    google_api_version = "v3"

class DriveServiceMixin(GoogleServiceMixin):
    google_scope = "https://www.googleapis.com/auth/drive.readonly"
    google_service_name = "drive"
    google_api_version = "v3"

class GoogleServiceOAuth2ReturnView(GoogleServiceMixin, View):
    def get(self, request, *args, **kwargs):
        if not xsrfutil.validate_token(settings.SECRET_KEY, str(request.REQUEST['state']),
                                 request.user):
            return  HttpResponseBadRequest("ERROR: XSRF fail. %s %s %s" % (str(request.REQUEST['state']), settings.SECRET_KEY, request.user))
        credential = self.flow.step2_exchange(request.REQUEST)
        storage = Storage(CredentialsModel, 'id', request.user, 'credential')
        storage.put(credential)

        return HttpResponseRedirect(request.session.get(self.return_path_session_key,"/"))

class LoadFromGDocView(LoginRequiredMixin, DriveServiceMixin, LearningObjectRelationMixin, View):

    @staticmethod
    def get_gdoc_html(drive, file_id):
        html = drive.files().export(fileId=file_id, mimeType='text/html').execute()
        soup = BeautifulSoup(html)
        body = soup.body
        # kill all spans
        spans = body.find_all("span")
        for span in spans:
            try:
                style = span['style']
            except KeyError:
                span.unwrap()
                continue    
            weight_match = re.search(r'font-weight:(\d*)', style)
            try:
                weight = int(weight_match.group(1))
            except AttributeError:
                weight = 400
            is_italic = (style.find("italic") != -1)
            is_sub = (style.find("sub") != -1)
            is_super = (style.find("super") != -1)
            styles = []
            if is_sub:
                styles.append("vertical-align:sub")
                styles.append("font-size: 70%;")
            elif is_super:
                styles.append("vertical-align:super")
                styles.append("font-size: 70%;")
            if weight > 400:
                styles.append("font-weight:%d" % weight)
            if is_italic:
                styles.append("font-style:italic")
            if len(styles):
                span['style'] = "; ".join(styles)
            else:
                span.unwrap()

        for el in body.descendants:
            if el.name == "span":
                continue
            try:
                del el['style']
            except (KeyError, TypeError):
                pass
        
        tables = body.find_all("table")
        for table in tables:
            if not table.thead:
                if table.tbody:
                    tbody = table.tbody
                    tr = table.tbody.tr
                    thead = tr.extract()
                else:
                    tbody = soup.new_tag("tbody")
                    tr = table.tr
                    thead = tr.extract()
                    for row in table("tr"):
                        tbody.append(row.extract())
                    table.append(tbody)
                tbody.insert_before(thead)
                for el in thead("td"):
                    el.name = "th"
                thead.wrap(soup.new_tag("thead"))
        html = body.prettify()
        html = re.sub(r"\<body.*?\>","", html)
        return html.replace("</body>","")

    def get(self, request, *args, **kwargs):
        try:
            drive = self.get_service(request)
        except GoogleOAuth2RedirectRequired, e:
            return HttpResponseRedirect(e.url)
        kwargs['type'] = "question"
        ret_uri = request.session.get("return_uri", "/")
        page = self.get_learning_object(*args, **kwargs)
        file_id = kwargs['file_id']
        html = self.get_gdoc_html(drive, file_id)
        page.text = html
        page.save()
        messages.success(request, "Page text successfully replaced.")
        return HttpResponseRedirect(ret_uri)

class PushVideoToYouTubeView(LoginRequiredMixin, 
                         YouTubeServiceMixin, 
                         LearningObjectRelationMixin, 
                         View):
    @staticmethod
    def error_response(e=""):
        return JsonResponse({'error': e}, status=500)
   
    # from https://developers.google.com/youtube/v3/guides/uploading_a_video#Sample_Code
    def initialize_upload(self, youtube, fh, **options):

      try:
        tags = options['keywords'].split(",")
      except KeyError:
        try:
            tags = options['tags']
        except KeyError:
            tags = None

      body=dict(
        snippet=dict(
          title=options['title'],
          description=options['description'],
          tags=tags,
          categoryId=options['categoryId']
        ),
        status=dict(
          privacyStatus=options['privacyStatus']
        )
      )

      # Call the API's videos.insert method to create and upload the video.
      insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=GoogleMediaIoBaseUpload(fh, mimetype=options['mimetype'], chunksize=-1, resumable=True)
      )

      response = self.resumable_upload(insert_request)
      return response



    def get(self, request, *args, **kwargs):
        try:
            youtube = self.get_service(request)
        except GoogleOAuth2RedirectRequired, e:
            return HttpResponseRedirect(e.url)
        ret_uri = request.session.get("return_uri", "/")
        vpk = kwargs['vpk']
        lobj = self.get_learning_object(*args, **kwargs)
        try:
            fileinst = UniqueFile.objects.get(pk=vpk)
        except UniqueFile.DoesNotExist:
            return self.error_response("Unique file with id %d not found" % vpk)
        if fileinst.type != "video":
            return self.error_response("File %s is not a video" % fileinst.name )
        if fileinst.youtube_id:
            return self.error_response("File %s has already been uploaded to YouTube (ID: %s)" % (fileinst.name, fileinst))
        # we have a video to upload.
        # see See https://developers.google.com/youtube/v3/docs/videoCategories/list for possible categoryId

        try:
            tags = [mod.title for mod in lobj.modules.all()]
        except AttributeError:
            tags = [mod.title for mod in lobj.modules]
        with DefaultStorage().open(fileinst.get_file_relative_url()) as fh:
            try:
                desc = BeautifulSoup(lobj.text).get_text()
            except:
                desc = ""
            try:
                response = self.initialize_upload(youtube, fh,
                    title = lobj.title,
                    description = desc, # strip HTML tags nicely
                    mimetype = fileinst.get_mime_type(),
                    tags = tags,
                    categoryId = 27, # =="Education"
                    privacyStatus = "unlisted", # alternatively "public", "private"
                    )
            except GoogleUploadError, e:
                messages.error(request, str(e))
                return HttpResponseRedirect(ret_uri)
        messages.success(request, "Video successfully uploaded: %s" % response['id'])
        fileinst.youtube_id = response['id']
        fileinst.save()
        return HttpResponseRedirect(ret_uri)


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

class JSONObjectValidationError(Exception):
    pass

class QuizValidationError(JSONObjectValidationError):
    pass

class GuideToolValidationError(JSONObjectValidationError):
    pass

class JSONObjectParser(object):
    def __init__(self, f):
        f.seek(0)
        dat = f.read()
        self.data = json.loads(dat)
        self.validate()

    def validate(self):
        data = self.data
        try:
            t = data[self.type_name]
        except KeyError:
            return self.error_response("Not a %s" % self.human_type_name)

        try:
            self.name = data['id']
        except KeyError:
            return self.error_response("%s object has no id" % self.human_type_name)
        return t
    

class QuizParser(JSONObjectParser):
    type_name = "quiz_object"
    human_type_name = "quiz"
    def error_response(self, text):
        raise QuizValidationError(text)

    def validate(self):
        t = super(QuizParser, self).validate()

        if t != "questions_answers":
            return self.error_response(
                "Not questions and answers; cannot import")
        return t

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

class GuideToolParser(JSONObjectParser):
    type_name = "guide_tool_object"
    human_type_name = "Guide tool"

    def error_response(self, text):
        raise GuideToolValidationError(text)

    def save(self):
        data = self.data
        dest = "guides/%s.json" % self.name
        out_data = []
        k_set = set(['id','type','text','help_text','responses'])
        for el in data['data']:
            row = dict([(k, el[k]) for k in k_set if k in el])
            out_data.append(row)
        out = data.copy()
        out['data'] = out_data
        f = ContentFile(json.dumps(out))
        default_storage.save(dest, f)

        return dest 

class ImportJSONObjectError(Exception):
    pass

class ImportJSONObjectView(CSRFExemptMixin, JSONView):
    
    def populate_post_dict(self):
        try:
            return self._post_dict
        except AttributeError:
            self._post_dict = parser.parse(self.request.POST.urlencode())
            return self._post_dict

    def error_response(self, error=""):
        return JsonResponse({'error': error}, status=500)



    def success_response(self, outcome):
        return JsonResponse({'success': 'Saved to %s' % 
            default_storage.url(outcome)})

    def get_learning_object(self, kwargs):
        try:
            self.model = ContentType.objects.get(
                app_label="repo",
                model=kwargs['object_name']).model_class()
        except ContentType.DoesNotExist:
            raise ImportJSONObjectError("Unknown learning object type")

        try:
            self.attach_to = model.objects.get(pk=kwargs['id'])
        except model.DoesNotExist:
            raise ImportJSONObjectError("Cannot find learning object")
        return self.attach_to

    def amend_learning_object(self, lobj, parse):
        lobj.save()

    def post(self, request, *args, **kwargs):
        self.request = request
        self.errors = []

        data = self.get_json_data()
        self.populate_post_dict()

        try:
            attach_to = self.get_learning_object()
        except ImportJSONObjectError, e:
            return self.error_response(e.message)

        try:
            parsed = self.parser(self.request.body)
        except JSONObjectValidationError, e:
            return self.error_response(e.message)
        self.amend_learning_object(attach_to, parsed)
        save_outcome = parsed.save()
        return self.success_response(save_outcome)

class ImportQuizView(ImportJSONObjectView):
    parser = QuizParser

    def amend_learning_object(self, lobj, parse):
        lobj.quiz_name = parse.name
        super(ImportQuizView, self).amend_learning_object(lobj, parse)

    def success_response(self, outcome):
        dest_questions, dest_answers = outcome
        return JsonResponse(
            {'success': 'Saved to %s, %s' % (
                default_storage.url(dest_questions),
                default_storage.url(dest_answers))},
            status=200)

class ImportGuideToolView(ImportJSONObjectView):
    parser = GuideToolParser



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
