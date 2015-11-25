from .models import *
from django.contrib import admin
from django import forms
import logging


def create_modeladmin(fn):
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


@create_modeladmin
def create_admin(model, fields, name="", hidden_fields=[], ):
    themodel = model
    thefields = fields

    class Meta:
        model = themodel
        fields = thefields + hidden_fields
    attrs = {}
    # attrs = dict([(k, v(widget=forms.HiddenInput()))
    #              for k, v in hidden_fields.iteritems()])
    attrs['__module__'] = ''
    attrs['Meta'] = Meta

    newform = type("NewForm", (forms.ModelForm,), attrs)

    for k in hidden_fields:
        newform.declared_fields[k] = newform.base_fields[k]
        del newform.base_fields[k]
        newform.declared_fields[k].widget = forms.HiddenInput()

    class NewAdmin(admin.ModelAdmin):
        form = newform

    return {'modeladmin': NewAdmin,
            'model': model,
            'name': str(model._meta.verbose_name + "-" + name) if name else ""}


@create_modeladmin
def create_power_admin(model):
    themodel = model

    class NewAdmin(admin.ModelAdmin):
        model = themodel
    return {'modeladmin': NewAdmin,
            'model': themodel,
            'name': str(themodel._meta.verbose_name + "-power")}


create_admin(
    model=Module,
    fields=['name', 'code'],
    hidden_fields=['topic', ],
)
create_admin(model=Topic, fields=['name', ])


create_admin(
    model=Question,
    # hidden_fields=['lessons', ],
    fields=["title", 'lessons'])

create_admin(
    model=Lesson,
    # hidden_fields=['modules', ],
    fields=["title", 'modules'])

for md in [Question, UniqueFile, Author,
           Event, Lesson, FileLink,
           UniqueFilesofModule]:
    create_power_admin(md)
