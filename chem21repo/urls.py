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
    url('', include('social_django.urls', namespace='social')),
    url(r'^login-error/$',
        TemplateView.as_view(template_name="chem21/login-error.html"), name="about"),
    url(r'^filebrowser/', include(fbsite.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^listing/$', HomePageView.as_view()),
    url(r'^video/(?P<checksum>[^/]+)[/]?$',
        VideoView.as_view(), name="video_detail"),
    url(r'^video_timeline/(?P<pk>[0-9]+).json', VideoTimelineView.as_view(), name="video_timeline"),
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
    url(r'^upload_media/(?P<type>[^/]*)/(?P<pk>[0-9]*)[/]?$', 
        MediaUploadView.as_view(), 
        name="media_upload"),
    url(r'^detach_media/(?P<type>[^/]*)/(?P<tpk>[0-9]*)/(?P<fpk>[0-9]+)/?$',#
        DetachMediaView.as_view(),
        name="media_detach"),
    url(r'^touched/(?P<type>[^/]*)/(?P<tpk>[0-9]*)/?$',
        ShowTouchedView.as_view(),
        name="touched"),
    url(r'^endnote/upload/$', EndnoteUploadView.as_view(),
        name="endnote_upload"),
    url(r'^endnote/search/(?P<term>.+)/$', BiblioSearchView.as_view(),
        name="endnote_search"),
    url(r'^files/add/(?P<target_type>.+)/(?P<target_id>[0-9]+)/$',
        AddFileView.as_view(),
        name="add_files"),
    url(r'^_admin/publish/pages/?$', PublishPagesView.as_view()),
    url(r'^_admin/publish/?$', PublishLearningObjectsView.as_view(),
        name="publish_view"),
    url(r'^_admin/publish/all/?$', PageIDsView.as_view(), 
        name="publishable_ids"),
    url(r'^_admin/publish/pdfs/?$', PDFIDsView.as_view(),
        name="pdf_ids"),
    url(r'^figures/get/(?P<type>.+)/(?P<pk>[0-9]+)/$',
        FiguresGetView.as_view(),
        name="get_figures"),
    url(r'^file_link/get/(?P<type>.+)/(?P<pk>[0-9]+)/$',
        FileLinkGetView.as_view(),
        name="get_file_link"),
    url(r'^structure/get/$',
        StructureGetView.as_view(),
        name="get_structure"),
    url(r'^files/attach/$',
        AttachUniqueFileView.as_view(),
        name="attach_files"),
    url(r"^get_molecules/$",
        MoleculeListView.as_view()),
    url(r'^set_molecule/(?P<type>[^/]+)/(?P<tpk>[0-9]+)/(?P<mpk>[0-9]+)/$',
        MoleculeAttachView.as_view()),
    url(r'^quiz/import/(?P<object_name>.+)/(?P<id>[0-9]+)/$',
    	ImportQuizView.as_view(), name="quiz_import"),
    url(r'^guide/import/(?P<object_name>.+)/(?P<id>[0-9]+)/$',
        ImportGuideToolView.as_view(), name="quiz_import"),
    url(r'^figure/delete/(?P<type>[^/]+)/(?P<tpk>[0-9]+)/(?P<fNum>[0-9]+)/?$',
        FigureDeleteView.as_view(), name="figure_delete"),
    url(r'version/(?P<pk>[0-9]+)[/]?$', TextVersionView.as_view(),
        name="version"),
    url(r'^local/strip_remote/', StripRemoteIdView.as_view(), name="strip_id"),
    url(r'^push/', PushView.as_view(), name="push_ajax"),
    url(r'^local/clear/', MarkAsCleanView.as_view(), name="clear_ajax"),
    url(r'^about/$',
        TemplateView.as_view(template_name="chem21/about.html"), name="about"),
    url(r'^legal/$',
        TemplateView.as_view(template_name="chem21/legal.html"), name="legal"),
    url(r'^local/sync/', PullView.as_view(), name="pull_ajax"),
    url(r'^dirty/(?P<object_name>.+)/(?P<id>[0-9]+)/$',
        DirtyView.as_view(), name="dirty"),
    url(r'^s3/(?P<path>.*)$', S3ProxyView.as_view(), name="s3_proxy"),
    url(r'^[/]?$', FrontView.as_view(), name="front"),
    url(r'^(?P<slug>[^/]*)/$', TopicView.as_view(), name="topic"),
    url(r'complete/google-service-oauth2', GoogleServiceOAuth2ReturnView.as_view(), name="google-service-oauth2-return"),
    url(r'files/upload/youtube/(?P<type>[^/]+)/(?P<tpk>[0-9]+)/(?P<vpk>[0-9]+)/$', PushVideoToYouTubeView.as_view(), 
        name="youtube_upload"),
    url(r'^video/transcripts/list/$', YouTubeCaptionListView.as_view()),
    url(r'^video/transcripts/get/(?P<pk>[0-9]+)/?$', YouTubeTranscriptView.as_view()),
    url(r'^(?P<topic_slug>[^/]*)/(?P<slug>[^/]*)/$',
        ModuleView.as_view(), name="module_detail"),
    url(r'^(?P<topic_slug>[^/]*)/(?P<module_slug>[^/]*)/(?P<slug>[^/]*)/$',
        LessonView.as_view(), name="lesson_detail"),
    url(r'^(?P<topic_slug>[^/]*)/(?P<module_slug>[^/]*)/(?P<lesson_slug>[^/]*)/(?P<slug>[^/]*)/$',
        QuestionView.as_view(), name="question_detail")

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = patterns('',
                           url(r'^__debug__/', include(debug_toolbar.urls)),
                           ) + urlpatterns
