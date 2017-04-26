from ..models import *
from ..views import BibTeXUploadView, LoadFromGDocView
from django.contrib import admin
from factories import create_admin, create_power_admin

from django.http import HttpResponseRedirect
from django.shortcuts import render
from chem21repo.repo.tokens import Token

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

    def get_token_form(self, request, token):
        if request.method == "POST":
            form = token.form(request.POST)
        else:
            form = token.form()
        return form

    def save_and_get_redirect(self, request, token, form):
        token.update(**form.cleaned_data)
        token.insert()
        token.question.save()
        return self._redirect(request)

    def edit_figure(self, request, qpk, para, order):
        context = {}
        question = Question.objects.get(pk=qpk)
        try:
            token = Token.get(
                "figure", para=int(para), fig=order,
                question=question)
        except Token.DoesNotExist:
            raise Http404("Token does not exist.")
        form = self.get_token_form(request, token)
        if form.is_valid():
            return self.save_and_get_redirect(request, token, form)
        context['form'] = form
        context['token_type'] = token_type
        context['token'] = token
        context['title'] = "Insert %s at paragraph %d" % (
            token_type, int(para))
        return render(request, "admin/question_token_form.html", context)

    def add_figure(self, request, qpk, para, figure):
        context = {}
        try:
            question = Question.objects.get(pk=qpk)
        except Question.DoesNotExist:
            raise Http404("Question does not exist")
        token = Token.create(
            "figure",
            para=int(para),
            fig=int(figure),
            question=question)
        form = self.get_token_form(request, token)
        if form.is_valid():
            return self.save_and_get_redirect(request, token, form)
        context['form'] = form
        context['token_type'] = 'figure'
        context['token'] = token
        context['title'] = "Insert %s at paragraph %d" % (
            'figure', int(para))
        return render(request, "admin/question_token_form.html", context)

    def remove_figure(self, request, qpk, para, figure):
        question = Question.objects.get(pk=qpk)
        token = Token.create(
            "figure",
            para=int(para),
            question=question,
            fig=int(figure))
        token.delete()
        token.question.save()
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
