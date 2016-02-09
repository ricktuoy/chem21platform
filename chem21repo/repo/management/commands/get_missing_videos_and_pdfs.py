from chem21repo.api_clients import C21RESTRequests, RESTError
from chem21repo.drupal import DrupalQuestion
from chem21repo.repo.models import Lesson
from chem21repo.repo.models import Module, UniqueFile
from chem21repo.repo.models import Question

from django.core.management.base import BaseCommand
from django.db import IntegrityError

import json


class Command(BaseCommand):
    help = 'Import objects from the platform'

    def save_question(self, question, dry=False):

        try:
            q_obj = Question.objects.get(remote_id=question['nid'])
            if q_obj.has_text_changes():
                self.print_obj(
                    "Question %s has text changes: ignoring", question)
                return

            q_obj.text = question['intro']
            if not dry:
                q_obj.save()
        except Question.DoesNotExist:
            if not dry:
                q_obj = Question.objects.create(
                    remote_id=question['nid'],
                    order=question['number'],
                    title=question['title'], text=question['intro'])
        if dry:
            self.print_obj("Dry run: question %s", question)
            return
        try:
            q_obj.lessons.add(lesson)
        except IntegrityError:
            pass
        return q_obj

    def print_obj(self, text, obj):
        try:
            print text % obj['title']
        except UnicodeError:
            print text % obj['nid']

    def handle(self, *args, **options):
        c21_requests = C21RESTRequests()
        c21_requests.authenticate()
        courses_data = c21_requests.index_courses()
        dry = False
        for module in courses_data:
            print "Module ****** %s" % module['title']
            tree_data = c21_requests.get("course", int(module['nid']))
            tree_data['nid'] = module['nid']
            for lesson in tree_data['lessons']:
                print "Lesson ********%s " % lesson['title']
                for question in lesson['questions']:
                    # print question['type']
                    try:
                        if question['type'] != "h5p_content":
                            continue
                    except KeyError:
                        continue

                    qnode = c21_requests.get("question", int(question['nid']))
                    try:
                        resources = qnode['h5p_resources']
                    except:
                        continue
                    if not resources:
                        continue
                    for fid, res in resources.iteritems():
                        print question['title']
                        try:
                            q = Question.objects.get(
                                remote_id=question['nid'])
                        except Question.DoesNotExist:
                            print "URRGGHH no question."
                            continue
                        try:
                            uf = UniqueFile.objects.get(remote_id=fid)
                            fpks = set([f.pk for f in q.files.all()])
                            print fpks
                            if uf.pk in fpks:
                                continue
                            else:
                                print "Yorks."
                            q.files.clear()
                            q.files.add(uf)
                            uf.drupal.pull()
                            uf.save()
                        except UniqueFile.DoesNotExist:
                            print question['title']
                            instance = UniqueFile(remote_id=fid)
                            try:
                                instance.drupal.pull()
                                instance.save()
                            except IntegrityError:
                                print "Checksum exists - changing remote id for checksum %s" % instance.checksum
                                old_instance = UniqueFile.objects.get(
                                    checksum=instance.checksum)
                                old_instance.remote_id = instance.remote_id
                                old_instance.save()
                                continue
                            except RESTError, e:
                                print "Cannot download file - error"
                                continue
                            q.files.clear()
                            q.files.add(instance)
                            print instance.local_paths
                            # DL the file, fingers crossed
                            try:
                                instance.drupal.pull()
                                instance.save()
                            except RESTError, e:
                                print "Cannot download file - error %s" % str(e)
                                

                    #print (question['title'], question['type'])
                    # self.save_question(
                    #    qnode, dry=dry)
                    """
                    node = DrupalQuestion(qnode)
                    print json.dumps(node, sort_keys=True,
                                     indent=4,
                                     separators=(',', ': '))
                    """
        # print json.dumps(DrupalQuestion(**c21_requests.get("question", 62)))
