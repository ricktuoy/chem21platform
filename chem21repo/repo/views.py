from django.shortcuts import render
from django.views.generic import TemplateView, DetailView
from .models import UniqueFile, Topic
from django.db.models import Prefetch
import logging

# Create your views here.

class HomePageView(TemplateView):
	template_name="repo/full_listing.html"
	def get_context_data(self, **kwargs):
		context = super(HomePageView, self).get_context_data(**kwargs)
		context['files'] = UniqueFile.objects.filter(type="video")
		context['topics'] = Topic.objects.all().prefetch_related(
			"modules",
			Prefetch("modules__files", 
				queryset=UniqueFile.objects.filter(type="video",cut_of__isnull=True),
				to_attr="video_files"),
			Prefetch("modules__video_files__cuts", 
				queryset=UniqueFile.objects.filter(type="video")))
		return context	

class VideoView(DetailView):
	model = UniqueFile
	template_name = "repo/video_detail.html"
	slug_field = "checksum"
	slug_url_kwarg = "checksum"


