from chem21repo.repo.models import Module, Lesson, Question, Topic


class Initialiser(object):

    @staticmethod
    def create_base_topic():
        topic = Topic(name="Topic")
        topic.save()
        return topic

    @staticmethod
    def create_base_module(topic):
        module = Module(topic=topic, name='Base module', code='BASE')
        module.save()
        return module

    @staticmethod
    def create_base_lesson(topic):
        module = Initialiser.create_base_module(topic)
        lesson = Lesson(title='Base lesson')
        lesson.save()
        lesson.modules.add(module)
        return lesson

    @staticmethod
    def add_lessons_to_module(module, rng):
        lessons = []
        pks = []

        for i in rng:
            les = Lesson(title='Lesson %s' % str(i))
            les.save()
            les.modules.add(module)
            les.save()
            pks.append(les.pk)

        for i in rng:
            lessons.append(Lesson.objects.get(pk=pks[i]))

        return lessons

    @staticmethod
    def add_questions_to_lesson(lesson, rng):
        questions = []
        pks = []

        for i in rng:
            q = Question(title='Question %s' % str(i))
            q.save()
            q.lessons.add(lesson)
            q.save()
            pks.append(q.pk)

        for i in rng:
            questions.append(Question.objects.get(pk=pks[i]))

        return questions

    @staticmethod
    def create_question_with_ancestors():
        topic = Initialiser.create_base_topic()
        lesson = Initialiser.create_base_lesson(topic)
        questions = Initialiser.add_questions_to_lesson(lesson, range(0, 1))
        return questions[0]
