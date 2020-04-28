from django.contrib import admin
from django.http import HttpResponseRedirect


class BaseModelAdmin(admin.ModelAdmin):

    def response_add(self, request, obj, post_url_continue="../%s/"):
        if '_continue' not in request.POST:
            resolved_obj = type(obj).objects.get(pk=obj.pk)
            return HttpResponseRedirect(resolved_obj.get_canonical_page().get_absolute_url())
        else:
            return super(BaseModelAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_continue' not in request.POST:
            resolved_obj = type(obj).objects.get(pk=obj.pk)
            return HttpResponseRedirect(resolved_obj.get_canonical_page().get_absolute_url())
        else:
            return super(BaseModelAdmin, self).response_change(request, obj)
