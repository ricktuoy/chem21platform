# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0022_questionsinlesson'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='lessons',
            field=models.ManyToManyField(to='repo.Lesson', through='repo.QuestionsInLesson'),
        ),
    ]
