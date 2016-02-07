
from chem21repo.repo.models import Lesson
from chem21repo.repo.models import Module
from chem21repo.repo.models import Question
from chem21repo.repo.models import Topic

from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify


class Command(BaseCommand):
    help = 'Print nodes with text changes'

    def handle(self, *args, **options):
    	for topic in Topic.objects.all():
        	topic.slug = slugify(topic.title)
        	topic.save()
        print "*** MODULES"
        for module in Module.objects.all():
        	module.slug = slugify(module.title)
        	module.save()
        print "*** LESSONS"
        for lesson in Lesson.objects.all():
        	lesson.slug = slugify(lesson.title)
        	lesson.save()
        print "*** QUESTIONS"
        for question in Question.objects.all():
            question.slug = slugify(question.title)
            question.save()
