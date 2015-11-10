# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0024_question_title'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='lessonsinmodule',
            unique_together=set([('lesson', 'module')]),
        ),
        migrations.AlterUniqueTogether(
            name='presentationsinquestion',
            unique_together=set([('question', 'presentation')]),
        ),
        migrations.AlterUniqueTogether(
            name='questionsinlesson',
            unique_together=set([('question', 'lesson')]),
        ),
        migrations.AlterUniqueTogether(
            name='slidesinpresentationversion',
            unique_together=set([('presentation', 'slide')]),
        ),
        migrations.AlterUniqueTogether(
            name='sourcefilesinpresentation',
            unique_together=set([('presentation', 'file')]),
        ),
        migrations.AlterUniqueTogether(
            name='videosinquestion',
            unique_together=set([('file', 'question')]),
        ),
        migrations.AlterIndexTogether(
            name='lessonsinmodule',
            index_together=set([('lesson', 'module')]),
        ),
        migrations.AlterIndexTogether(
            name='presentationsinquestion',
            index_together=set([('question', 'presentation')]),
        ),
        migrations.AlterIndexTogether(
            name='questionsinlesson',
            index_together=set([('question', 'lesson')]),
        ),
        migrations.AlterIndexTogether(
            name='slidesinpresentationversion',
            index_together=set([('presentation', 'slide')]),
        ),
        migrations.AlterIndexTogether(
            name='sourcefilesinpresentation',
            index_together=set([('presentation', 'file')]),
        ),
        migrations.AlterIndexTogether(
            name='videosinquestion',
            index_together=set([('file', 'question')]),
        ),
    ]
