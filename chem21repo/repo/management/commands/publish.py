from chem21repo.storage import S3StaticFileSystem
from staticgenerator import StaticGenerator

from chem21repo.repo.models import Question, Lesson, Module, Topic
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse


class Command(BaseCommand):
    help = 'Print nodes with text changes'

    def handle(self, *args, **options):
        paths = ['/', ]
        for topic in Topic.objects.all():
            paths.append(reverse('topic', kwargs={'slug': topic.slug}))
            
            for module in topic.modules.all():
                paths.append(
                    reverse('module_detail', kwargs={
                        'topic_slug': topic.slug,
                        'slug': module.slug}))
                
                for lesson in module.lessons.all():
                    paths.append(reverse('lesson_detail', kwargs={
                                 'topic_slug': topic.slug,
                                 'module_slug': module.slug,
                                 'slug': lesson.slug}))
	                for question in lesson.questions.all():
	                    paths.append(reverse('question_detail', kwargs={
	                                 'topic_slug': topic.slug,
	                                 'module_slug': module.slug,
	                                 'lesson_slug': lesson.slug,
	                                 'slug': question.slug}))
	        
	    gen = StaticGenerator(*paths, fs=S3StaticFileSystem())
        gen.publish()
