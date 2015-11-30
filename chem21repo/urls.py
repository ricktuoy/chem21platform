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


urlpatterns = [
    url(r'^filebrowser/', include(fbsite.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^[/]?$', HomePageView.as_view()),
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
    url(r'^push/', PushView.as_view(), name="push_json")
]
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)),
                            )
