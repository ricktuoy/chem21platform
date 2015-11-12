import base64
import json
import requests

from django.conf import settings
from django.core.files.storage import get_storage_class


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

    def auth(fn):
        def inner(obj, method, **kwargs):
            if not obj.auth_data:
                raise RESTAuthError(
                    "Method %s requires authentication" % method)
            kwargs['cookies'] = obj._merge_auth_cookies(kwargs)
            return fn(obj, method, **kwargs)
        return inner

    def extend_method(fn):
        def inner(obj, method, **kwargs):
            return fn(obj.abs_url(method), **kwargs)
        return inner

    get = extend_method(requests.get)
    post = extend_method(requests.post)
    put = extend_method(requests.put)
    get_auth = auth(get)
    post_auth = auth(post)
    put_auth = auth(put)

    def get_json_response(self):
        try:
            return self.response.json()
        except ValueError:
            raise RESTError(
                "Bad response %s from method %s (expected JSON)" % (
                    self.response, self.method_name))


class DrupalNode(object):

    """wrapper for Drupal node via API"""

    def __init__(self, node={}):
        self.node = node

    def is_h5p(self):
        return self.json['type'] == "h5p_content"

    def is_h5p_video(self):
        try:
            if self.node['main_library']['name'] == "H5P.InteractiveVideo":
                return True
        except KeyError:
            pass
        return False

    @property
    def h5p_data(self):
        if not self.is_h5p():
            return None
        else:
            return self.node['json_content']

    @property
    def title(self):
        return self.node['title']

    @title.setter
    def title(self, title):
        self.node['title'] = title
        if self.is_h5p_video():
            self.node['json_content']['interactiveVideo'][
                'video']['title'] = title

    

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
            "/lesson_tree/retrieved/", params={'course': cId})
        return self.get_json_response()

    def get_node(self, nId):
        self.method_name = "get_node"
        self.response = self.get_auth(
            "/node/%d" % nId)
        return self.get_json_response()

    def create_video_question(self, lId, title, ufile, intro):
        self.method_name = "create_video_question"
        mstorage = get_storage_class(settings.MEDIAFILES_STORAGE)()
        lstorage = get_storage_class(settings.STATICFILES_STORAGE)()
        with mstorage.open(ufile.path, "rb") as v_file:
            encoded_video = base64.b64encode(v_file.read())
        # with storage.open
        with lstorage.open(settings.STATIC_ROOT +
                           "video_template.json") as v_file:
            node = DrupalNode(json.loads(v_file.read()))
        node.title = title
        self.response = self.post_auth(
            "/question/", data={'node': node,
                                'video': encoded_video,
                                'lesson': lId,
                                'intro': intro})
