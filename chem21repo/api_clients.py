import requests
import logging
from django.conf import settings


class RESTAuthError(Exception):
    pass


class RESTError(Exception):
    pass


class DrupalRESTRequests(object):

    """wrapper to requests lib for Drupal REST server """

    def __init__(self, base_url, rest_url, username, password):
        self.base_url = base_url
        self.rest_url = rest_url
        self.username = username
        self.password = password
        self.auth_data = None
        self.csrf_token = None

    def authenticate(self, force=False):
        if not self.auth_data or force:
            response = self._post("/user/login",
                                  data={'username': self.username,
                                        'password': self.password})
            if response.status_code != 200:
                raise RESTAuthError(response.text)
            try:
                self.auth_data = response.json()
            except ValueError:
                raise RESTAuthError(
                    "Authentication did not return JSON at %s" % self.base_url)
        return self.auth_data

    def get_csrf_headers(self, force=False):
        # if not self.csrf_token or force:
        response = requests.get(
            self.base_url + "/services/session/token",
            cookies=self.get_auth_cookies())
        if response.status_code != 200:
            raise RESTAuthError("CSRF returned %d %s (%s)" %
                                (response.status_code,
                                    response.text,
                                    self.base_url + "/services/session/token"))
        try:
            self.csrf_token = response.text
        except ValueError:
            raise RESTAuthError(
                "CSRF token returned odd value at %s" % self.base_url)
        return {'X-CSRF-Token': self.csrf_token}

    def pull(self, node):
        response = self.get(node.object_name, node.id)
        node.populate(**response)
        return response

    def push(self, node):
        try:
            if node.id:
                try:
                    out = (self.update(node.id,
                                       node.__class__(**node.dirty())),
                           False)
                    return out
                except RESTError, e:
                    if not self.response.status_code == 410:
                        raise e
        except AttributeError:
            pass
        response = self.create(node)
        return (response, True)

    def get(self, object_name, id):
        self.method_name = "get_" + object_name
        self.response = self._get_auth(
            "/%s/%d" % (object_name, id))
        return self.get_json_response()

    def create(self, node):
        self.method_name = "create_%s" % node.object_name
        node.serialise_fields()
        # logging.debug("Create node: %s" % node)
        self.response = self._post_auth("/%s/" % node.object_name, json=node)
        # logging.debug("Create result: %s" % self.response.text)
        return self.get_json_response()

    def update(self, id, node):
        node.set('id', id)
        self.method_name = "update_%s" % node.object_name
        
        node.remove_empty_optional_fields()
        node.serialise_fields()
        logging.debug("Update node: %s" % node.filter_changed_fields())
        self.response = self._put_auth(
            "/%s/%s/" % (node.object_name, id),
            json=node.filter_changed_fields())
        logging.debug("Update result: %s" % self.response.text)
        return self.get_json_response()

    def _auth(fn):
        def inner(obj, method, **kwargs):
            obj.authenticate()
            kwargs['cookies'] = obj._update_auth_cookies(**kwargs)
            kwargs['headers'] = obj._update_csrf_headers(**kwargs)
            return fn(obj, method, **kwargs)
        return inner

    def _extend_method(fn):
        def inner(obj, method, **kwargs):
            return fn(obj._abs_url(method), **kwargs)
        return inner

    _get = _extend_method(requests.get)
    _post = _extend_method(requests.post)
    _put = _extend_method(requests.put)
    _delete = _extend_method(requests.delete)
    _get_auth = _auth(_get)
    _post_auth = _auth(_post)
    _put_auth = _auth(_put)
    _delete_auth = _auth(_delete)

    def _abs_url(self, rel_url):
        url = self.base_url + self.rest_url
        return url + rel_url

    def get_auth_cookies(self):
        return {self.auth_data['session_name']: self.auth_data['sessid']}

    def _update_csrf_headers(self, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers'].update(self.get_csrf_headers())
        return kwargs['headers']

    def _update_auth_cookies(self, **kwargs):
        kwargs['cookies'] = kwargs.get('cookies', {})
        kwargs['cookies'].update(self.get_auth_cookies())
        return kwargs['cookies']

    def get_json_response(self):
        if self.response.status_code != 200:
            raise RESTError(
                "Method %s (%s) returned status code %s: %s. Headers %s" % (
                    self.method_name, self.response.url,
                    self.response.status_code, self.response.text,
                    self.response.headers))
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
                                     settings.CHEM21_PLATFORM_BASE_URL)
        kwargs['rest_url'] = getattr(kwargs,
                                     'rest_url',
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
            "/node", params={'parameters[type]': 'course','pagesize': 500})

        return self.get_json_response()

    def import_endnote(self, fl):
        self.method_name = "import_endnote"
        self.response = self._post_auth(
            "/biblio/import", data={'data': fl})
        return self.get_json_response()

    def search_endnote(self, term):
        self.method_name = "search_endnote"
        # raise Exception(term)
        self.response = self._get_auth(
            "/biblio", params={'term': term})
        return self.get_json_response()
