from apiclient.discovery import build
from apiclient.errors import HttpError as GoogleHttpError
from apiclient.http import MediaIoBaseUpload as GoogleMediaIoBaseUpload

from oauth2client.contrib.django_orm import Storage
from oauth2client.client import OAuth2WebServerFlow as Flow
from oauth2client.contrib import xsrfutil
from .repo.models import CredentialsModel

from django.views.generic import View
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

import httplib2
import httplib
import dateutil.parser

class GoogleOAuth2RedirectRequired(Exception):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return self.url

class GoogleUploadError(Exception):
    pass

class GoogleFlowBaseMixin(object):
  @property
  def flow(self):
      try:
          return self._flow
      except AttributeError:
          pass
      self._flow = Flow(settings.GOOGLE_OAUTH2_KEY, settings.GOOGLE_OAUTH2_SECRET, 
          scope=self.get_google_scope_for_authorization(),
          prompt="consent",
          access_type="offline",
          redirect_uri=self.request.build_absolute_uri(reverse("google-service-oauth2-return")))
      return self._flow

  def get_google_scope_for_authorization(self):
    return self.request_scopes

  @property
  def request_scopes(self):
    return self.request.session.get("google_service_scope", "").split(" ")  




class GoogleServiceMixin(GoogleFlowBaseMixin):
    # Always retry when these exceptions are raised.
    RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
      httplib.IncompleteRead, httplib.ImproperConnectionState,
      httplib.CannotSendRequest, httplib.CannotSendHeader,
      httplib.ResponseNotReady, httplib.BadStatusLine)

    # Always retry when an apiclient.errors.HttpError with one of these status
    # codes is raised.
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
    MAX_RETRIES = 10

    def get_google_scope_for_authorization(self):
      if not self.scope_is_authorized():
        return self.refresh_google_scope()
      return self.request_scopes

    def refresh_google_scope(self):
        scopes = set(self.request_scopes)
        scopes.update(self.scopes)
        self.request.session["google_service_scope"] = " ".join(scopes)
        return scopes

    @property
    def scopes(self):
      try:
        return self.google_scope.split(" ")
      except AttributeError:
        return []


    def scope_is_authorized(self):
      return frozenset(self.scopes).issubset(frozenset(self.request_scopes))

    @property
    def google_storage(self):
        try:
            return self._google_storage
        except AttributeError:
            pass
        self._google_storage = Storage(CredentialsModel, 'id', self.request.user, 'credential')
        return self._google_storage

    @property
    def credential(self):
        try:
            return self._credential
        except AttributeError:
            pass
        self._credential = self.google_storage.get()
        return self._credential

    @property
    def return_path_session_key(self):
        return "google_oauth_return_path"
    

    def redirect_authorize(self):
      self.flow.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                       self.request.user)
      self.request.session[self.return_path_session_key] = self.request.path
      authorize_url = self.flow.step1_get_authorize_url()
      raise GoogleOAuth2RedirectRequired(authorize_url)

    def get_service(self, request=None):
        try:
            return self._service
        except AttributeError:
            pass
        if request:
            self.request = request
        if self.credential is None or self.credential.invalid == True or not self.scope_is_authorized():    
            self.redirect_authorize()
        else:
            http = httplib2.Http()
            http = self.credential.authorize(http)
            return build(self.google_service_name, self.google_api_version, http=http)

    # This method implements an exponential backoff strategy to resume a
    # failed upload.
    # from https://developers.google.com/youtube/v3/guides/uploading_a_video#Sample_Code
    def resumable_upload(self, insert_request):

      httplib2.RETRIES = 1
      response = None
      error = None
      retry = 0
      while response is None:
        try:
          status, response = insert_request.next_chunk()
          if 'id' in response:
            return response
          else:
            raise GoogleUploadError("The upload failed with an unexpected response: %s" % response)
        except GoogleHttpError, e:
          if e.resp.status in self.RETRIABLE_STATUS_CODES:
            error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                 e.content)
          else:
            raise
        except self.RETRIABLE_EXCEPTIONS, e:
          error = "A retriable error occurred: %s" % e

        if error is not None:
          retry += 1
          if retry > self.MAX_RETRIES:
            raise GoogleUploadError("The upload failed after %d attempts: %s" % (self.MAX_RETRIES, response))

          max_sleep = 2 ** retry
          sleep_seconds = random.random() * max_sleep
          time.sleep(sleep_seconds)

class YouTubeServiceMixin(GoogleServiceMixin):
    google_scope = "https://www.googleapis.com/auth/youtube.upload"
    google_service_name = "youtube"
    google_api_version = "v3"

class YouTubeCaptionServiceMixin(GoogleServiceMixin):
    google_scope = "https://www.googleapis.com/auth/youtube.force-ssl"
    google_service_name = "youtube"
    google_api_version = "v3"

    # Call the API's captions.list method to list the existing caption tracks.
    def get_caption_list(self, youtube, video_id):
        try:
            results = youtube.captions().list(
                part="snippet",
                videoId=video_id
                ).execute()
        except GoogleHttpError, e:
            if e.resp.status==404:
                return None
            if e.resp.status==403:
                self.redirect_authorize()
        return results['items']


    def get_recent_caption(self, youtube, video_id):
        caption_set = self.get_caption_list(youtube, video_id)
        if caption_set is None:
            return None
        def reduce_fn(c1, c2):
            if c2['snippet']['language'] != "en":
                return c1
            if c1 is None:
                return c2
            t1 = dateutil.parser.parse(c1['snippet']['lastUpdated'])
            t2 = dateutil.parser.parse(c2['snippet']['lastUpdated'])
            if t1 < t2:
                return c2
            return c1 

        return reduce(reduce_fn, caption_set, None)

    def get_srt(self, youtube, caption_id):
      try:
        result = youtube.captions().download(id=caption_id, tfmt="srt").execute()
      except GoogleHttpError, e:
        if e.resp.status==404:
          return None
        if e.resp.status==403:
          self.redirect_authorize()
      return result


class DriveServiceMixin(GoogleServiceMixin):
    google_scope = "https://www.googleapis.com/auth/drive.readonly"
    google_service_name = "drive"
    google_api_version = "v3"


class GoogleServiceOAuth2ReturnView(GoogleServiceMixin, View):

    def get(self, request, *args, **kwargs):
        if not xsrfutil.validate_token(settings.SECRET_KEY, str(request.REQUEST['state']),
                                 request.user):
            return  HttpResponseBadRequest("ERROR: XSRF fail. %s %s %s" % (
              str(request.REQUEST['state']), 
              settings.SECRET_KEY, 
              request.user))
        credential = self.flow.step2_exchange(request.REQUEST)
        storage = Storage(CredentialsModel, 'id', request.user, 'credential')
        storage.put(credential)

        return HttpResponseRedirect(request.session.get(self.return_path_session_key,"/"))
