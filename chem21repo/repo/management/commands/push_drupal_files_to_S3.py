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
            remote_id=0).filter(type__in=["application"],ext=".pdf")
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
                remote_id=0).filter(type__in=["application"],ext=".pdf"):
            s3storage = DefaultStorage()
            lstorage = UniqueFile.storage
            if s3storage.exists("sources/%s" % f.filename):
                # print "File already exists on S3"
                # f.s3d=True
                # f.save()
                continue
            try:
                lpath = f.local_paths[0]
            except IndexError:
                qns = list(f.questions.all())
                qs = [str(q) for q in qns]
                if f and qs:
                    print [(l.title, [m.title for m in l.modules.all()]) for l in q.lessons.all()]
                    print "No local path for %s in %s" % (f.checksum, ",".join(qs))
                    print 
                else:
                    print "Orphan file: %s" % f
                continue

            try:
                with lstorage.open(lpath, 'rb') as lofl:
                    data = lofl.read()
            except IOError:
                qs = [str(q) for q in f.questions.all()]
                if qs:
                    print "Error reading local file for %s in %s" % (f.checksum, qs)

                    print "-- Trying to download ..."
                    f.drupal.pull()
                    f.save()
                    try:
                        with lstorage.open(lpath, 'rb') as lofl:
                            data = lofl.read()
                    except IOError:
                        print "-- Still no good ... abort."
                        continue
                else:
                    print "Error reading orphan file (WTF) %s" % f.checksum
                    continue

            with s3storage.open("sources/%s" % f.filename, 'wb') as s3fl:
                qs = [str(q) for q in f.questions.all()]
                print "Writing file %s in %s" % (f.checksum, qs)
                s3fl.write(data)
