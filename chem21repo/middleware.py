import json
import urllib
import sys

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError


def show_toolbar(request):
    return True


class C21AdminMiddleware(object):

    def process_response(self, request, response):
        try:
            data = json.loads(
                urllib.unquote(request.COOKIES['admin_save_redirect']))
        except KeyError:
            return response
        except ValueError:
            return HttpResponseServerError(
                "Bad json value. %s" %
                request.COOKIES['admin_save_redirect'])
        try:
            if request.path == data['fromUrl']:
                url = data['url']
                response = HttpResponseRedirect(url)
                response.delete_cookie('admin_save_redirect')
        except KeyError:
            #raise KeyError("Can't find %s in %s" % ("fromUrl", data))
            pass
        return response

class C21StaticGenMiddleware(object):
	def process_template_response(self, request, response):
		response.context_data['staticgenerator'] = getattr(request, 'staticgenerator', False)
		return response