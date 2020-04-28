def show_toolbar(request):
    return True


class C21StaticGenMiddleware(object):
    def process_template_response(self, request, response):
        response.context_data['staticgenerator'] = getattr(
            request, 'staticgenerator', False)
        return response
