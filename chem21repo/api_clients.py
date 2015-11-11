import base64
import json
import requests

from django.conf import settings
from django.core.files.storage import DefaultStorage


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


class DrupalNode(object):

    """wrapper for Drupal node via API"""

    def __init__(self, json=None):
        self.json = json

    def is_h5p(self):
        return self.json['type'] == "h5p_content"

    @property
    def h5p_data(self):
        if not self.is_h5p():
            return None
        else:
            return json.loads(self.json['json_content'])


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

    def create_video_question(self, lId, title, ufile, intro):
        self.method_name = "create_video_question"
        storage = DefaultStorage()
        with storage.open(ufile.path, "rb") as v_file:
            encoded_video = base64.b64encode(v_file.read())
        #with storage.open
        self.response = self.put_auth(
            "/h5p_video", data={'json_content': json.dumps(h5p),
                                'video': encoded_video})
