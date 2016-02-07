from chem21repo.api_clients import C21RESTRequests, RESTError
from chem21repo.drupal import drupal_node_factory
from chem21repo.repo.models import UniqueFile, Question

from django.core.management.base import BaseCommand

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

        for f in UniqueFile.objects.exclude(remote_id__isnull=True).exclude(
                remote_id=0).filter(type__in=["video", "image"]):
            download = False
            for path in f.local_paths:
                if UniqueFile.storage.exists(path):
                    print "Exists: %s" % path
                else:
                    download = True
            if not download:
                "File already downloaded"
                continue
            print f.filename
            print f.questions.all()
            try:
            	f.drupal.pull()
            except RESTError, e:
            	print "Unable to pull file"
