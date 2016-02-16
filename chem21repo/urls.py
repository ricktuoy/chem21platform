"""chem21 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib import admin
from filebrowser.sites import site as fbsite
from repo.views import *
from chem21.views import *

urlpatterns = [
    url('^', include('django.contrib.auth.urls')),
    url(r'^filebrowser/', include(fbsite.urls)),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^listing/$', HomePageView.as_view()),
    url(r'^video/(?P<checksum>[^/]+)[/]?$',
        VideoView.as_view(), name="video_detail"),
    url(r'^source_file/move/(?P<from_id>[0-9]+)/(?P<to_id>[0-9]+)[/]?$',
        SourceFileMoveView.as_view(), name="source_file_move"),
    url(r'^cut_file/move/(?P<from_id>[0-9]+)/(?P<to_id>[0-9]+)[/]?$',
        CutFileMoveView.as_view(), name="cut_file_move"),
    url(r'^topic/move/(?P<from_id>[0-9]+)/(?P<to_id>[0-9]+)[/]?$',
        TopicMoveView.as_view(), name="topic_move"),
    url(r'^module/move/(?P<from_id>[0-9]+)/(?P<to_id>[0-9]+)[/]?$',
        ModuleMoveView.as_view(), name="module_move"),
    url(r'^lesson/move/(?P<from_id>[0-9]+)/(?P<to_id>[0-9]+)/(?P<parent_id>[0-9]+)[/]?$',
        LessonMoveView.as_view(), name="lesson_move"),
    url(r'^question/move/(?P<from_id>[0-9]+)/(?P<to_id>[0-9]+)/(?P<parent_id>[0-9]+)[/]?$',
        QuestionMoveView.as_view(), name="question_move"),
    url(r'^lesson/remove/(?P<id>[0-9]+)/(?P<parent_id>[0-9]+)[/]?$',
        LessonRemoveView.as_view(), name="lesson_remove"),
    url(r'^question/remove/(?P<id>[0-9]+)/(?P<parent_id>[0-9]+)[/]?$',
        QuestionRemoveView.as_view(), name="question_remove"),
    url(r'^file/remove/(?P<id>[0-9]+)/(?P<parent_id>[0-9]+)[/]?$',
        FileRemoveView.as_view(), name="file_remove"),
    url(r'^file/delete/(?P<id>[0-9]+)/(?P<parent_id>[0-9]+)[/]?$',
        FileDeleteView.as_view(), name="file_delete"),
    url(r'^endnote/upload/$', EndnoteUploadView.as_view(),
        name="endnote_upload"),
    url(r'^endnote/search/(?P<term>.+)/$', EndnoteSearchView.as_view(),
        name="endnote_search"),
    url(r'^files/add/(?P<target_type>.+)/(?P<target_id>[0-9]+)/$',
        AddFileView.as_view(),
        name="add_files"),
    url(r'version/(?P<pk>[0-9]+)[/]?$', TextVersionView.as_view(),
        name="version"),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^local/strip_remote/', StripRemoteIdView.as_view(), name="strip_id"),
    url(r'^push/', PushView.as_view(), name="push_ajax"),
    url(r'^local/clear/', MarkAsCleanView.as_view(), name="clear_ajax"),
    url(r'^local/sync/', PullView.as_view(), name="pull_ajax"),
    url(r'^dirty/(?P<object_name>.+)/(?P<id>[0-9]+)/$',
        DirtyView.as_view(), name="dirty"),
    url(r'^[/]?$', FrontView.as_view(), name="front"),
    url(r'^(?P<slug>[^/]*)/$', TopicView.as_view(), name="topic"),
    url(r'^(?P<topic_slug>[^/]*)/(?P<slug>[^/]*)/$',
        ModuleView.as_view(), name="module_detail"),
    url(r'^(?P<topic_slug>[^/]*)/(?P<module_slug>[^/]*)/(?P<slug>[^/]*)/$',
        LessonView.as_view(), name="lesson_detail"),
    url(r'^(?P<topic_slug>[^/]*)/(?P<module_slug>[^/]*)/(?P<lesson_slug>[^/]*)/(?P<slug>[^/]*)/$',
        QuestionView.as_view(), name="question_detail"),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ) + urlpatterns
