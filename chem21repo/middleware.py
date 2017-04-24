import json
import urllib
import sys
import logging 
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError


def show_toolbar(request):
    return True


class C21AdminMiddleware(object):

    ADMIN_STAGE_INPUT = 1
    ADMIN_STAGE_PROCESS = 2
    ADMIN_STAGE_COMPLETE = 3

    @staticmethod
    def is_admin_uri(uri):

        return ("admin" in frozenset(uri.split("/")))

    @staticmethod
    def is_ignorable_request(request):
        try:
            parts = request.path.split("/")
            return (
                request.is_ajax() or
                parts[1] == "s3" or
                parts[1] == "__debug__" or
                parts[1] == "video_timeline")
        except IndexError:
            return False

    def get_admin_uris_in_stack(self, request):
        return [uri for uri in request.session.get('recent_uri_stack', []) if self.is_admin_uri(uri)]


    def process_response(self, request, response):
        if not hasattr(request, 'session'):
            return response

        if "admin_stage" not in request.session or request.session['admin_stage'] != self.ADMIN_STAGE_COMPLETE:
            return response

        if "admin_return_uri" not in request.session:
            logging.error("Trying to redirect but no admin return URI stored")
            return response

        return HttpResponseRedirect(request.session['admin_return_uri'])

    def process_request(self, request):
        try:
            if (request.method == "GET" and request.path == request.session['admin_return_uri']) or \
                request.session['admin_stage'] == self.ADMIN_STAGE_COMPLETE:
                    del request.session['admin_stage']
        except KeyError:
            pass

        logging.debug("Admin stage before: " + repr(request.session.get('admin_stage', "Nowt")))
        if request.method == "POST" and self.is_admin_uri(request.path) and not self.is_ignorable_request(request):
            request.session['admin_stage'] = self.ADMIN_STAGE_PROCESS
            return None

        if request.method == "GET" and self.is_admin_uri(request.path):
            if 'admin_stage' in request.session and request.session['admin_stage'] == self.ADMIN_STAGE_PROCESS:
                request.session['admin_stage'] = self.ADMIN_STAGE_COMPLETE
            else:
                request.session['admin_stage'] = self.ADMIN_STAGE_INPUT
            
        logging.debug("Admin stage after: " + repr(request.session.get('admin_stage', "Nowt")))

        if request.method != "GET" or self.is_ignorable_request(request):
            return None
        logging.debug("Request stack before: " + repr(request.session.get('recent_uri_stack', "Nowt")))

        request.session['current_uri'] = request.path
        
        if not self.is_admin_uri(request.path) and not "admin_stage" in request.session:
            request.session['admin_return_uri'] = request.path
        try:
            request.session['recent_uri_stack'].append(request.path)     
        except KeyError:
            request.session['recent_uri_stack'] = [request.path, ]
        if len(request.session['recent_uri_stack']) > 10:
            request.session['recent_uri_stack'].pop(0)

        logging.debug("Request stack after: " + repr(request.session.get('recent_uri_stack', "Nowt"))) 
        logging.debug("Return URI: %s" % repr(request.session.get('admin_return_uri', "Nowt")))
        return None


class C21ReturnURIMiddleware(object):
    def process_request(self, request):
        """
        request.session['previous_uri'] = previous_uri
        request.session['current_uri'] = request.path
        """
        return None 


class C21StaticGenMiddleware(object):
    def process_template_response(self, request, response):
        response.context_data['staticgenerator'] = getattr(
            request, 'staticgenerator', False)
        return response
