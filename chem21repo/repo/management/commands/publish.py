from chem21repo.storage import S3StaticFileSystem
from staticgenerator import StaticGenerator
from django.contrib.contenttypes.models import ContentType
from chem21repo.repo.models import Question, Lesson, Module, Topic, PresentationAction
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse


class Command(BaseCommand):
    help = 'Publish the site'
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument('--no-front',
                    action="store_false",
                    dest="front",
                    default=True,
                    help="Don't publish the homepage")
        parser.add_argument('--type',
                    dest="type",
                    type=str)
        parser.add_argument('--id',
                    dest="id",
                    type=int)

    def publish_learning_object(self, obj):
        paths = obj.get_url_list()
        gen = StaticGenerator(*paths, fs=S3StaticFileSystem())
        gen.publish()

    def handle(self, *args, **options):
        if options['front']:
            paths = frozenset(['/', '/about/', '/legal/'])
        else:
            paths = frozenset(['/about/', '/legal/'])
        if options['id']:
            ct = ContentType.objects.get(app_label="repo", model=options['type'])
            obj = ct.get_object_for_this_type(pk=options['id'])
            paths |= frozenset(obj.get_url_list())
        else:
            lobj_classes = [Topic, Module, Lesson, Question]
            for klass in lobj_classes:
                for lobj in klass.objects.all():
                    paths |= frozenset(lobj.get_url_list())

        paths |= frozenset([reverse(
            "video_timeline", kwargs={"pk": timeline.presentation.pk, }) \
                for timeline in PresentationAction.objects.all()])



        gen = StaticGenerator(*list(paths), fs=S3StaticFileSystem())
        gen.publish()
