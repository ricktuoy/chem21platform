from django.shortcuts import render
from django.views.generic import TemplateView
from models import File

# Create your views here.

class HomePageView(TemplateView):
	template_name="repo/full_listing.html"
	def get_context_data(self, **kwargs):
		context = super(HomePageView, self).get_context_data(**kwargs)
		context['files'] = File.objects.filter(type="video")
		return context	