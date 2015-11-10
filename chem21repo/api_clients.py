import requests
from django.conf import settings


class RESTAuthError(Exception):
    pass


class RESTError(Exception):
    pass


class DrupalRESTRequests(object):

    """wrapper to requests lib for Drupal REST server """

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password

    def abs_url(self, rel_url):
        return self.base_url + rel_url

    def authenticate(self):
        self.response = self.post("/user/login",
                                  data={'username': self.username,
                                        'password': self.password})
        try:
            self.auth_data = self.response.json()
        except ValueError:
            raise RESTAuthError(
                "Unable to authenticate with endpoint %s" % self.base_url)

    def _merge_auth_cookies(self, args):
        cookies = getattr(args, 'cookies', {})
        cookies[self.auth_data['session_name']] = self.auth_data['sessid']
        return cookies

    def get(self, method, **kwargs):
        return requests.get(self.abs_url(method), **kwargs)

    def get_auth(self, method, **kwargs):
        if not self.auth_data:
            raise RESTAuthError("Method %s requires authentication" % method)
        kwargs['cookies'] = self._merge_auth_cookies(kwargs)
        return self.get(method, **kwargs)

    def post(self, method, **kwargs):
        return requests.post(self.abs_url(method), **kwargs)

    def post_auth(self, method, **kwargs):
        if not self.auth_data:
            raise RESTAuthError("Method %s requires authentication" % method)
        kwargs['cookies'] = self._merge_auth_cookies(kwargs)
        return self.post(method, **kwargs)

    def get_json_response(self):
        try:
            return self.response.json()
        except ValueError:
            raise RESTError(
                "Bad response %s from method %s (expected JSON)" % (
                    self.response, self.method_name))


class C21RESTRequests(DrupalRESTRequests):

    """wrappers for CHEM21 API methods"""

    def __init__(self, *args, **kwargs):
        kwargs['base_url'] = getattr(kwargs,
                                     'base_url',
                                     settings.CHEM21_PLATFORM_BASE_URL +
                                     settings.CHEM21_PLATFORM_REST_API_URL)
        kwargs['username'] = getattr(kwargs,
                                     'username',
                                     settings.CHEM21_PLATFORM_API_USER)
        kwargs['password'] = getattr(kwargs,
                                     'password',
                                     settings.CHEM21_PLATFORM_API_PWD)
        return super(C21RESTRequest, self).init(*args, **kwargs)

    def get_courses(self):
        self.method_name = "get_courses"
        self.response = self.get_auth(
            "/node", params={'parameters[type]': 'course'})
        return self.get_json_response()

    def get_lesson_tree(self, cId):
        self.method_name = "get_lesson_tree"
        self.response = self.get_auth(
            "/lesson_tree/retrieve", params={'course': cId})
        return self.get_json_response()

    def get_node(self, nId):
        self.method_name = "get_node"
        self.response = self.get_auth(
            "/node/%d" % nId)
        return self.get_json_response()


