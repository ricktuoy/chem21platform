from .models import *
from django.contrib import admin
from django import forms
import logging
from filebrowser.sites import site


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
        newform.declared_fields[k] = newform.base_fields[k]
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
    class NewAdmin(admin.ModelAdmin):
        form = newform
        class Media:
            js = [
                '/s3/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js',
                '/s3/js/tinymce_setup.js',
            ]

    if not base_admin:
        final_admin = NewAdmin
    else:
        final_admin = base_admin

    final_admin.save_model = getattr(final_admin, "save_model", final_admin)

    return {'modeladmin': NewAdmin,
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
create_admin(
    model=Topic, 
    fields=['name', 'text','icon' ]
)
create_admin(
    model=Question,
    hidden_fields=['lessons', ],
    fields=["title", 'text', 'byline'])
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
        'fk': ['biblio',],
    }

create_admin(
    model=PresentationAction,
    hidden_fields=['presentation', ],
    fields=["start", "end", "biblio"],
    base_admin=PresentationActionAdmin)

for md in [Question, UniqueFile, Author,
           LearningTemplate, Molecule,
           Event, Lesson, FileLink, Module,
           UniqueFilesofModule, CredentialsModel]:
    create_power_admin(md)
