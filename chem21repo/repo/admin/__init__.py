from ..models import *
from ..views import BibTeXUploadView, LoadFromGDocView
from django.contrib import admin
from factories import create_admin, create_power_admin

from django.http import HttpResponseRedirect
from django.shortcuts import render
from ..shortcodes import HTMLShortcodeParser
from ..shortcodes.errors import BlockNotFoundError

create_admin(
    model=Module,
    fields=['name', 'code', 'text'],
    hidden_fields=['topic', ],
)


class BiblioAdmin(admin.ModelAdmin):
    def get_urls(self):
        from django.conf.urls import url
        urls = super(BiblioAdmin, self).get_urls()
        my_urls = [
            url(r'^biblio/import_references[/]?$',
                self.admin_site.admin_view(BibTeXUploadView.as_view()),
                name='repo_biblio_importreferences'
                ),
        ]
        return my_urls + urls

    class Media:
        js = [
            '/s3/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js',
            '/s3/js/tinymce_setup.js',
        ]


create_admin(
    model=Biblio,
    fields=['title', 'citekey'],
    base_admin=BiblioAdmin
)

create_admin(
    model=Topic,
    fields=['name', 'text', 'icon']
)

create_admin(
    model=Lesson,
    hidden_fields=['modules', ],
    fields=["title", "text"])

create_admin(
    model=UniqueFile,
    fields=["title", "type", "youtube_id", "remote_path",
            'authors', 'description'])

create_admin(
    model=GlossaryTerm,
    fields=["name", "description"])


class PresentationActionAdmin(admin.ModelAdmin):
    raw_id_fields = ('biblio',)
    autocomplete_lookup_fields = {
        'fk': ['biblio'],
    }

    class Media:
        js = [
            '/s3/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js',
            '/s3/js/tinymce_setup.js',
        ]


create_admin(
    model=PresentationAction,
    hidden_fields=['presentation', ],
    fields=["start", "end", "action_type", "biblio", "image", "text", ],
    base_admin=PresentationActionAdmin)


class QuestionAdmin(admin.ModelAdmin):
    def get_urls(self):
        from django.conf.urls import url
        urls = super(QuestionAdmin, self).get_urls()
        my_urls = [
            url(r'^add_figure/([0-9]+)/([0-9]+)/([0-9]+)$',
                self.admin_site.admin_view(self.add_figure),
                name='add_figure'
                ),
            url(r'^edit_figure/([0-9]+)/([0-9]+)/([0-9]+)$',
                self.admin_site.admin_view(self.add_figure),
                name='edit_figure'
                ),
            url(r'^remove_figure/([0-9]+)/([0-9]+)/([0-9]+)$',
                self.admin_site.admin_view(self.remove_figure),
                name='remove_figure'
                ),
            url(r'^load_gdoc/(?P<tpk>[0-9]+)/(?P<file_id>.*)[/]?$',
                self.admin_site.admin_view(LoadFromGDocView.as_view()),
                name='repo_question_loadgdoc'
                ),
        ]
        return my_urls + urls

    def _redirect(self, request):
        url = request.session.get('admin_return_uri', "/")
        return HttpResponseRedirect(url)

    def get_shortcode_form(self, request, shortcode, question):
        if request.method == "POST":
            shortcode.update(**request.POST)
        return shortcode.get_form(question)


    def edit_figure(self, request, qpk, block_id):
        context = {}
        try:
            question = Question.objects.get(pk=qpk)
        except Question.DoesNotExist:
            raise Http404("Question does not exist")
        parser = HTMLShortcodeParser(question.text)
        renderers = parser.get_renderers(block_id)
        renderer = renderers[0]
        form = self.get_shortcode_form(request, renderer, question)
        if request.method == POST and form.is_valid():
            shortcode.update(**form.cleaned_data)
            new_html = parser.replace_shortcode(block_id, renderer)
            question.text = new_html
            question.save()
            return self._redirect(request)
        context['form'] = form
        context['token_type'] = token_type
        context['token'] = token
        context['title'] = "Edit figure"
        return render(request, "admin/question_token_form.html", context)

    def add_figure(self, request, qpk, block_id):
        context = {}
        try:
            question = Question.objects.get(pk=qpk)
        except Question.DoesNotExist:
            raise Http404("Question does not exist")
        renderer = FigureRenderer()
        form = self.get_shortcode_form(request, renderer, question)
        if request.method == POST and form.is_valid():
            parser = HTMLShortcodeParser(question.text)
            new_html = parser.insert_shortcode(block_id, renderer)
            question.text = new_html
            question.save()
            return self._redirect(request)
        context['form'] = form
        context['token_type'] = 'figure'
        context['token'] = token
        context['title'] = "Insert figure"
        return render(request, "admin/question_token_form.html", context)

    def remove_figure(self, request, qpk, para, figure):
        try:
            question = Question.objects.get(pk=qpk)
        except Question.DoesNotExist:
            raise Http404("Question does not exist")
        parser = HTMLShortcodeParser(question.text)
        try:
            html = parser.remove_shortcode(block_id)
        except BlockNotFoundError:
            pass
        question.text = html
        question.save()
        return self._redirect(request)

    class Media:
        js = [
            '/s3/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js',
            '/s3/js/tinymce_setup.js',
        ]


create_admin(
    model=Question,
    hidden_fields=['lessons', ],
    fields=["title", 'text', 'byline'],
    base_admin=QuestionAdmin)

for md in [Question, UniqueFile, Author,
           LearningTemplate, Molecule,
           Lesson, Module, Topic,
           UniqueFilesofModule, CredentialsModel, Biblio]:
    create_power_admin(md)