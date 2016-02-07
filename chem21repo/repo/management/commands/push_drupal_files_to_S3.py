from chem21repo.api_clients import C21RESTRequests, RESTError
from chem21repo.drupal import drupal_node_factory
from chem21repo.repo.models import UniqueFile, Question

from django.core.management.base import BaseCommand
from django.core.files.storage import DefaultStorage
from django.core.files.storage import get_storage_class
import os


class Command(BaseCommand):
    help = 'Download all drupal files'

    def handle(self, *args, **options):
        files = UniqueFile.objects.exclude(remote_id__isnull=True).exclude(
            remote_id=0).filter(type__in=["video", "image"])
        # print [(f.filename, f.questions.all()) for f in files]
        """
        for q in Question.objects.all():
            if q.video and not q.video.remote_id:
                print "Storing remote ID for %s" % q.title
                text = q.text
                try:
                    q.drupal.pull()
                except RESTError, e:
                    print "Unable to pull file"
                    print q.drupal.api.response
                q.text = text
                q.save()
        """

        # for f in UniqueFile.objects.exclude(remote_id__isnull=True).exclude(
        #        remote_id=0).filter(type__in=["video", "image"]):
        #   f.s3d=False
        #   f.save()
        for f in UniqueFile.objects.exclude(remote_id__isnull=True).exclude(
                remote_id=0).filter(type__in=["video", "image"]):
            s3storage = DefaultStorage()
            lstorage = UniqueFile.storage
            if s3storage.exists("sources/%s" % f.filename):
                print "File already exists on S3"
                # f.s3d=True
                # f.save()
                continue
            try:
                lpath = f.local_paths[0]
            except IndexError:
                print "No local file for %s"
                continue

            try:
                with lstorage.open(lpath, 'rb') as lofl:
                    data = lofl.read()
            except IOError:
                print "No local file for %s"

            with s3storage.open("sources/%s" % f.filename, 'wb') as s3fl:
                s3fl.write(data)
