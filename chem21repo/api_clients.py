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
        self.auth_data = None

    def authenticate(self):
        self.response = self._post("/user/login",
                                   data={'username': self.username,
                                         'password': self.password})
        if self.response.status_code != 200:
            raise RESTAuthError(self.response.text)
        try:
            self.auth_data = self.response.json()
        except ValueError:
            raise RESTAuthError(
                "Authentication did not return JSON at %s" % self.base_url)

    def pull(self, node):
        self.get(node.object_name, node.id)
        node.populate(**self.get_json_response())

    def push(self, node):
        try:
            self.update(node.id, node)
        except AttributeError:
            self.create(node)

    def get(self, object_name, id):
        self.method_name = "get_" + object_name
        self.response = self._get_auth(
            "/%s/%d" % (object_name, id))
        return self.get_json_response()

    def create(self, node):
        self.method_name = "create_%s" % node.object_name
        node.serialise_extra_fields()
        self.response = self.post_auth("/%s/" % node.object_name, data=node)
        return self.get_json_response()

    def update(self, id, node):
        self.method_name = "update_%s" % node.object_name
        node.remove_empty_optional_fields()
        node.serialise_extra_fields()
        self.response = self.post_auth(
            "/%s/" % (node.object_name, id), data=node.filter_changed_fields())
        return self.get_json_response()

    # ------------------------------- helpers

    def _auth(fn):
        def inner(obj, method, **kwargs):
            if not obj.auth_data:
                raise RESTAuthError(
                    "Method %s requires authentication" % method)
            kwargs['cookies'] = obj._merge_auth_cookies(kwargs)
            return fn(obj, method, **kwargs)
        return inner

    def _extend_method(fn):
        def inner(obj, method, **kwargs):
            return fn(obj._abs_url(method), **kwargs)
        return inner

    _get = _extend_method(requests.get)
    _post = _extend_method(requests.post)
    _put = _extend_method(requests.put)
    _get_auth = _auth(_get)
    _post_auth = _auth(_post)
    _put_auth = _auth(_put)

    def _abs_url(self, rel_url):
        return self.base_url + rel_url

    def _merge_auth_cookies(self, args):
        cookies = getattr(args, 'cookies', {})
        cookies[self.auth_data['session_name']] = self.auth_data['sessid']
        return cookies

    def get_json_response(self):
        try:
            return self.response.json()
        except ValueError:
            raise RESTError(
                "Bad response %s from method %s (%s)\n %s" % (
                    self.response, self.response.url,
                    self.method_name, self.response.text))


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
        return super(C21RESTRequests, self).__init__(*args, **kwargs)

    def index_courses(self):
        self.method_name = "index_courses"
        self.response = self._get_auth(
            "/node", params={'parameters[type]': 'course'})
        return self.get_json_response()
