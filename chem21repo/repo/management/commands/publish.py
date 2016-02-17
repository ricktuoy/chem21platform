from chem21repo.storage import S3StaticFileSystem
from staticgenerator import StaticGenerator

from chem21repo.repo.models import Question, Lesson, Module, Topic
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse


class Command(BaseCommand):
    help = 'Publish the site'
    leave_locale_alone = True

    def publish_learning_object(self, obj):
        paths = obj.get_url_list()
        gen = StaticGenerator(*paths, fs=S3StaticFileSystem())
        gen.publish()

    def handle(self, *args, **options):
        paths = frozenset(['/', ])
        lobj_classes = [Topic, Module, Lesson, Question]

        for klass in lobj_classes:
            for lobj in klass.objects.all():
                paths |= frozenset(lobj.get_url_list())

        gen = StaticGenerator(*list(paths), fs=S3StaticFileSystem())
        gen.publish()
