from django.db import models


class SCORMUserEvent(models.Model):
    username = models.CharField(max_length=10)
    event = models.CharField(max_length=20)
    datetime = models.DateTimeField()
    course_id = models.CharField(max_length=75)

    class Meta:
        unique_together = ('username', 'event', 'course_id')
        index_together = ('username', 'course_id')
