from django.core.files.storage import default_storage
import json
import logging


class ToolNotFoundError(Exception):
    pass


class ToolBase(dict):
    quizzes = {}
    storage = default_storage

    @classmethod
    def load(cls, name):
        if name not in Quiz.quizzes:
            cls.quizzes[name] = cls(name)
        return Quiz.quizzes[name]

    def __init__(self, name):
        self.name = name
        try:
            with self.storage.open(self.question_file_path, "r") as f:
                super(ToolBase, self).__init__(**json.load(f))
        except IOError:
            raise ToolNotFoundError(
                "Question file not found. %s" % self.question_file_path)

        self.questions = self['data']
        self._answers_raw = None
        self.answers = None

    def load_answers(self):
        if 'answers' not in self:
            try:
                with self.storage.open(self.answer_file_path, "r") as f:
                    self['answers'] = json.load(f)['data']
            except IOError:
                raise IOError(
                    "Answer file not found. %s" % self.answer_file_path)
        return self['answers']

    def iter_questions(self):
        for i in range(1, len(self.questions) + 1):
            yield i, self.get_question(i)

    def iter_answers(self):
        self.load_answers()
        for i, answer in zip(
                range(1, len(self['answers']) + 1),
                self['answers']):
            q = self.get_question(i)
            if q.has_choices:
                answer['correct_texts'] = [
                    q.get_choice_text_by_id(cid)
                    for cid in answer['correct']]
            answer['question'] = q
            answer['type'] = q['type']
            yield i, answer

    @property
    def answer_file_url(self):
        if self.answer_file_path is not None:
            return self.storage.url(self.answer_file_path)
        return ""

    def get_question(self, num):
        if num < 1:
            raise QuestionNotFoundError(
                "No such question: %s, question %d" % (self.name, num))
        try:
            raw_q = self.questions[num - 1]
        except IndexError:
            raise QuestionNotFoundError(
                "No such question: %s, question %d" % (self.name, num))
        return Question(raw_q['id'], self, num, **raw_q)

    def get_answer(self, num):
        try:
            raw_a = self.answers[num - 1]
        except IndexError:
            raise AnswerNotFoundError(
                "No such answer: %s, question %d" % (self.name, num))
        return Answer(raw_a['id'], self, num, **raw_a)

    def __len__(self):
        return len(self.questions)


class Quiz(ToolBase):
    PATH_ROOT = 'quiz'

    @property
    def question_file_path(self):
        return "%s/%s_questions.json" % (self.PATH_ROOT, self.name)

    @property
    def answer_file_path(self):
        return "%s/%s_answers.json" % (self.PATH_ROOT, self.name)


class Guide(Quiz):
    PATH_ROOT = "guides"

    @property
    def question_file_path(self):
        return "%s/%s.json" % (
            self.PATH_ROOT, self.name)

    @property
    def answer_file_path(self):
        return None


class QuestionNotFoundError(Exception):
    pass


class AnswerNotFoundError(QuestionNotFoundError):
    pass


class Question(dict):

    def __init__(self, pk, quiz, num, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.pk = pk
        self.num = num
        self.quiz = quiz
        self._next = None
        self._prev = None
        self._choices_by_id = None

    def is_final(self):
        if(self.num == len(self.quiz)):
            return True
        return False

    def get_choice_text_by_id(self, cid):
        if not self.has_choices:
            return None
        if self._choices_by_id is None:
            self._choices_by_id = dict([
                (r['id'], r['text'])
                for r in self['responses']
            ])
        return self._choices_by_id[cid]

    @property
    def has_choices(self):
        if self['type'] == "numeric":
            return False
        return True

    @property
    def next_question(self):
        if self._next is None:
            try:
                self._next = self.quiz.get_question(self.num + 1)
            except QuestionNotFoundError:
                self._next = False

        return self._next

    @property
    def previous_question(self):
        if self._prev is None:
            try:
                self._prev = self.quiz.get_question(self.num - 1)
            except QuestionNotFoundError:
                self._prev = None
        return self._prev


class Answer(Question):
    pass
