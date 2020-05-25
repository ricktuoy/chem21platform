from django.db.models import Prefetch

from .models import Topic, Module, Lesson, Question


class TopicLoader(object):
    @staticmethod
    def get_pages_for_topic(topic_slug):
        return TopicLoader._prefetch_pages(Topic.objects.filter(
            slug=topic_slug)).first()

    @staticmethod
    def get_pages_for_all_topics():
        return TopicLoader._prefetch_pages(Topic.objects.all().exclude(archived=True))

    @staticmethod
    def _prefetch_pages(topic_queryset):
        return topic_queryset.prefetch_related(
            Prefetch("modules",
                     queryset=Module.objects.all().exclude(archived=True).order_by('order')),
            Prefetch("modules__lessons",
                     queryset=Lesson.objects.all().exclude(archived=True).order_by('order'),
                     to_attr="ordered_lessons"),
            Prefetch("modules__ordered_lessons__questions",
                     queryset=Question.objects.all().exclude(archived=True).order_by(
                         'order'),
                     to_attr="ordered_questions"))


class PageLoader(object):
    pks = {}
    get_all = True

    def __init__(self, get_all=True, topics=None, modules=None, lessons=None, questions=None):
        self.pks['question'] = questions if questions else []
        self.pks['lesson'] = lessons if lessons else []
        self.pks['module'] = modules if modules else []
        self.pks['topic'] = topics if topics else []
        self.get_all = get_all

    def is_match(self, model_name, obj):
        return self.get_all or str(obj.pk) in self.pks[model_name]

    def get_list(self):
        # flatten tree structure
        tree = TopicLoader.get_pages_for_all_topics()
        print tree
        out = []
        for topic in tree:
            if self.is_match('topic', topic):
                out.append(topic)
            for module in topic.modules.all():
                if self.is_match('module', module):
                    out.append(module)
                for lesson in module.ordered_lessons:
                    if self.is_match('lesson', lesson):
                        out.append(lesson)
                    for question in lesson.ordered_questions:
                        if self.is_match('question', question):
                            out.append(question)
        return out


class PDFLoader(PageLoader):

    def get_list(self):
        tree = TopicLoader.get_pages_for_all_topics()
        out = []
        for topic in tree:
            for module in topic.modules.all():
                if self.is_match('module', module):
                    out.append(module)
        return out


SCORMLoader = PDFLoader
