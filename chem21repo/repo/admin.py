from .models import *
from .views import BibTeXUploadView, LoadFromGDocView
from django.contrib import admin

import logging
from filebrowser.sites import site
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render
from chem21repo.repo.tokens import Token



create_admin(
    model=Module,
    fields=['name', 'code', 'text'],
    hidden_fields=['topic', ],
)


class BiblioAdmin(admin.ModelAdmin):
    def get_urls(self):
        from django.conf.urls import patterns
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
    fields=['name', 'text','icon' ]
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
    fields=["name","description"])

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
        from django.conf.urls import patterns
        from django.conf.urls import url
        #from django.conf.urls.defaults import *
        urls = super(QuestionAdmin, self).get_urls()
        my_urls = [
            url(r'^add_token/([0-9]+)/([0-9]+)/(.*)$',
                self.admin_site.admin_view(self.add_token),
                name='page_add_token'
                ),
            url(r'^remove_token/([0-9]+)/([0-9]+)/(.*)$',
                self.admin_site.admin_view(self.delete_token),
                name='page_remove_token'
                ),
            url(r'^load_gdoc/(?P<tpk>[0-9]+)/(?P<file_id>.*)[/]?$',
                self.admin_site.admin_view(LoadFromGDocView.as_view()),
                name='page_load_text'
                ),
        ]
        return my_urls + urls

    def _redirect(self, request):
        url = request.session.get('admin_return_uri',"/")
        return HttpResponseRedirect(url)

    def get_token_form(self, request, token):
        if request.method == "POST":
            form = token.form(request.POST)
        else:
            form = token.form()
        return form

    def save_and_get_redirect(self, request, token, form):           
        token.update(**form.cleaned_data)
        token.render()
        token.question.save()
        return self._redirect(request)

    def update_token(self, request, qpk, para, token_type, order):
        context = {}
        question = Question.objects.get(pk=qpk)
        try:
            token = Token.get(token_type, para=int(para), question = question, order=order)
        except Token.DoesNotExist:
            raise Http404("Token does not exist.")
        form = self.get_token_form(request, token)
        if form.is_valid():
            return self.save_and_get_redirect(request, token, form)
        context['form'] = form
        context['token_type'] = token_type
        context['token'] = token
        context['title'] = "Insert %s at paragraph %d" % (token_type, int(para)) 
        return render(request, "admin/question_token_form.html", context)

    def add_token(self, request, qpk, para, token_type):
        context = {}
        try:
            question = Question.objects.get(pk=qpk)
        except Question.DoesNotExist:
            raise Http404("Question does not exist")
        token = Token.create(token_type, para=int(para), question = question)
        form = self.get_token_form(request, token)
        if form.is_valid():
            return self.save_and_get_redirect(request, token, form)
        context['form'] = form
        context['token_type'] = token_type
        context['token'] = token
        context['title'] = "Insert %s at paragraph %d" % (token_type, int(para)) 
        return render(request, "admin/question_token_form.html", context)

    def delete_token(self, request, qpk, para, token_type):
        question = Question.get(qpk)
        try:
            token = Token.get(token_type, para=int(para), question=question, order=order)
        except Token.DoesNotExist:
            raise Http404("Token does not exist.")
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
