from .models import *
from .views import BibTeXUploadView
from django.contrib import admin
from django import forms
import logging
from filebrowser.sites import site
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render
from chem21repo.repo.tokens import Token

import urllib

def register_modeladmin(fn):
    def wrapper(*args, **kwargs):
        iargs = fn(*args, **kwargs)
        (model, modeladmin, name) = [iargs[name]
                                     for name in
                                     ('model', 'modeladmin', 'name')]

        class Meta:
            proxy = True
            app_label = model._meta.app_label

        attrs = {'__module__': '', 'Meta': Meta}
        if name:
            newmodel = type(name, (model,), attrs)
        else:
            newmodel = model
        admin.site.register(newmodel, modeladmin)
        return (newmodel, modeladmin)
    return wrapper


@register_modeladmin
def create_admin(model, fields, name="", hidden_fields=[], form=None, base_admin=None):
    themodel = model
    thefields = fields
    
    if not form:    
        class Meta:
            model = themodel
            fields = thefields + hidden_fields
        attrs = {}
        attrs['__module__'] = ''
        attrs['Meta'] = Meta
        newform = type("NewForm", (forms.ModelForm,), attrs)
    else:
        newform = form

    
    for k in hidden_fields:
        try:
            newform.declared_fields[k] = newform.base_fields[k]
        except:
            raise Exception((themodel, Exception(newform.base_fields),))
        del newform.base_fields[k]
        if isinstance(newform.declared_fields[k],
                      (forms.MultipleChoiceField,
                       forms.models.ModelMultipleChoiceField)):
            newform.declared_fields[k].widget = forms.MultipleHiddenInput()
        else:
            newform.declared_fields[k].widget = forms.HiddenInput()
        newform.declared_fields[k].label = str(
            type(newform.declared_fields[k]))

    def _save_callback(self, request, obj, form, change):
        obj.user = request.user
        obj.save()
        
    if not base_admin:
        class Media:
            js = [
                '/s3/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js',
                '/s3/js/tinymce_setup.js',
            ]
        final_admin = type("NewAdmin", (admin.ModelAdmin,), {'__module__': '', 'Media': Media})
    else:
        final_admin = base_admin

    final_admin.save_model = getattr(final_admin, "save_model", _save_callback)
    final_admin.form = newform

    return {'modeladmin': final_admin,
            'model': themodel,
            'name': str(themodel._meta.verbose_name +
                        "-" + name)
            if name else ""}


@register_modeladmin
def create_power_admin(model):
    themodel = model

    class NewAdmin(admin.ModelAdmin):
        model = themodel
    return {'modeladmin': NewAdmin,
            'model': themodel,
            'name': str(themodel._meta.verbose_name + "-power")}


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
                name='repo_question_addtoken'
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

    def delete_token(self, request, qpk, para, token_type, order):
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
           Event, Lesson, FileLink, Module,
           UniqueFilesofModule, CredentialsModel, Biblio]:
    create_power_admin(md)
